# tests/test_lists.py
from http import HTTPStatus


def test_create_list(client):
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

    response3 = client.request('PATCH', '/list', json=payload)
    assert response3.json()['name'] == 'Updated Name'

    p2 = {'id': [data['id']]}
    response2 = client.request('DELETE', '/list', json=p2)
    assert response2.status_code == HTTPStatus.OK
