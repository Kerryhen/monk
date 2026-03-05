from http import HTTPStatus
from typing import Annotated

import requests
from fastapi import Depends, HTTPException
from pocketbase.errors import ClientResponseError

from app.schemas import (
    CampaignSchema,
    ClientSchema,
    CreateCampaignSchema,
    CreateListSchema,
    DeleteListSchema,
    DeleteResponseSchema,
    ListSchema,
    ResponseCampaignSchema,
    ResponseUpdateListSchema,
    UpdateCampaignSchema,
    UpdateListSchema,
)
from app.sessions import Monk, PocketBaseSession, get_pocketbase_session
from app.settings import Settings

settings = Settings()
url_monk = f'{settings.LISTMONK_API_URL}/lists'
url_monk_campaigns = f'{settings.LISTMONK_API_URL}/campaigns'
auth_monk = (settings.LISTMONK_USER, settings.LISTMONK_TOKEN)

MonkLists = Monk(auth_creds=auth_monk, url=url_monk)
MonkCampaigns = Monk(auth_creds=auth_monk, url=url_monk_campaigns)
Pocket = Annotated[PocketBaseSession, Depends(get_pocketbase_session)]


class Interface:
    def __init__(self, monk, monk_campaigns, pb):
        self.__monk = monk
        self.__monk_campaigns = monk_campaigns
        self.__pb = pb

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_client_list_ids(self, client_id: str) -> list[str]:
        result = self.__pb.client.collection('monk_client_lists').get_list(1, 1, {'filter': f'client="{client_id}"'})
        if result.total_items == 0:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Client "{client_id}" not found')
        return [str(lid) for lid in result.items[0].lists]

    def _get_campaign_raw(self, campaign_id: int) -> dict:
        response = self.__monk_campaigns.get({}, path=f'/{campaign_id}')
        response.raise_for_status()
        return response.json()['data']

    def _verify_campaign_ownership(self, campaign: dict, client_id: str) -> None:
        client_list_ids = self._get_client_list_ids(client_id)
        campaign_list_ids = [str(lst['id']) for lst in campaign.get('lists', [])]
        if not any(lid in client_list_ids for lid in campaign_list_ids):
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail='Campaign does not belong to client')

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
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=f'Could not reach Listmonk API: {e}',
            )
        result = response.json()
        list_id = result['data']['id']

        self.__pb.client.collection('monk_lists').create({'id': list_id})
        self.__pb.client.collection('monk_client_lists').update(client_id, {'lists': existing_lists + [list_id]})

        return ListSchema(**result['data'])

    def user_list(self, user_id):
        self.__pb.client.collection('monk_lists').get_list(1, 30, {'filter': f'id="{user_id}"'})

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

        return DeleteResponseSchema(data=True)

    def update_list(self, list_id, payload: UpdateListSchema) -> ResponseUpdateListSchema:
        response = self.__monk.put(
            payload.list.model_dump(),
            path=f'/{list_id}',
        )

        # monk_lists only stores the id; no extra fields to sync
        return ResponseUpdateListSchema(**response.json())

    # -------------------------------------------------------------------------
    # Campaigns
    # -------------------------------------------------------------------------

    def create_campaign(self, payload: CreateCampaignSchema) -> CampaignSchema:
        client_list_ids = self._get_client_list_ids(payload.client.id)
        for list_id in payload.campaign.lists:
            if str(list_id) not in client_list_ids:
                raise HTTPException(
                    status_code=HTTPStatus.FORBIDDEN,
                    detail=f'List {list_id} does not belong to client "{payload.client.id}"',
                )

        try:
            response = self.__monk_campaigns.post(payload.campaign.model_dump())
        except requests.RequestException as e:
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail=f'Could not reach Listmonk API: {e}',
            )
        response.raise_for_status()
        return CampaignSchema(**response.json()['data'])

    def get_campaigns(self, client: ClientSchema) -> list[CampaignSchema]:
        client_list_ids = self._get_client_list_ids(client.id)

        response = self.__monk_campaigns.get({'page': 1, 'per_page': 500})
        response.raise_for_status()
        all_campaigns = response.json()['data']['results'] or []

        filtered = [
            CampaignSchema(**c) for c in all_campaigns if any(str(lst['id']) in client_list_ids for lst in c.get('lists', []))
        ]
        return filtered

    def update_campaign(self, campaign_id: int, payload: UpdateCampaignSchema) -> ResponseCampaignSchema:
        campaign = self._get_campaign_raw(campaign_id)
        self._verify_campaign_ownership(campaign, payload.client.id)

        # Listmonk PUT requires a full body; merge current state with the requested changes.
        # The GET response returns `lists` as [{id, name, ...}] objects; PUT expects [id] integers.
        merged = {**campaign, **payload.campaign.model_dump(exclude_none=True)}
        merged['lists'] = [lst['id'] if isinstance(lst, dict) else lst for lst in merged['lists']]

        response = self.__monk_campaigns.put(merged, path=f'/{campaign_id}')
        response.raise_for_status()
        return ResponseCampaignSchema(data=CampaignSchema(**response.json()['data']))

    def delete_campaign(self, campaign_id: int, client: ClientSchema) -> DeleteResponseSchema:
        campaign = self._get_campaign_raw(campaign_id)
        self._verify_campaign_ownership(campaign, client.id)

        response = self.__monk_campaigns.delete({}, path=f'/{campaign_id}')
        response.raise_for_status()
        return DeleteResponseSchema(data=True)

    def set_campaign_status(self, campaign_id: int, status: str, client: ClientSchema) -> CampaignSchema:
        campaign = self._get_campaign_raw(campaign_id)
        self._verify_campaign_ownership(campaign, client.id)

        response = self.__monk_campaigns.post({'status': status}, path=f'/{campaign_id}/status')
        response.raise_for_status()
        return CampaignSchema(**response.json()['data'])


interface = Interface(MonkLists, MonkCampaigns, get_pocketbase_session())


def get_interface_api():
    return interface
