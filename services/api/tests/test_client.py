from http import HTTPStatus

MXF = {'X-Instance-ID': 'mxf'}


def test_get_client(client, created_list):
    response = client.get('/v1/client', headers=MXF)

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['id'] == 'mxf'
    assert data['default_list'] is not None
    assert created_list['id'] in data['lists']


def test_get_client_unknown_returns_404(client):
    response = client.get('/v1/client', headers={'X-Instance-ID': 'never-registered-client'})

    assert response.status_code == HTTPStatus.NOT_FOUND
