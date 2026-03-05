from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile

from app.interface import Interface, get_interface_api
from app.schemas import ClientSchema
from app.sessions import get_monk_session

router = APIRouter(
    prefix='/subscriber',
    responses={404: {'description': 'Not found'}},
)

Api = Annotated[Interface, Depends(get_interface_api)]


@router.post('/import', status_code=HTTPStatus.OK, dependencies=[Depends(get_monk_session)])
async def import_subscribers(client: str, file: UploadFile, api: Api):
    """Upload a CSV of subscribers and enroll them in the client's default list."""
    content = await file.read()
    return api.import_subscribers(ClientSchema(id=client), content, file.filename)
