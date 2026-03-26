import io
from http import HTTPStatus

import pytest

from app.interface import interface
from app.schemas import ClientSchema, DeleteListSchema

TEST_EMAIL = 'testimport@example.com'

MXF = {'X-Instance-ID': 'mxf'}
NEW_CLIENT = 'brand-new-client'
NEW_CLIENT_HDR = {'X-Instance-ID': NEW_CLIENT}


@pytest.fixture
def cleanup_new_client():
    yield
    try:
        info = interface.get_client(ClientSchema(id=NEW_CLIENT))
        if info.lists:
            interface.delete_list(DeleteListSchema(client=ClientSchema(id=NEW_CLIENT), id=info.lists))
    except Exception:
        pass


@pytest.fixture(autouse=True)
def cleanup_test_subscriber():
    yield
    interface.delete_subscriber_by_email(TEST_EMAIL)


def test_import_to_default_list(client, created_list):
    """Import without list_id enrolls subscribers in the client's default list."""
    csv_content = f'email,name\n{TEST_EMAIL},Test User\n'.encode()
    response = client.post(
        '/v1/subscriber/import',
        files={'file': ('subscribers.csv', io.BytesIO(csv_content), 'text/csv')},
        headers=MXF,
    )
    assert response.status_code == HTTPStatus.OK


def test_import_to_specific_list(client, created_list):
    """Import with a valid list_id owned by the client enrolls in that list."""
    csv_content = f'email,name\n{TEST_EMAIL},Test User\n'.encode()
    response = client.post(
        f'/v1/subscriber/import?list_id={created_list["id"]}',
        files={'file': ('subscribers.csv', io.BytesIO(csv_content), 'text/csv')},
        headers=MXF,
    )
    assert response.status_code == HTTPStatus.OK


def test_import_with_invalid_list_returns_404(client, created_list):
    """Import with a list_id not owned by the client returns 404."""
    csv_content = f'email,name\n{TEST_EMAIL},Test User\n'.encode()
    response = client.post(
        '/v1/subscriber/import?list_id=99999',
        files={'file': ('subscribers.csv', io.BytesIO(csv_content), 'text/csv')},
        headers=MXF,
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_json_import_to_default_list(client, created_list):
    """JSON import without list_id enrolls subscribers in the client's default list."""
    response = client.post(
        '/v1/subscriber/import/json',
        json=[{'email': TEST_EMAIL, 'name': 'Test User'}],
        headers=MXF,
    )
    assert response.status_code == HTTPStatus.OK


def test_json_import_to_specific_list(client, created_list):
    """JSON import with a valid list_id owned by the client enrolls in that list."""
    response = client.post(
        f'/v1/subscriber/import/json?list_id={created_list["id"]}',
        json=[{'email': TEST_EMAIL, 'name': 'Test User'}],
        headers=MXF,
    )
    assert response.status_code == HTTPStatus.OK


def test_json_import_with_invalid_list_returns_404(client, created_list):
    """JSON import with a list_id not owned by the client returns 404."""
    response = client.post(
        '/v1/subscriber/import/json?list_id=99999',
        json=[{'email': TEST_EMAIL, 'name': 'Test User'}],
        headers=MXF,
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_import_auto_creates_client_and_default_list(client, cleanup_new_client):
    """CSV import for an unknown client auto-creates the client with a default list."""
    csv_content = f'email,name\n{TEST_EMAIL},Test User\n'.encode()
    response = client.post(
        '/v1/subscriber/import',
        files={'file': ('subscribers.csv', io.BytesIO(csv_content), 'text/csv')},
        headers=NEW_CLIENT_HDR,
    )
    assert response.status_code == HTTPStatus.OK
    info = interface.get_client(ClientSchema(id=NEW_CLIENT))
    assert info.default_list is not None


def test_json_import_auto_creates_client_and_default_list(client, cleanup_new_client):
    """JSON import for an unknown client auto-creates the client with a default list."""
    response = client.post(
        '/v1/subscriber/import/json',
        json=[{'email': TEST_EMAIL, 'name': 'Test User'}],
        headers=NEW_CLIENT_HDR,
    )
    assert response.status_code == HTTPStatus.OK
    info = interface.get_client(ClientSchema(id=NEW_CLIENT))
    assert info.default_list is not None
