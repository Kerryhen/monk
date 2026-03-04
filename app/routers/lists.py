import logging
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.schemas import (
    CreateListSchema,
    DeleteListResonseSchema,
    DeleteListSchema,
    ListSchema,
    ResponseUpdateListSchema,
    UpdateListSchema,
)
from app.sessions import PocketBaseSession, get_pocketbase_session
from app.settings import Settings

from . import Interface, get_interface_api

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger.warning('Started')

settings = Settings()

router = APIRouter(
    prefix='/list',
    responses={404: {'description': 'Not found'}},
)


# Monk = Annotated[MonkSession, Depends(get_monk_session)]
Pocket = Annotated[PocketBaseSession, Depends(get_pocketbase_session)]
DeleteListParams = Annotated[DeleteListSchema, Query()]
Api = Annotated[Interface, Depends(get_interface_api)]

url_monk = f'{settings.LISTMONK_API_URL}/lists'
auth_monk = (settings.LISTMONK_USER, settings.LISTMONK_TOKEN)


@router.post('/', status_code=HTTPStatus.CREATED, response_model=ListSchema)
def create_list(payload: CreateListSchema, client: str, api: Api):
    """
    Create a new list in Listmonk via its API and update PocketBase.
    """
    return api.create_list(payload, client)


@router.delete('/', status_code=HTTPStatus.OK, response_model=DeleteListResonseSchema)
def delete_list(params: DeleteListParams, api: Api):
    return api.delete_list(params)


@router.patch('/{list_id}', response_model=ResponseUpdateListSchema)
def patch_list(list_id: str, list_values: UpdateListSchema, api: Api):
    return api.update_list(list_id, list_values)
