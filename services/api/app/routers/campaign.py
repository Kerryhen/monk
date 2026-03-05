from http import HTTPStatus
from typing import Annotated, List

from fastapi import APIRouter, Depends

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
from app.sessions import MonkSession, get_monk_session

router = APIRouter(prefix='/campaign', tags=['campaign'])

InterfaceAPI = Annotated[Interface, Depends(get_interface_api)]
MonkAuth = Annotated[MonkSession, Depends(get_monk_session)]


@router.post('/', status_code=HTTPStatus.CREATED, response_model=CampaignSchema)
def create_campaign(client: str, body: LM_CreateCampaignSchema, iface: InterfaceAPI, _: MonkAuth):
    payload = CreateCampaignSchema(client=ClientSchema(id=client), campaign=body)
    return iface.create_campaign(payload)


@router.get('/', response_model=List[CampaignSchema])
def get_campaigns(client: str, iface: InterfaceAPI, _: MonkAuth):
    return iface.get_campaigns(ClientSchema(id=client))


@router.put('/{campaign_id}', response_model=ResponseCampaignSchema)
def update_campaign(campaign_id: int, client: str, body: LM_UpdateCampaignSchema, iface: InterfaceAPI, _: MonkAuth):
    payload = UpdateCampaignSchema(client=ClientSchema(id=client), campaign=body)
    return iface.update_campaign(campaign_id, payload)


@router.delete('/{campaign_id}', response_model=DeleteResponseSchema)
def delete_campaign(campaign_id: int, client: str, iface: InterfaceAPI, _: MonkAuth):
    return iface.delete_campaign(campaign_id, ClientSchema(id=client))


@router.post('/{campaign_id}/start', response_model=CampaignSchema)
def start_campaign(campaign_id: int, client: str, iface: InterfaceAPI, _: MonkAuth):
    return iface.set_campaign_status(campaign_id, 'running', ClientSchema(id=client))


@router.post('/{campaign_id}/stop', response_model=CampaignSchema)
def stop_campaign(campaign_id: int, client: str, iface: InterfaceAPI, _: MonkAuth):
    return iface.set_campaign_status(campaign_id, 'paused', ClientSchema(id=client))
