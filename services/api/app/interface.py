import csv
import io
import json
import logging
from http import HTTPStatus
from typing import Annotated, Optional

import requests
from fastapi import Depends, HTTPException
from pocketbase.errors import ClientResponseError

from app.schemas import (
    CampaignSchema,
    ClientInfoSchema,
    ClientSchema,
    CreateCampaignSchema,
    CreateListSchema,
    DeleteListSchema,
    DeleteResponseSchema,
    ImportSubscriberItem,
    ListSchema,
    LM_CreateListSchema,
    ResponseCampaignSchema,
    ResponseUpdateListSchema,
    UpdateCampaignSchema,
    UpdateListSchema,
)
from app.sessions import Monk, PocketBaseSession, get_pocketbase_session
from app.settings import Settings

logger = logging.getLogger(__name__)

settings = Settings()
url_monk = f'{settings.LISTMONK_API_URL}/lists'
url_monk_campaigns = f'{settings.LISTMONK_API_URL}/campaigns'
url_monk_subscribers = f'{settings.LISTMONK_API_URL}/import/subscribers'
url_monk_subscribers_single = f'{settings.LISTMONK_API_URL}/subscribers'
auth_monk = (settings.LISTMONK_USER, settings.LISTMONK_TOKEN)

MonkLists = Monk(auth_creds=auth_monk, url=url_monk)
MonkCampaigns = Monk(auth_creds=auth_monk, url=url_monk_campaigns)
MonkSubscribers = Monk(auth_creds=auth_monk, url=url_monk_subscribers)
MonkSubscribersSingle = Monk(auth_creds=auth_monk, url=url_monk_subscribers_single)
Pocket = Annotated[PocketBaseSession, Depends(get_pocketbase_session)]


class Interface:
    def __init__(self, monk, monk_campaigns, monk_subscribers, monk_subscribers_single, pb):
        self.__monk = monk
        self.__monk_campaigns = monk_campaigns
        self.__monk_subscribers = monk_subscribers
        self.__monk_subscribers_single = monk_subscribers_single
        self.__pb = pb

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_client_list_ids(self, client_id: str) -> list[str]:
        result = self.__pb.client.collection('monk_client_lists').get_list(1, 1, {'filter': f'client="{client_id}"'})
        if result.total_items == 0:
            return []
        return [str(lid) for lid in result.items[0].lists]

    def _get_campaign_raw(self, campaign_id: int) -> dict:
        response = self.__monk_campaigns.get({}, path=f'/{campaign_id}')
        response.raise_for_status()
        return response.json()['data']

    def _verify_campaign_ownership(self, campaign: dict, client_id: str) -> list[str]:
        client_list_ids = self._get_client_list_ids(client_id)
        campaign_list_ids = [str(lst['id']) for lst in campaign.get('lists', [])]
        if not any(lid in client_list_ids for lid in campaign_list_ids):
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail='Campaign does not belong to client')
        return client_list_ids

    # -------------------------------------------------------------------------
    # Lists
    # -------------------------------------------------------------------------

    def create_list(self, payload: CreateListSchema) -> ListSchema:
        client = payload.client.id
        list_result = self.__pb.client.collection('monk_client_lists').get_list(1, 1, {'filter': f'client="{client}"'})
        items, total = list_result.items, list_result.total_items
        if total == 0:
            client_record = self.__pb.client.collection('monk_client_lists').create({'client': client, 'lists': []})
            client_id = client_record.id
            existing_lists = []
        else:
            client_id = items[0].id
            existing_lists = items[0].lists

        try:
            response = self.__monk.post(payload.list.model_dump())
        except requests.RequestException as e:
            logger.error('create_list.unreachable', extra={'client': client, 'error': str(e)})
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=f'Could not reach Listmonk API: {e}',
            )
        result = response.json()
        list_id = result['data']['id']

        self.__pb.client.collection('monk_lists').create({'id': list_id})
        updates = {'lists': existing_lists + [list_id]}
        if not existing_lists:
            updates['default_list'] = list_id
        self.__pb.client.collection('monk_client_lists').update(client_id, updates)

        logger.info('create_list.ok', extra={'client': client, 'list_id': list_id, 'list_name': result['data']['name']})
        return ListSchema(**result['data'])

    def get_lists(self, client: ClientSchema) -> list[ListSchema]:
        result = self.__pb.client.collection('monk_client_lists').get_list(1, 1, {'filter': f'client="{client.id}"'})
        if result.total_items == 0:
            logger.info('get_lists.ok', extra={'client': client.id, 'count': 0})
            return []
        client_list_ids = [str(lid) for lid in result.items[0].lists]

        response = self.__monk.get({'page': 1, 'per_page': 500})
        response.raise_for_status()
        all_lists = response.json()['data']['results'] or []

        filtered = [ListSchema(**lst) for lst in all_lists if str(lst['id']) in client_list_ids]
        logger.info('get_lists.ok', extra={'client': client.id, 'count': len(filtered)})
        return filtered

    def get_client(self, client: ClientSchema) -> ClientInfoSchema:
        result = self.__pb.client.collection('monk_client_lists').get_list(1, 1, {'filter': f'client="{client.id}"'})
        if result.total_items == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Client "{client.id}" not found')
        record = result.items[0]
        logger.info('get_client.ok', extra={'client': client.id})
        return ClientInfoSchema(
            id=client.id,
            default_list=int(record.default_list) if record.default_list else None,
            lists=[int(lid) for lid in record.lists],
        )

    def delete_list(self, params: DeleteListSchema) -> DeleteResponseSchema:
        for _id in params.id:
            try:
                result = self.__pb.client.collection('monk_client_lists').get_list(1, 1, {'filter': f'lists ~ "{_id}"'})
                if result.total_items > 0:
                    owner = result.items[0]
                    updated_lists = [lid for lid in owner.lists if str(lid) != str(_id)]
                    self.__pb.client.collection('monk_client_lists').update(owner.id, {'lists': updated_lists})
                self.__pb.client.collection('monk_lists').delete(str(_id))
            except ClientResponseError:
                pass

        self.__monk.delete(params=params.model_dump(exclude_none=True, exclude={'client'}))

        logger.info('delete_list.ok', extra={'client': params.client.id, 'ids': params.id})
        return DeleteResponseSchema(data=True)

    def update_list(self, list_id, payload: UpdateListSchema) -> ResponseUpdateListSchema:
        response = self.__monk.put(
            payload.list.model_dump(),
            path=f'/{list_id}',
        )

        # monk_lists only stores the id; no extra fields to sync
        logger.info('update_list.ok', extra={'client': payload.client.id, 'list_id': list_id})
        return ResponseUpdateListSchema(**response.json())

    # -------------------------------------------------------------------------
    # Campaigns
    # -------------------------------------------------------------------------

    def create_campaign(self, payload: CreateCampaignSchema) -> CampaignSchema:
        client_list_ids = self._get_client_list_ids(payload.client.id)
        for list_id in payload.campaign.lists:
            if str(list_id) not in client_list_ids:
                logger.error(
                    'create_campaign.forbidden',
                    extra={'client': payload.client.id, 'list_id': list_id},
                )
                raise HTTPException(
                    status_code=HTTPStatus.FORBIDDEN,
                    detail=f'List {list_id} does not belong to client "{payload.client.id}"',
                )

        try:
            response = self.__monk_campaigns.post(payload.campaign.model_dump(mode='json'))
        except requests.RequestException as e:
            logger.error('create_campaign.unreachable', extra={'client': payload.client.id, 'error': str(e)})
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=f'Could not reach Listmonk API: {e}',
            )
        response.raise_for_status()
        data = response.json()['data']
        logger.info(
            'create_campaign.ok',
            extra={'client': payload.client.id, 'campaign_id': data['id'], 'campaign_name': data['name']},
        )
        return CampaignSchema(**data)

    def get_campaigns(self, client: ClientSchema) -> list[CampaignSchema]:
        client_list_ids = self._get_client_list_ids(client.id)

        response = self.__monk_campaigns.get({'page': 1, 'per_page': 500})
        response.raise_for_status()
        all_campaigns = response.json()['data']['results'] or []

        filtered = [
            CampaignSchema(**c) for c in all_campaigns if any(str(lst['id']) in client_list_ids for lst in c.get('lists', []))
        ]
        logger.info('get_campaigns.ok', extra={'client': client.id, 'count': len(filtered)})
        return filtered

    def update_campaign(self, campaign_id: int, payload: UpdateCampaignSchema) -> ResponseCampaignSchema:
        campaign = self._get_campaign_raw(campaign_id)
        client_list_ids = self._verify_campaign_ownership(campaign, payload.client.id)

        if payload.campaign.lists is not None:
            for lst in payload.campaign.lists:
                list_id = str(lst['id'] if isinstance(lst, dict) else lst)
                if list_id not in client_list_ids:
                    raise HTTPException(
                        status_code=HTTPStatus.FORBIDDEN,
                        detail=f'List {list_id} does not belong to client "{payload.client.id}"',
                    )

        # Listmonk PUT requires a full body; merge current state with the requested changes.
        # The GET response returns `lists` as [{id, name, ...}] objects; PUT expects [id] integers.
        merged = {**campaign, **payload.campaign.model_dump(mode='json', exclude_none=True)}
        merged['lists'] = [lst['id'] if isinstance(lst, dict) else lst for lst in merged['lists']]

        response = self.__monk_campaigns.put(merged, path=f'/{campaign_id}')
        response.raise_for_status()
        logger.info('update_campaign.ok', extra={'client': payload.client.id, 'campaign_id': campaign_id})
        return ResponseCampaignSchema(data=CampaignSchema(**response.json()['data']))

    def delete_campaign(self, campaign_id: int, client: ClientSchema) -> DeleteResponseSchema:
        campaign = self._get_campaign_raw(campaign_id)
        self._verify_campaign_ownership(campaign, client.id)

        response = self.__monk_campaigns.delete({}, path=f'/{campaign_id}')
        response.raise_for_status()
        logger.info('delete_campaign.ok', extra={'client': client.id, 'campaign_id': campaign_id})
        return DeleteResponseSchema(data=True)

    def set_campaign_status(self, campaign_id: int, status: str, client: ClientSchema) -> CampaignSchema:
        campaign = self._get_campaign_raw(campaign_id)
        self._verify_campaign_ownership(campaign, client.id)

        response = self.__monk_campaigns.put({'status': status}, path=f'/{campaign_id}/status')
        response.raise_for_status()
        data = response.json()['data']
        logger.info('set_campaign_status.ok', extra={'client': client.id, 'campaign_id': campaign_id, 'status': data['status']})
        return CampaignSchema(**data)

    # -------------------------------------------------------------------------
    # Subscribers
    # -------------------------------------------------------------------------

    def _get_or_create_default_list(self, client: ClientSchema) -> int:
        """Auto-creates the client and a default list if they do not exist yet."""
        logger.info('import_subscribers.auto_create_client', extra={'client': client.id})
        list_obj = self.create_list(
            CreateListSchema(
                client=client,
                list=LM_CreateListSchema(name=f'{client.id} Default', type='private', optin='single'),
            )
        )
        return list_obj.id

    def _resolve_target_list(self, client: ClientSchema, list_id: Optional[int]) -> int:
        """Returns the target list ID for an import. Auto-creates the client with a default list if needed."""
        result = self.__pb.client.collection('monk_client_lists').get_list(1, 1, {'filter': f'client="{client.id}"'})

        if result.total_items == 0:
            return self._get_or_create_default_list(client)

        record = result.items[0]
        default_list = record.default_list
        if not default_list:
            return self._get_or_create_default_list(client)

        client_list_ids = [str(lid) for lid in record.lists]
        if list_id is not None:
            if str(list_id) not in client_list_ids:
                logger.error('import_subscribers.list_not_found', extra={'client': client.id, 'list_id': list_id})
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f'List {list_id} not found or does not belong to client "{client.id}"',
                )
            return list_id

        return int(default_list)

    def _post_csv_to_listmonk(self, client: ClientSchema, file_bytes: bytes, filename: str, target_list: int) -> dict:
        """Sends a CSV file to Listmonk's bulk import endpoint."""
        params = json.dumps({
            'mode': 'subscribe',
            'subscription_status': 'confirmed',
            'lists': [target_list],
            'delim': ',',
        })
        try:
            response = self.__monk_subscribers.post_multipart(
                files={'file': (filename, file_bytes, 'text/csv')},
                data={'params': params},
            )
        except requests.RequestException as e:
            logger.error('import_subscribers.unreachable', extra={'client': client.id, 'error': str(e)})
            raise HTTPException(status_code=HTTPStatus.SERVICE_UNAVAILABLE, detail=f'Could not reach Listmonk API: {e}')
        response.raise_for_status()
        return response.json()

    def import_subscribers(self, client: ClientSchema, file_bytes: bytes, filename: str, list_id: Optional[int] = None) -> dict:
        target_list = self._resolve_target_list(client, list_id)
        result = self._post_csv_to_listmonk(client, file_bytes, filename, target_list)
        logger.info('import_subscribers.ok', extra={'client': client.id, 'target_list': target_list, 'file': filename})
        return result

    def import_subscribers_json(
        self, client: ClientSchema, items: list[ImportSubscriberItem], list_id: Optional[int] = None
    ) -> dict:
        target_list = self._resolve_target_list(client, list_id)

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=['email', 'name'])
        writer.writeheader()
        for item in items:
            writer.writerow({'email': item.email, 'name': item.name})
        file_bytes = buf.getvalue().encode()

        result = self._post_csv_to_listmonk(client, file_bytes, 'import.csv', target_list)
        logger.info('import_subscribers_json.ok', extra={'client': client.id, 'target_list': target_list, 'count': len(items)})
        return result

    def delete_subscriber_by_email(self, email: str) -> None:
        response = self.__monk_subscribers_single.get({'query': f"subscribers.email='{email}'"})
        if not response.ok:
            logger.warning('delete_subscriber_by_email.query_failed', extra={'email': email})
            return
        results = response.json().get('data', {}).get('results') or []
        if not results:
            logger.warning('delete_subscriber_by_email.not_found', extra={'email': email})
            return
        subscriber_id = results[0]['id']
        del_response = self.__monk_subscribers_single.delete({}, path=f'/{subscriber_id}')
        if del_response.ok:
            logger.info('delete_subscriber_by_email.ok', extra={'email': email, 'subscriber_id': subscriber_id})
        else:
            logger.warning('delete_subscriber_by_email.delete_failed', extra={'email': email, 'subscriber_id': subscriber_id})


interface = Interface(MonkLists, MonkCampaigns, MonkSubscribers, MonkSubscribersSingle, get_pocketbase_session())


def get_interface_api():
    return interface
