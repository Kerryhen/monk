from http import HTTPStatus

from fastapi import HTTPException

from app.handlers.base import MessengerHandlerBase
from app.handlers.chatwoot import ChatwootHandler
from app.handlers.fake import FakeHandler
from app.handlers.resolver import DefaultVariableResolver

# Pre-configured singleton instances (PROB-02/ALT-B).
# The factory returns existing instances — no per-request instantiation needed.
HANDLERS: dict[str, MessengerHandlerBase] = {
    'fake': FakeHandler(),
    'chatwoot': ChatwootHandler(resolver=DefaultVariableResolver()),
}


def get_handler(name: str) -> MessengerHandlerBase:
    handler = HANDLERS.get(name)
    if handler is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Unknown messenger handler: "{name}"')
    return handler
