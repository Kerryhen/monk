from app.interface import interface
from app.schemas import (
    ClientSchema,
    CreateListSchema,
    DeleteListSchema,
    LM_CreateListSchema,
    LM_UpdateListSchema,
    UpdateListSchema,
)


def test_create_list():
    payload = CreateListSchema(
        client=ClientSchema(id='teste'),
        list=LM_CreateListSchema(name='teste', type='private', optin='single', tags=['test_list'], description='a test list'),
    )

    response = interface.create_list(payload)
    assert response.name == payload.list.name

    interface.delete_list(DeleteListSchema(client=ClientSchema(id='teste'), id=[response.id]))


def test_delete_list(created_list):
    result = interface.delete_list(DeleteListSchema(client=ClientSchema(id='mxf'), id=[created_list['id']]))
    assert result.data is True


def test_update_list(created_list):
    payload = UpdateListSchema(
        client=ClientSchema(id='mxf'),
        list=LM_UpdateListSchema(name='Updated Name'),
    )
    updated = interface.update_list(created_list['id'], payload)
    assert updated.data.name == 'Updated Name'
