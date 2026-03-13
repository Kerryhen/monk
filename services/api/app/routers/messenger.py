from fastapi import APIRouter

from app.handlers import get_handler
from app.schemas import MessengerPayload

router = APIRouter(prefix='/messenger', tags=['messenger'])


@router.post('/{handler_name}')
def receive_message(handler_name: str, payload: MessengerPayload):
    get_handler(handler_name).send(payload)
    return {'status': 'ok'}
