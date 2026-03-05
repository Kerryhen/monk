from http import HTTPStatus
from typing import Annotated

import requests
from fastapi import Depends, HTTPException
from pocketbase.errors import ClientResponseError

from app.schemas import CreateListSchema, DeleteListResonseSchema, ListSchema, ResponseUpdateListSchema
from app.sessions import Monk, PocketBaseSession, get_pocketbase_session
from app.sessions import get_monk_session as get_monk_session
from app.settings import Settings as Settings

settings = Settings()
url_monk = f'{settings.LISTMONK_API_URL}/lists'
auth_monk = (settings.LISTMONK_USER, settings.LISTMONK_TOKEN)

Monk = Monk(auth_creds=auth_monk, url=url_monk)
Pocket = Annotated[PocketBaseSession, Depends(get_pocketbase_session)]


class Interface:
    def __init__(self, monk, pb):
        self.__monk = monk
        self.__pb = pb

    def create_list(self, payload: CreateListSchema, client: str) -> ListSchema:
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
            response = self.__monk.post(payload.model_dump())
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

    def delete_list(self, params) -> DeleteListResonseSchema:
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

        self.__monk.delete(params=params.model_dump(exclude_none=True))

        return DeleteListResonseSchema(data=True)

    def update_list(self, list_id, list_values):
        response = self.__monk.put(
            list_values.model_dump(),
            path=f'/{list_id}',
        )

        # monk_lists only stores the id; no extra fields to sync
        return ResponseUpdateListSchema(**response.json())


interface = Interface(Monk, get_pocketbase_session())


def get_interface_api():
    return interface
