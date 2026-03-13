from http import HTTPStatus
from typing import Annotated, List

from fastapi import APIRouter, Depends, Header

from app.interface import Interface, get_interface_api
from app.schemas import (
    CampaignSchema,
    ClientSchema,
    CreateCampaignSchema,
    DeleteResponseSchema,
    LM_CreateCampaignSchema,
    LM_UpdateCampaignSchema,
    ResponseCampaignSchema,
    UpdateCampaignSchema,
)

router = APIRouter(prefix='/campaign', tags=['campaign'])

InterfaceAPI = Annotated[Interface, Depends(get_interface_api)]
InstanceID = Annotated[str, Header()]


@router.post('/', status_code=HTTPStatus.CREATED, response_model=CampaignSchema)
def create_campaign(body: LM_CreateCampaignSchema, iface: InterfaceAPI, x_instance_id: InstanceID):
    payload = CreateCampaignSchema(client=ClientSchema(id=x_instance_id), campaign=body)
    return iface.create_campaign(payload)


@router.get('/', response_model=List[CampaignSchema])
def get_campaigns(iface: InterfaceAPI, x_instance_id: InstanceID):
    return iface.get_campaigns(ClientSchema(id=x_instance_id))


@router.put('/{campaign_id}', response_model=ResponseCampaignSchema)
def update_campaign(
    campaign_id: int,
    body: LM_UpdateCampaignSchema,
    iface: InterfaceAPI,
    x_instance_id: InstanceID,
):
    payload = UpdateCampaignSchema(client=ClientSchema(id=x_instance_id), campaign=body)
    return iface.update_campaign(campaign_id, payload)


@router.delete('/{campaign_id}', response_model=DeleteResponseSchema)
def delete_campaign(campaign_id: int, iface: InterfaceAPI, x_instance_id: InstanceID):
    return iface.delete_campaign(campaign_id, ClientSchema(id=x_instance_id))


@router.post('/{campaign_id}/start', response_model=CampaignSchema)
def start_campaign(campaign_id: int, iface: InterfaceAPI, x_instance_id: InstanceID):
    return iface.set_campaign_status(campaign_id, 'running', ClientSchema(id=x_instance_id))


@router.post('/{campaign_id}/stop', response_model=CampaignSchema)
def stop_campaign(campaign_id: int, iface: InterfaceAPI, x_instance_id: InstanceID):
    return iface.set_campaign_status(campaign_id, 'paused', ClientSchema(id=x_instance_id))
