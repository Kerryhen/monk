# tests/conftest.py
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from app.main import app
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
def created_list(client, list_payload):
    response = client.post('/list?client=mxf', json=list_payload)
    assert response.status_code == HTTPStatus.CREATED

    data = response.json()

    # provide the created list to the test
    return data

    # automatic cleanup
    client.delete('/list', params={'id': [data['id']]})
