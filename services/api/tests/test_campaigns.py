# tests/test_campaigns.py
from http import HTTPStatus

import pytest

from app.interface import interface
from app.schemas import (
    ClientSchema,
    CreateCampaignSchema,
    CreateListSchema,
    DeleteListSchema,
    LM_CreateCampaignSchema,
    LM_CreateListSchema,
)

MXF = {'X-Instance-ID': 'mxf'}


@pytest.fixture
def created_foreign_list():
    """A list belonging to a different client, used to test ownership enforcement."""
    payload = CreateListSchema(
        client=ClientSchema(id='other_test_client'),
        list=LM_CreateListSchema(name='Foreign Test List', type='public', optin='single'),
    )
    list_obj = interface.create_list(payload)
    yield list_obj.model_dump()
    interface.delete_list(DeleteListSchema(client=ClientSchema(id='other_test_client'), id=[list_obj.id]))


def test_create_campaign(client, created_campaign):
    assert created_campaign['id'] is not None
    assert created_campaign['name'] == 'Automated Campaign Test'
    assert created_campaign['subject'] == 'Test Subject'
    assert created_campaign['status'] == 'draft'


def test_get_campaigns(client, created_campaign):
    response = client.get('/v1/campaign/', headers=MXF)
    assert response.status_code == HTTPStatus.OK
    campaigns = response.json()
    assert isinstance(campaigns, list)
    ids = [c['id'] for c in campaigns]
    assert created_campaign['id'] in ids


def test_update_campaign(client, created_campaign):
    campaign_id = created_campaign['id']
    response = client.put(
        f'/v1/campaign/{campaign_id}',
        headers=MXF,
        json={'name': 'Updated Campaign Name'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['data']['name'] == 'Updated Campaign Name'


def test_delete_campaign(client, created_list):
    payload = CreateCampaignSchema(
        client=ClientSchema(id='mxf'),
        campaign=LM_CreateCampaignSchema(
            name='Campaign To Delete',
            subject='Delete Me',
            lists=[created_list['id']],
            type='regular',
            content_type='plain',
            body='Temporary campaign.',
        ),
    )
    campaign = interface.create_campaign(payload)

    response = client.delete(f'/v1/campaign/{campaign.id}', headers=MXF)
    assert response.status_code == HTTPStatus.OK
    assert response.json()['data'] is True


def test_create_campaign_rejects_foreign_list(client, created_list, created_foreign_list):
    """Creating a campaign with a list not owned by the client must return 403."""
    response = client.post(
        '/v1/campaign/',
        headers=MXF,
        json={
            'name': 'Unauthorized Campaign',
            'subject': 'Should Fail',
            'lists': [created_foreign_list['id']],
            'type': 'regular',
            'content_type': 'plain',
            'body': 'This should not be created.',
        },
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_update_campaign_rejects_foreign_list(client, created_campaign, created_foreign_list):
    """Updating a campaign to use a list not owned by the client must return 403."""
    response = client.put(
        f'/v1/campaign/{created_campaign["id"]}',
        headers=MXF,
        json={'lists': [{'id': created_foreign_list['id']}]},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_update_campaign_rejects_foreign_campaign(client, created_list, created_foreign_list):
    """Updating a campaign owned by another client must return 403."""
    foreign_campaign = interface.create_campaign(
        CreateCampaignSchema(
            client=ClientSchema(id='other_test_client'),
            campaign=LM_CreateCampaignSchema(
                name='Foreign Campaign',
                subject='Foreign Subject',
                lists=[created_foreign_list['id']],
                type='regular',
                content_type='plain',
                body='Foreign body.',
            ),
        )
    )
    try:
        response = client.put(
            f'/v1/campaign/{foreign_campaign.id}',
            headers=MXF,
            json={'name': 'Hijacked'},
        )
        assert response.status_code == HTTPStatus.FORBIDDEN
    finally:
        interface.delete_campaign(foreign_campaign.id, ClientSchema(id='other_test_client'))


def test_delete_campaign_rejects_foreign_campaign(client, created_list, created_foreign_list):
    """Deleting a campaign owned by another client must return 403."""
    foreign_campaign = interface.create_campaign(
        CreateCampaignSchema(
            client=ClientSchema(id='other_test_client'),
            campaign=LM_CreateCampaignSchema(
                name='Foreign Campaign To Delete',
                subject='Foreign Subject',
                lists=[created_foreign_list['id']],
                type='regular',
                content_type='plain',
                body='Foreign body.',
            ),
        )
    )
    try:
        response = client.delete(f'/v1/campaign/{foreign_campaign.id}', headers=MXF)
        assert response.status_code == HTTPStatus.FORBIDDEN
    finally:
        interface.delete_campaign(foreign_campaign.id, ClientSchema(id='other_test_client'))


def test_start_campaign(client, created_campaign):
    """Starting a campaign must return 200 and transition status to running or finished."""
    campaign_id = created_campaign['id']
    response = client.post(f'/v1/campaign/{campaign_id}/start', headers=MXF)
    assert response.status_code == HTTPStatus.OK
    assert response.json()['status'] in {'running', 'finished'}


def test_stop_campaign(client, created_campaign):
    """Stopping a running campaign must return 200 with status paused."""
    campaign_id = created_campaign['id']
    start = client.post(f'/v1/campaign/{campaign_id}/start', headers=MXF)
    if start.json()['status'] == 'finished':
        pytest.skip('Campaign finished immediately (no subscribers in list)')
    response = client.post(f'/v1/campaign/{campaign_id}/stop', headers=MXF)
    assert response.status_code == HTTPStatus.OK
    assert response.json()['status'] == 'paused'
