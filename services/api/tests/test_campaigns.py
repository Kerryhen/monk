# tests/test_campaigns.py
from http import HTTPStatus

from app.interface import interface
from app.schemas import ClientSchema, CreateCampaignSchema, LM_CreateCampaignSchema


def test_create_campaign(client, created_campaign):
    assert created_campaign['id'] is not None
    assert created_campaign['name'] == 'Automated Campaign Test'
    assert created_campaign['subject'] == 'Test Subject'
    assert created_campaign['status'] == 'draft'


def test_get_campaigns(client, created_campaign):
    response = client.get('/campaign/', params={'client': 'mxf'})
    assert response.status_code == HTTPStatus.OK
    campaigns = response.json()
    assert isinstance(campaigns, list)
    ids = [c['id'] for c in campaigns]
    assert created_campaign['id'] in ids


def test_update_campaign(client, created_campaign):
    campaign_id = created_campaign['id']
    response = client.put(
        f'/campaign/{campaign_id}',
        params={'client': 'mxf'},
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

    response = client.delete(f'/campaign/{campaign.id}', params={'client': 'mxf'})
    assert response.status_code == HTTPStatus.OK
    assert response.json()['data'] is True
