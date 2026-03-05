import io
from http import HTTPStatus


def test_import_subscribers(client, created_list):
    csv_content = b'email,name\ntestimport@example.com,Test User\n'
    response = client.post(
        '/subscriber/import?client=mxf',
        files={'file': ('subscribers.csv', io.BytesIO(csv_content), 'text/csv')},
    )
    assert response.status_code == HTTPStatus.OK
