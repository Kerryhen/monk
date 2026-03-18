import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from threading import Thread
from typing import override

import requests
from pocketbase.errors import ClientResponseError

from app.context import enrich_wide_event
from app.handlers.base import MessengerHandlerBase, VariableResolverBase
from app.handlers.chatwoot.schemas import ChatwootTemplateConfig
from app.schemas import MessengerPayload, MessengerRecipient
from app.sessions import get_pocketbase_session

logger = logging.getLogger(__name__)


@dataclass
class CampaignCtx:
    """Holds campaign-level data shared across all recipients in one send() call."""

    config: dict
    template: ChatwootTemplateConfig
    payload: MessengerPayload
    instancia: dict


class ChatwootHandler(MessengerHandlerBase):
    def __init__(self, resolver: VariableResolverBase) -> None:
        self._resolver = resolver

    @override
    def send(self, payload: MessengerPayload) -> None:
        """Return immediately; process recipients in a background thread (PROB-06)."""
        Thread(target=self._process_all, args=(payload,), daemon=True).start()

    # ------------------------------------------------------------------ #
    # PocketBase helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_instance_id(tags: list[str] | None) -> str | None:
        for tag in tags or []:
            if tag.startswith('instance:'):
                return tag.split(':', 1)[1]
        return None

    @staticmethod
    def _fetch_channel_config(pb, instance_id: str) -> dict | None:
        try:
            record = pb.client.collection('monk_channel_configs').get_first_list_item(
                f'instance_id="{instance_id}" && handler="chatwoot" && channel="whatsapp"'
            )
            return record.config
        except ClientResponseError:
            return None

    @staticmethod
    def _fetch_instancia(pb, instance_id: str) -> dict:
        try:
            record = pb.client.collection('instancias').get_first_list_item(f'instance_id="{instance_id}"')
            return {k: v for k, v in record.__dict__.items() if not k.startswith('_')}
        except Exception:
            return {}

    # ------------------------------------------------------------------ #
    # Chatwoot API calls
    # ------------------------------------------------------------------ #

    @staticmethod
    def _headers(api_token: str) -> dict:
        return {'api_access_token': api_token, 'Content-Type': 'application/json'}

    def _find_or_create_contact(self, session: requests.Session, config: dict, phone: str, name: str) -> int | None:
        base = f'{config["url"].rstrip("/")}/api/v1/accounts/{config["account_id"]}'
        headers = self._headers(config['api_token'])

        resp = session.get(
            f'{base}/contacts/search',
            params={'q': phone, 'include_contacts': 'true'},
            headers=headers,
            timeout=10,
        )
        if resp.ok:
            results = resp.json().get('payload', [])
            if results:
                return results[0]['id']

        resp = session.post(
            f'{base}/contacts',
            json={'name': name, 'phone_number': phone},
            headers=headers,
            timeout=10,
        )
        return resp.json().get('id') if resp.ok else None

    def _create_conversation(self, session: requests.Session, config: dict, contact_id: int) -> int | None:
        base = f'{config["url"].rstrip("/")}/api/v1/accounts/{config["account_id"]}'
        resp = session.post(
            f'{base}/conversations',
            json={'inbox_id': config['inbox_id'], 'contact_id': contact_id},
            headers=self._headers(config['api_token']),
            timeout=10,
        )
        return resp.json().get('id') if resp.ok else None

    @staticmethod
    def _build_message_body(template: ChatwootTemplateConfig, resolved_body: dict, resolved_buttons: list) -> dict:
        processed_params: dict = dict(resolved_body)
        if resolved_buttons:
            processed_params['buttons'] = resolved_buttons
        return {
            'template_params': {
                'name': template.template_name,
                'category': template.category,
                'language': template.language,
                'processed_params': processed_params,
            }
        }

    def _send_template_message(self, session: requests.Session, config: dict, conversation_id: int, message_body: dict) -> bool:
        base = f'{config["url"].rstrip("/")}/api/v1/accounts/{config["account_id"]}'
        resp = session.post(
            f'{base}/conversations/{conversation_id}/messages',
            json=message_body,
            headers=self._headers(config['api_token']),
            timeout=10,
        )
        return resp.ok

    # ------------------------------------------------------------------ #
    # Per-recipient processing
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_context(recipient: MessengerRecipient, ctx: CampaignCtx) -> dict:
        return {
            'lead': {
                'uuid': recipient.uuid,
                'email': recipient.email,
                'name': recipient.name,
                'status': recipient.status,
                'attribs': recipient.attribs,
            },
            'campanha': {
                'uuid': ctx.payload.campaign.uuid,
                'name': ctx.payload.campaign.name,
                'subject': ctx.payload.subject,  # top-level payload field covers PROB-01
                'tags': ctx.payload.campaign.tags or [],
            },
            'instancia': ctx.instancia,
        }

    def _resolve_params(self, recipient: MessengerRecipient, ctx: CampaignCtx) -> tuple[dict, list] | None:
        """Resolve all template variable refs. Returns None if any required field is absent."""
        context = self._build_context(recipient, ctx)

        resolved_body: dict[str, str] = {}
        for slot, ref in ctx.template.params.body.items():
            ok, value = self._resolver.resolve(ref, context)
            if not ok:
                logger.warning('chatwoot.skip_recipient', extra={'reason': f'missing:{ref}', 'uuid': recipient.uuid})
                return None
            resolved_body[slot] = value

        resolved_buttons: list[dict] = []
        for btn in ctx.template.params.buttons:
            ok, value = self._resolver.resolve(btn.parameter, context)
            if not ok:
                logger.warning('chatwoot.skip_recipient', extra={'reason': f'missing:{btn.parameter}', 'uuid': recipient.uuid})
                return None
            resolved_buttons.append({'type': btn.type, 'parameter': value, 'url': btn.url, 'variables': btn.variables})

        return resolved_body, resolved_buttons

    def _process_one(self, recipient: MessengerRecipient, ctx: CampaignCtx, session: requests.Session) -> bool:
        resolved = self._resolve_params(recipient, ctx)
        if resolved is None:
            return False

        resolved_body, resolved_buttons = resolved
        phone = recipient.attribs.get(ctx.config['phone_attrib'])
        if not phone:
            logger.warning('chatwoot.skip_recipient', extra={'reason': 'missing:phone', 'uuid': recipient.uuid})
            return False

        contact_id = self._find_or_create_contact(session, ctx.config, str(phone), recipient.name)
        if contact_id is None:
            logger.error('chatwoot.contact_error', extra={'uuid': recipient.uuid})
            return False

        conversation_id = self._create_conversation(session, ctx.config, contact_id)
        if conversation_id is None:
            logger.error('chatwoot.conversation_error', extra={'uuid': recipient.uuid})
            return False

        message_body = self._build_message_body(ctx.template, resolved_body, resolved_buttons)
        if not self._send_template_message(session, ctx.config, conversation_id, message_body):
            logger.error('chatwoot.send_error', extra={'uuid': recipient.uuid})
            return False

        return True

    # ------------------------------------------------------------------ #
    # Batch processing (runs in daemon thread)
    # ------------------------------------------------------------------ #

    def _process_all(self, payload: MessengerPayload) -> None:
        # Parse template config from body (PROB-05)
        try:
            template = ChatwootTemplateConfig.model_validate_json(payload.body)
        except Exception as exc:
            logger.error('chatwoot.invalid_body', extra={'error': str(exc)})
            enrich_wide_event({
                'handler': 'chatwoot',
                'error': 'invalid_body',
                'recipients_total': len(payload.recipients),
                'recipients_sent': 0,
                'recipients_skipped': len(payload.recipients),
            })
            return

        # Extract instance_id from campaign tags (ALT-A from PROB-03)
        instance_id = self._extract_instance_id(payload.campaign.tags)
        if not instance_id:
            logger.error('chatwoot.missing_instance_id', extra={'campaign': payload.campaign.uuid})
            enrich_wide_event({
                'handler': 'chatwoot',
                'error': 'missing_instance_id',
                'recipients_total': len(payload.recipients),
                'recipients_sent': 0,
                'recipients_skipped': len(payload.recipients),
            })
            return

        pb = get_pocketbase_session()
        config = self._fetch_channel_config(pb, instance_id)
        if config is None:
            logger.error('chatwoot.missing_config', extra={'instance_id': instance_id})
            enrich_wide_event({
                'handler': 'chatwoot',
                'error': 'missing_config',
                'recipients_total': len(payload.recipients),
                'recipients_sent': 0,
                'recipients_skipped': len(payload.recipients),
            })
            return

        ctx = CampaignCtx(
            config=config,
            template=template,
            payload=payload,
            instancia=self._fetch_instancia(pb, instance_id),
        )
        session = requests.Session()

        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(lambda r: self._process_one(r, ctx, session), payload.recipients))

        sent_count = sum(1 for r in results if r)
        skipped_count = sum(1 for r in results if not r)

        enrich_wide_event({
            'handler': 'chatwoot',
            'campaign': payload.campaign.name,
            'recipients_total': len(payload.recipients),
            'recipients_sent': sent_count,
            'recipients_skipped': skipped_count,
        })
