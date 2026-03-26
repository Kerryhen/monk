from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Path

from app.handlers import get_schema_provider, get_template_provider
from app.handlers.chatwoot.handler import fetch_chatwoot_config
from app.sessions import get_pocketbase_session

router = APIRouter(prefix='/channels', tags=['channels'])

_HandlerPath = Annotated[str, Path(description='Messenger handler name', example='chatwoot')]
_ChannelPath = Annotated[str, Path(description='Channel type', example='whatsapp')]
_InstanceHeader = Annotated[str, Header(description='Instance identifier', example='87v79w2os56q298')]


@router.get('/{handler}/{channel}/schemas')
def list_schemas(
    handler: _HandlerPath,
    channel: _ChannelPath,
) -> dict:
    """Return all JSON schemas available for the given handler and channel."""
    return get_schema_provider(handler, channel).get_schemas()


@router.get('/{handler}/{channel}/schemas/{name}')
def get_schema(
    handler: _HandlerPath,
    channel: _ChannelPath,
    name: Annotated[str, Path(description='Schema name', example='lead')],
) -> dict:
    """Return a specific JSON schema by name for the given handler and channel."""
    provider = get_schema_provider(handler, channel)
    try:
        return provider.get_schema(name)
    except KeyError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Schema "{name}" not found')


@router.get('/{handler}/{channel}/templates')
def list_templates(
    handler: _HandlerPath,
    channel: _ChannelPath,
    x_instance_id: _InstanceHeader,
) -> list:
    """Return all approved message templates for the given handler, channel, and instance."""
    pb = get_pocketbase_session()
    config = fetch_chatwoot_config(pb, x_instance_id, handler, channel)
    if config is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'No config for instance "{x_instance_id}" handler="{handler}" channel="{channel}"',
        )
    return get_template_provider(handler, channel).get_templates(config)
