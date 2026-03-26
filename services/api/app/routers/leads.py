from http import HTTPStatus
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Header, UploadFile

from app.interface import Interface, get_interface_api
from app.schemas import ClientSchema, ImportSubscriberItem

router = APIRouter(
    prefix='/subscriber',
    responses={404: {'description': 'Not found'}},
)

Api = Annotated[Interface, Depends(get_interface_api)]
InstanceID = Annotated[str, Header()]


@router.post('/import', status_code=HTTPStatus.OK)
async def import_subscribers(file: UploadFile, api: Api, x_instance_id: InstanceID, list_id: Optional[int] = None):
    """Upload a CSV of subscribers and enroll them in the specified list (or the client's default list)."""
    content = await file.read()
    return api.import_subscribers(ClientSchema(id=x_instance_id), content, file.filename, list_id)


@router.post('/import/json', status_code=HTTPStatus.OK)
def import_subscribers_json(
    body: list[ImportSubscriberItem],
    api: Api,
    x_instance_id: InstanceID,
    list_id: Optional[int] = None,
):
    """Upload a JSON array of subscribers and enroll them in the specified list (or the client's default list)."""
    return api.import_subscribers_json(ClientSchema(id=x_instance_id), body, list_id)
