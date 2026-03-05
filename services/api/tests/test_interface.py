from app.routers import interface as api
from app.schemas import CreateListSchema


def test_create_list():
    payload = CreateListSchema(
        id=0, name='teste', type='private', optin='single', status='active', tags=['test_list'], description='a test list'
    )

    response = api.create_list(payload, 'teste')
    assert response.model_dump()['name'] == payload.name
