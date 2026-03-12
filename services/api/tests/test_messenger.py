# tests/test_messenger.py
from http import HTTPStatus

from fastapi.testclient import TestClient

from app.handlers.fake import FakeHandler
from app.main import app
from app.sessions import get_monk_session

VALID_PAYLOAD = {
    'subject': 'Hello',
    'body': 'Test body',
    'content_type': 'plaintext',
    'recipients': [{'uuid': 'abc', 'email': 'x@x.com', 'name': 'X', 'attribs': {}, 'status': 'enabled'}],
    'campaign': {'uuid': 'xyz', 'name': 'Test Campaign', 'tags': []},
    'attachments': [],
}


def test_fake_handler_returns_200(client):
    response = client.post('/v1/messenger/fake', json=VALID_PAYLOAD)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'status': 'ok'}


def test_unknown_handler_returns_404(client):
    response = client.post('/v1/messenger/unknown_handler', json=VALID_PAYLOAD)
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_missing_auth_returns_401():
    # Clear the autouse override so real auth runs, then use a client with no credentials.
    app.dependency_overrides.pop(get_monk_session, None)
    try:
        bare_client = TestClient(app, raise_server_exceptions=False)
        response = bare_client.post('/v1/messenger/fake', json=VALID_PAYLOAD)
        assert response.status_code == HTTPStatus.UNAUTHORIZED
    finally:
        # Restore is handled by the autouse override_monk fixture on the next test.
        pass


def test_fake_handler_captures_payload(client):
    """FakeHandler must store received payloads for test inspection."""
    FakeHandler.clear()
    client.post('/v1/messenger/fake', json=VALID_PAYLOAD)
    assert len(FakeHandler.received) == 1
    msg = FakeHandler.received[0]
    assert msg.subject == VALID_PAYLOAD['subject']
    assert msg.recipients[0].email == VALID_PAYLOAD['recipients'][0]['email']
