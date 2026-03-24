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


@router.post('', status_code=HTTPStatus.CREATED, response_model=CampaignSchema)
def create_campaign(body: LM_CreateCampaignSchema, iface: InterfaceAPI, x_instance_id: InstanceID):
    """Create a new campaign.

    For **email** campaigns set `messenger` to `email` and pass a plain string as `body`.

    For **WhatsApp** campaigns set `messenger` to `whatsapp` and pass a structured object
    as `body` containing `template_params` with the template name, language, category, and
    `processed_params.body` — a mapping of slot numbers to **resolver references**.

    ### Resolver references (`processed_params.body`)

    Each value in `processed_params.body` is a dot-path into the recipient context,
    optionally followed by a colon and a default value:

    ```
    schema.field:default_value
    schema.field.subfield
    ```

    Available schemas: `lead`, `campanha`, `instancia`.

    | Reference | Resolves to |
    |---|---|
    | `lead.name` | Recipient name |
    | `lead.email` | Recipient email |
    | `lead.attribs.phone` | Custom subscriber attribute |
    | `campanha.name` | Campaign name |
    | `campanha.subject` | Campaign subject |
    | `instancia.razao_social` | Instance company name |

    If the field is missing and no default is given, the recipient is **skipped**.
    If a default is given (e.g. `lead.name:amigo`), the default is used instead.

    URLs are valid defaults — the colon split stops at the first `:`, so
    `lead.attribs.payment_link:https://pay.example.com/default` works correctly.

    ### Discovering templates and schemas

    Use the helper endpoints before building the campaign body:

    - `GET /v1/channels/chat/whatsapp/templates` — lists all approved WhatsApp templates
      for your instance, including their slot structure and parameter counts.
    - `GET /v1/channels/chat/whatsapp/schemas` — lists all JSON schemas describing the
      fields available in the resolver context (lead, campanha, instancia).
    - `GET /v1/channels/chat/whatsapp/schemas/{name}` — returns the full JSON schema for
      a specific context object, useful for building a UI that maps subscriber attributes
      to template slots.
    """
    payload = CreateCampaignSchema(client=ClientSchema(id=x_instance_id), campaign=body)
    return iface.create_campaign(payload)


@router.get('', response_model=List[CampaignSchema])
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
