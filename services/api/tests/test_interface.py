from app.interface import interface
from app.schemas import CreateListSchema, DeleteListSchema, UpdateListSchema


def test_create_list():
    payload = CreateListSchema(
        name='teste', type='private', optin='single', status='active', tags=['test_list'], description='a test list'
    )

    response = interface.create_list(payload, 'teste')
    assert response.name == payload.name

    interface.delete_list(DeleteListSchema(id=[response.id]))


def test_delete_list(created_list):
    result = interface.delete_list(DeleteListSchema(id=[created_list['id']]))
    assert result.data is True


def test_update_list(created_list):
    updated = interface.update_list(created_list['id'], UpdateListSchema(name='Updated Name'))
    assert updated.data.name == 'Updated Name'
