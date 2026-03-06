from typing import Annotated

from fastapi import APIRouter, Depends

from app.handlers import get_handler
from app.schemas import MessengerPayload
from app.sessions import MonkSession, get_monk_session

router = APIRouter(prefix='/messenger', tags=['messenger'])

MonkAuth = Annotated[MonkSession, Depends(get_monk_session)]


@router.post('/{handler_name}')
def receive_message(handler_name: str, payload: MessengerPayload, _: MonkAuth):
    get_handler(handler_name).send(payload)
    return {'status': 'ok'}
