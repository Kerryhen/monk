# tests/test_lists.py
from http import HTTPStatus

import pytest


@pytest.mark.skip(reason='OldVersion')
def test_full_list(client):
    payload = {
        'name': 'Automated Test',
        'type': 'public',
        'optin': 'double',
        'tags': ['marketing', 'email'],
        'description': 'Automatic generated List',
    }

    response = client.post('/list?client=mxf', json=payload)

    assert response.status_code == HTTPStatus.CREATED

    data = response.json()
    assert data['name'] == payload['name']
    assert data['optin'] == payload['optin']
    assert data['status'] == 'active'
    assert data['tags'] == payload['tags']

    payload['name'] = 'Updated Name'

    response3 = client.request('PATCH', f'/list/{data["id"]}', json=payload)

    assert response3.json().get('name', None) == 'Updated Name'

    p2 = {'id': [data['id']]}
    response2 = client.request('DELETE', '/list', json=p2)
    assert response2.status_code == HTTPStatus.OK


def test_create_list(client, list_payload):
    response = client.post('/list?client=mxf', json=list_payload)

    assert response.status_code == HTTPStatus.CREATED

    data = response.json()
    assert data['name'] == list_payload['name']
    assert data['optin'] == list_payload['optin']
    assert data['status'] == 'active'
    assert data['tags'] == list_payload['tags']

    # cleanup for this standalone test
    client.delete('/list', params={'id': [data['id']]})


# @pytest.mark.skip(reason='OldVersion')
def test_update_list(client, created_list):
    updated_payload = {
        'name': 'Updated Name',
    }

    response = client.patch(
        f'/list/{created_list["id"]}',
        json=updated_payload,
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['data']['name'] == 'Updated Name'


# @pytest.mark.skip(reason='OldVersion')
def test_delete_list(client, created_list):
    response = client.delete(
        '/list',
        params={'id': [created_list['id']]},
    )

    assert response.status_code == HTTPStatus.OK
