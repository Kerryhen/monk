from http import HTTPStatus

from fastapi import HTTPException

from app.handlers.base import MessengerHandlerBase, SchemaProviderBase, TemplateProviderBase
from app.handlers.chatwoot import ChatwootHandler, ChatwootSchemaProvider, ChatwootTemplateProvider
from app.handlers.fake import FakeHandler
from app.handlers.resolver import DefaultVariableResolver

# Pre-configured singleton instances (PROB-02/ALT-B).
HANDLERS: dict[str, MessengerHandlerBase] = {
    'fake': FakeHandler(),
    'chat': ChatwootHandler(resolver=DefaultVariableResolver()),
}

# Provider registries keyed by (handler, channel).
# Parametrized from the start to avoid breaking URL changes later (PROB-09).
SCHEMA_PROVIDERS: dict[tuple[str, str], SchemaProviderBase] = {
    ('chat', 'whatsapp'): ChatwootSchemaProvider(),
}
TEMPLATE_PROVIDERS: dict[tuple[str, str], TemplateProviderBase] = {
    ('chat', 'whatsapp'): ChatwootTemplateProvider(),
}


def get_handler(name: str) -> MessengerHandlerBase:
    handler = HANDLERS.get(name)
    if handler is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Unknown messenger handler: "{name}"')
    return handler


def get_schema_provider(handler: str, channel: str) -> SchemaProviderBase:
    provider = SCHEMA_PROVIDERS.get((handler, channel))
    if provider is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'No schema provider for handler="{handler}" channel="{channel}"',
        )
    return provider


def get_template_provider(handler: str, channel: str) -> TemplateProviderBase:
    provider = TEMPLATE_PROVIDERS.get((handler, channel))
    if provider is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'No template provider for handler="{handler}" channel="{channel}"',
        )
    return provider
