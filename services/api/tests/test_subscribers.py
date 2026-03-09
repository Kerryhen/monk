import io
from http import HTTPStatus

import pytest

from app.interface import interface

TEST_EMAIL = 'testimport@example.com'


@pytest.fixture(autouse=True)
def cleanup_test_subscriber():
    yield
    interface.delete_subscriber_by_email(TEST_EMAIL)


def test_import_to_default_list(client, created_list):
    """Import without list_id enrolls subscribers in the client's default list."""
    csv_content = f'email,name\n{TEST_EMAIL},Test User\n'.encode()
    response = client.post(
        '/v1/subscriber/import?client=mxf',
        files={'file': ('subscribers.csv', io.BytesIO(csv_content), 'text/csv')},
    )
    assert response.status_code == HTTPStatus.OK


def test_import_to_specific_list(client, created_list):
    """Import with a valid list_id owned by the client enrolls in that list."""
    csv_content = f'email,name\n{TEST_EMAIL},Test User\n'.encode()
    response = client.post(
        f'/v1/subscriber/import?client=mxf&list_id={created_list["id"]}',
        files={'file': ('subscribers.csv', io.BytesIO(csv_content), 'text/csv')},
    )
    assert response.status_code == HTTPStatus.OK


def test_import_with_invalid_list_falls_back_to_default(client, created_list):
    """Import with a list_id not owned by the client silently falls back to default."""
    csv_content = f'email,name\n{TEST_EMAIL},Test User\n'.encode()
    response = client.post(
        '/v1/subscriber/import?client=mxf&list_id=99999',
        files={'file': ('subscribers.csv', io.BytesIO(csv_content), 'text/csv')},
    )
    assert response.status_code == HTTPStatus.OK


def test_json_import_to_default_list(client, created_list):
    """JSON import without list_id enrolls subscribers in the client's default list."""
    response = client.post(
        '/v1/subscriber/import/json?client=mxf',
        json=[{'email': TEST_EMAIL, 'name': 'Test User'}],
    )
    assert response.status_code == HTTPStatus.OK


def test_json_import_to_specific_list(client, created_list):
    """JSON import with a valid list_id owned by the client enrolls in that list."""
    response = client.post(
        f'/v1/subscriber/import/json?client=mxf&list_id={created_list["id"]}',
        json=[{'email': TEST_EMAIL, 'name': 'Test User'}],
    )
    assert response.status_code == HTTPStatus.OK


def test_json_import_with_invalid_list_falls_back_to_default(client, created_list):
    """JSON import with a list_id not owned by the client silently falls back to default."""
    response = client.post(
        '/v1/subscriber/import/json?client=mxf&list_id=99999',
        json=[{'email': TEST_EMAIL, 'name': 'Test User'}],
    )
    assert response.status_code == HTTPStatus.OK
