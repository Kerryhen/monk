# tests/test_channels.py
from http import HTTPStatus


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


def test_list_templates_returns_non_empty_list(client):
    response = client.get('/v1/channels/chatwoot/whatsapp/templates')
    assert response.status_code == HTTPStatus.OK
    templates = response.json()
    assert isinstance(templates, list)
    assert len(templates) >= 1


def test_list_templates_item_has_required_fields(client):
    templates = client.get('/v1/channels/chatwoot/whatsapp/templates').json()
    tmpl = templates[0]
    assert 'template_name' in tmpl
    assert 'params' in tmpl
    assert 'body' in tmpl['params']
    assert 'buttons' in tmpl['params']


def test_unknown_handler_schemas_returns_404(client):
    response = client.get('/v1/channels/unknown/whatsapp/schemas')
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_unknown_channel_templates_returns_404(client):
    response = client.get('/v1/channels/chatwoot/telegram/templates')
    assert response.status_code == HTTPStatus.NOT_FOUND
