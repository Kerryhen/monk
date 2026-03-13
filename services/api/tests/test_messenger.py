# tests/test_messenger.py
from http import HTTPStatus

from app.handlers.fake import FakeHandler

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


def test_fake_handler_captures_payload(client):
    """FakeHandler must store received payloads for test inspection."""
    FakeHandler.clear()
    client.post('/v1/messenger/fake', json=VALID_PAYLOAD)
    assert len(FakeHandler.received) == 1
    msg = FakeHandler.received[0]
    assert msg.subject == VALID_PAYLOAD['subject']
    assert msg.recipients[0].email == VALID_PAYLOAD['recipients'][0]['email']
