from http import HTTPStatus

from fastapi import HTTPException

from app.handlers.base import MessengerHandlerBase
from app.handlers.fake import FakeHandler

HANDLERS: dict[str, type[MessengerHandlerBase]] = {
    'fake': FakeHandler,
}


def get_handler(name: str) -> MessengerHandlerBase:
    handler_class = HANDLERS.get(name)
    if handler_class is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f'Unknown messenger handler: "{name}"')
    return handler_class()
