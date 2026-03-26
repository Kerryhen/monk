# tests/test_e2e.py
"""Full point-to-point flow tests: new client → import subscribers → run campaign."""

from http import HTTPStatus

import pytest

from app.interface import interface
from app.schemas import ClientSchema, DeleteListSchema

E2E_CLIENT = 'e2e-test-client'
E2E_CLIENT_HDR = {'X-Instance-ID': E2E_CLIENT}
E2E_EMAIL = 'e2e-subscriber@example.com'


@pytest.fixture(autouse=True)
def cleanup_e2e_client():
    yield
    try:
        info = interface.get_client(ClientSchema(id=E2E_CLIENT))
        if info.lists:
            interface.delete_list(DeleteListSchema(client=ClientSchema(id=E2E_CLIENT), id=info.lists))
    except Exception:
        pass
    interface.delete_subscriber_by_email(E2E_EMAIL)


def test_new_client_import_and_run_campaign(client):
    """
    Full flow for a brand-new client:
      1. Import a subscriber (auto-creates client + default list).
      2. Retrieve client info to obtain the auto-created list ID.
      3. Create a campaign targeting that list.
      4. Start the campaign.
    """
    # Step 1: import subscriber — client does not exist yet
    response = client.post(
        '/v1/subscriber/import/json',
        json=[{'email': E2E_EMAIL, 'name': 'E2E User'}],
        headers=E2E_CLIENT_HDR,
    )
    assert response.status_code == HTTPStatus.OK

    # Step 2: client and default list must now exist
    info_response = client.get('/v1/client', headers=E2E_CLIENT_HDR)
    assert info_response.status_code == HTTPStatus.OK
    info = info_response.json()
    assert info['default_list'] is not None
    default_list_id = info['default_list']

    # Step 3: create campaign on the auto-created list
    campaign_response = client.post(
        '/v1/campaign/',
        headers=E2E_CLIENT_HDR,
        json={
            'name': 'E2E Test Campaign',
            'subject': 'E2E Subject',
            'lists': [default_list_id],
            'type': 'regular',
            'content_type': 'plain',
            'body': 'Hello from the e2e test.',
        },
    )
    assert campaign_response.status_code == HTTPStatus.CREATED
    campaign_id = campaign_response.json()['id']

    try:
        # Step 4: start the campaign
        start_response = client.post(f'/v1/campaign/{campaign_id}/start', headers=E2E_CLIENT_HDR)
        assert start_response.status_code == HTTPStatus.OK
        assert start_response.json()['status'] in {'running', 'finished'}
    finally:
        interface.delete_campaign(campaign_id, ClientSchema(id=E2E_CLIENT))
