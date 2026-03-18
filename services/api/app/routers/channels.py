from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from app.handlers import get_schema_provider, get_template_provider

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
def list_templates(handler: str, channel: str) -> list:
    return get_template_provider(handler, channel).get_templates()
