# tests/test_channels.py
from http import HTTPStatus
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Schema endpoints (unchanged behaviour)
# ---------------------------------------------------------------------------


def test_list_schemas_returns_all_sources(client):
    response = client.get('/v1/channels/chatwoot/whatsapp/schemas')
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert set(data.keys()) == {'lead', 'campanha', 'instancia'}


def test_get_schema_lead_has_expected_fields(client):
    response = client.get('/v1/channels/chatwoot/whatsapp/schemas/lead')
    assert response.status_code == HTTPStatus.OK
    schema = response.json()
    properties = schema.get('properties', {})
    for field in ('uuid', 'email', 'name', 'status', 'attribs'):
        assert field in properties, f'Expected field "{field}" in lead schema'


def test_get_schema_campanha_has_expected_fields(client):
    response = client.get('/v1/channels/chatwoot/whatsapp/schemas/campanha')
    assert response.status_code == HTTPStatus.OK
    properties = response.json().get('properties', {})
    for field in ('uuid', 'name', 'subject', 'tags'):
        assert field in properties


def test_get_schema_unknown_returns_404(client):
    response = client.get('/v1/channels/chatwoot/whatsapp/schemas/schema_inexistente')
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_unknown_handler_schemas_returns_404(client):
    response = client.get('/v1/channels/unknown/whatsapp/schemas')
    assert response.status_code == HTTPStatus.NOT_FOUND


# ---------------------------------------------------------------------------
# Templates endpoint — requires instance_id query param
# ---------------------------------------------------------------------------

_FAKE_CONFIG = {
    'url': 'https://chatwoot.example.com',
    'api_token_templates': 'xpto',
    'account_id': '3',
}

_FAKE_TEMPLATE = {
    'id': '918383884459546',
    'name': 'resgatar_conversa_01',
    'status': 'APPROVED',
    'category': 'UTILITY',
    'language': 'pt_BR',
    'components': [{'type': 'BODY', 'text': 'Olá, tudo bem?'}],
    'parameter_format': 'POSITIONAL',
}

_FAKE_INBOXES_RESPONSE = {'payload': [{'id': 8, 'message_templates': [_FAKE_TEMPLATE]}]}


def test_list_templates_missing_instance_id_returns_422(client):
    response = client.get('/v1/channels/chatwoot/whatsapp/templates')
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_list_templates_unknown_instance_returns_404(client):
    with patch('app.routers.channels.fetch_chatwoot_config', return_value=None):
        response = client.get('/v1/channels/chatwoot/whatsapp/templates?instance_id=unknown')
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_list_templates_returns_non_empty_list(client):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = _FAKE_INBOXES_RESPONSE

    with (
        patch('app.routers.channels.fetch_chatwoot_config', return_value=_FAKE_CONFIG),
        patch('app.handlers.chatwoot.template_provider.requests.get', return_value=mock_resp),
    ):
        response = client.get('/v1/channels/chatwoot/whatsapp/templates?instance_id=test-instance')

    assert response.status_code == HTTPStatus.OK
    templates = response.json()
    assert isinstance(templates, list)
    assert len(templates) >= 1


def test_list_templates_item_has_required_fields(client):
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = _FAKE_INBOXES_RESPONSE

    with (
        patch('app.routers.channels.fetch_chatwoot_config', return_value=_FAKE_CONFIG),
        patch('app.handlers.chatwoot.template_provider.requests.get', return_value=mock_resp),
    ):
        templates = client.get('/v1/channels/chatwoot/whatsapp/templates?instance_id=test-instance').json()

    tmpl = templates[0]
    for field in ('id', 'name', 'status', 'category', 'language', 'components'):
        assert field in tmpl, f'Expected field "{field}" in template'


def test_list_templates_collects_across_all_inboxes(client):
    second_template = {**_FAKE_TEMPLATE, 'id': '999', 'name': 'outro_template'}
    inboxes = {
        'payload': [
            {'id': 8, 'message_templates': [_FAKE_TEMPLATE]},
            {'id': 9, 'message_templates': [second_template]},
        ]
    }
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = inboxes

    with (
        patch('app.routers.channels.fetch_chatwoot_config', return_value=_FAKE_CONFIG),
        patch('app.handlers.chatwoot.template_provider.requests.get', return_value=mock_resp),
    ):
        templates = client.get('/v1/channels/chatwoot/whatsapp/templates?instance_id=test-instance').json()

    assert len(templates) == len(inboxes['payload'])


def test_list_templates_chatwoot_error_returns_502(client):
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 401

    with (
        patch('app.routers.channels.fetch_chatwoot_config', return_value=_FAKE_CONFIG),
        patch('app.handlers.chatwoot.template_provider.requests.get', return_value=mock_resp),
    ):
        response = client.get('/v1/channels/chatwoot/whatsapp/templates?instance_id=test-instance')

    assert response.status_code == HTTPStatus.BAD_GATEWAY


def test_unknown_channel_templates_returns_404(client):
    with patch('app.routers.channels.fetch_chatwoot_config', return_value=None):
        response = client.get('/v1/channels/chatwoot/telegram/templates?instance_id=any')
    assert response.status_code == HTTPStatus.NOT_FOUND
