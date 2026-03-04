from http import HTTPStatus

from fastapi import APIRouter

from . import CreateListSchema, ListSchema
from . import interface as api

router = APIRouter(
    prefix='/list',
    responses={404: {'description': 'Not found'}},
)


@router.post('/', status_code=HTTPStatus.CREATED, response_model=ListSchema)
def create_list(payload: CreateListSchema):
    return api.create_list(payload)


@router.get('/')
def get_campaing():
    pass


@router.update('/')
def update_campaing():
    pass


@router.delete('/')
def delete_campaing():
    pass


@router.post('/start')
def start_campaing():
    pass


@router.post('/stop')
def stop_campaing():
    pass
