from http import HTTPStatus
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.interface import Interface, get_interface_api
from app.schemas import (
    ClientSchema,
    CreateListSchema,
    DeleteListSchema,
    DeleteResponseSchema,
    ListSchema,
    LM_CreateListSchema,
    LM_UpdateListSchema,
    ResponseUpdateListSchema,
    UpdateListSchema,
)
from app.sessions import PocketBaseSession, get_pocketbase_session
from app.settings import Settings

settings = Settings()

router = APIRouter(
    prefix='/list',
    responses={404: {'description': 'Not found'}},
)

Pocket = Annotated[PocketBaseSession, Depends(get_pocketbase_session)]
Api = Annotated[Interface, Depends(get_interface_api)]


@router.post('/', status_code=HTTPStatus.CREATED, response_model=ListSchema)
def create_list(payload: LM_CreateListSchema, client: str, api: Api):
    """Create a new list in Listmonk and record ownership in PocketBase."""
    return api.create_list(CreateListSchema(client=ClientSchema(id=client), list=payload))


@router.delete('/', status_code=HTTPStatus.OK, response_model=DeleteResponseSchema)
def delete_list(
    client: str,
    api: Api,
    ids: Annotated[Optional[list[int]], Query(alias='id')] = None,
    query: Optional[str] = None,
):
    return api.delete_list(DeleteListSchema(client=ClientSchema(id=client), id=ids, query=query))


@router.patch('/{list_id}', response_model=ResponseUpdateListSchema)
def patch_list(list_id: str, payload: LM_UpdateListSchema, client: str, api: Api):
    return api.update_list(list_id, UpdateListSchema(client=ClientSchema(id=client), list=payload))
