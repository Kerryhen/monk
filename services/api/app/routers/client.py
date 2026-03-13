from typing import Annotated

from fastapi import APIRouter, Depends, Header

from app.interface import Interface, get_interface_api
from app.schemas import ClientInfoSchema, ClientSchema

router = APIRouter(
    prefix='/client',
    responses={404: {'description': 'Not found'}},
)

Api = Annotated[Interface, Depends(get_interface_api)]
InstanceID = Annotated[str, Header()]


@router.get('', response_model=ClientInfoSchema)
def get_client(api: Api, x_instance_id: InstanceID):
    """Return ownership info for the client: default list and all owned list IDs."""
    return api.get_client(ClientSchema(id=x_instance_id))
