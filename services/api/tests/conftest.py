# tests/conftest.py
import pytest
from fastapi.testclient import TestClient

from app.interface import interface
from app.main import app
from app.schemas import CreateListSchema, DeleteListSchema
from app.sessions import MonkSession, get_monk_session
from app.settings import Settings

settings = Settings()


@pytest.fixture(scope='session')
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def override_monk():
    def fake_monk():
        return MonkSession(username=settings.LISTMONK_USER)

    app.dependency_overrides[get_monk_session] = fake_monk
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def list_payload():
    return {
        'name': 'Automated Test',
        'type': 'public',
        'optin': 'double',
        'tags': ['marketing', 'email'],
        'description': 'Automatic generated List',
    }


@pytest.fixture
def created_list(list_payload):
    payload = CreateListSchema(**list_payload)
    list_obj = interface.create_list(payload, 'mxf')
    yield list_obj.model_dump()
    interface.delete_list(DeleteListSchema(id=[list_obj.id]))
