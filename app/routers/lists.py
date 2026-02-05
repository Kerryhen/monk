from http import HTTPStatus
from typing import Annotated

import requests
from fastapi import APIRouter, Depends, HTTPException
from pocketbase.errors import ClientResponseError

from app.schemas import CreateListSchema, DeleteListResonseSchema, DeleteListSchema, ListSchema
from app.sessions import MonkSession, PocketBaseSession, get_monk_session, get_pocketbase_session
from app.settings import Settings

settings = Settings()

router = APIRouter(
    prefix='/list',
    responses={404: {'description': 'Not found'}},
)

Monk = Annotated[MonkSession, Depends(get_monk_session)]
Pocket = Annotated[PocketBaseSession, Depends(get_pocketbase_session)]

url_monk = f'{settings.LISTMONK_API_URL}/lists'
auth_monk = (settings.LISTMONK_USER, settings.LISTMONK_TOKEN)


@router.post('/', status_code=HTTPStatus.CREATED, response_model=ListSchema)
def create_list(payload: CreateListSchema, client: str, pb: Pocket):
    """
    Create a new list in Listmonk via its API and update PocketBase.
    """

    # Ensure proper filter syntax
    list_result = pb.client.collection('monk_client_lists').get_list(1, 1, {'filter': f'client="{client}"'})
    items, total = list_result.items, list_result.total_items
    if total == 0:
        client_record = pb.client.collection('monk_client_lists').create({'client': client, 'lists': []})
        client_id = client_record.id
        existing_lists = []
    else:
        client_id = items[0].id
        existing_lists = items[0].lists

    try:
        response = requests.post(
            url_monk,
            json=payload.model_dump(),
            auth=auth_monk,
            timeout=5,
        )
        response.raise_for_status()  # Raises HTTPError for bad responses
    except requests.RequestException as e:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail=f'Could not reach Listmonk API: {e}',
        )

    result = response.json()
    list_id = result['data']['id']

    pb.client.collection('monk_lists').create({'id': list_id, 'name': payload.name, 'owner': client_id})
    # Update PocketBase client record with new list (append)
    pb.client.collection('monk_client_lists').update(client_id, {'lists': existing_lists + [list_id]})

    return ListSchema(**result['data'])


@router.delete('/', status_code=HTTPStatus.OK, response_model=DeleteListResonseSchema)
def delete_list(payload: DeleteListSchema, pb: Pocket):
    try:
        for _id in payload.id:
            pb.client.collection('monk_lists').delete(str(_id))
    except ClientResponseError:
        pass

    requests.delete(
        url_monk,
        params=payload.model_dump(),
        auth=auth_monk,
        timeout=5,
    )
    return DeleteListResonseSchema(data=True)


@router.patch('/{list_id}', response_model=ListSchema)
def patch_list(list_id: int, list_values: CreateListSchema, pb: Pocket):
    response = requests.patch(f'{url_monk}/{list_id}', json=list_values.model_dump(), auth=auth_monk, timeout=5)
    pb.client.collection('monk_lists').update(list_id, list_values)
    return response
