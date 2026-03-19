from http import HTTPStatus
from typing import override

import requests
from fastapi import HTTPException

from app.handlers.base import TemplateProviderBase


class ChatwootTemplateProvider(TemplateProviderBase):
    @override
    def get_templates(self, config: dict) -> list[dict]:
        base = f'{config["url"].rstrip("/")}/api/v1/accounts/{config["account_id"]}'
        headers = {'api_access_token': config['api_token']}
        try:
            resp = requests.get(f'{base}/inboxes', headers=headers, timeout=10)
        except requests.RequestException as exc:
            raise HTTPException(status_code=HTTPStatus.BAD_GATEWAY, detail=f'Chatwoot unreachable: {exc}') from exc
        if not resp.ok:
            raise HTTPException(status_code=HTTPStatus.BAD_GATEWAY, detail=f'Chatwoot inboxes error: {resp.status_code}')
        templates: list[dict] = []
        for inbox in resp.json().get('payload', []):
            templates.extend(inbox.get('message_templates', []))
        return templates
