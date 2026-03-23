from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.handlers import get_schema_provider, get_template_provider
from app.handlers.chatwoot.handler import fetch_chatwoot_config
from app.sessions import get_pocketbase_session

router = APIRouter(prefix='/channels', tags=['channels'])


@router.get('/{handler}/{channel}/schemas')
def list_schemas(handler: str, channel: str) -> dict:
    return get_schema_provider(handler, channel).get_schemas()


@router.get('/{handler}/{channel}/schemas/{name}')
def get_schema(handler: str, channel: str, name: str) -> dict:
    provider = get_schema_provider(handler, channel)
    try:
        return provider.get_schema(name)
    except KeyError:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Schema "{name}" not found')


@router.get('/{handler}/{channel}/templates')
def list_templates(handler: str, channel: str, instance_id: Annotated[str, Query()]) -> list:
    pb = get_pocketbase_session()
    config = fetch_chatwoot_config(pb, instance_id)
    if config is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'No config for instance "{instance_id}" handler="{handler}" channel="{channel}"',
        )
    return get_template_provider(handler, channel).get_templates(config)
