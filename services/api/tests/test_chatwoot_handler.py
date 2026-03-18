# tests/test_chatwoot_handler.py
import json
from unittest.mock import MagicMock, patch

import pytest
from pocketbase.errors import ClientResponseError

from app.handlers.chatwoot.handler import CampaignCtx, ChatwootHandler
from app.handlers.chatwoot.schemas import ChatwootTemplateConfig
from app.handlers.resolver import DefaultVariableResolver
from app.schemas import MessengerCampaignMeta, MessengerPayload, MessengerRecipient

# --- constants for call counts ---
CHATWOOT_CALLS_NEW_CONTACT = 3  # contact_create + conversation + message
CHATWOOT_CALLS_EXIST_CONTACT = 2  # conversation + message (contact found in search)

# --------------------------------------------------------------------------- #
# Shared test data
# --------------------------------------------------------------------------- #

TEMPLATE_BODY = json.dumps({
    'template_name': 'cobranca_v2',
    'language': 'pt_BR',
    'category': 'UTILITY',
    'params': {
        'body': {
            '1': 'lead.name:amigo',
            '2': 'instancia.razao_social:Empresa',
        },
        'buttons': [],
    },
})

CHATWOOT_CONFIG = {
    'url': 'https://chatwoot.example.com',
    'api_token': 'test_token',
    'account_id': 5,
    'inbox_id': 10,
    'phone_attrib': 'phone',
}

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture
def handler():
    return ChatwootHandler(resolver=DefaultVariableResolver())


@pytest.fixture
def template():
    return ChatwootTemplateConfig.model_validate_json(TEMPLATE_BODY)


@pytest.fixture
def recipient():
    return MessengerRecipient(
        uuid='r-001',
        email='joao@example.com',
        name='João',
        attribs={'phone': '+5511999999999'},
        status='enabled',
    )


@pytest.fixture
def payload(recipient):
    return MessengerPayload(
        subject='Sua fatura venceu',
        body=TEMPLATE_BODY,
        content_type='plain',
        campaign=MessengerCampaignMeta(
            uuid='camp-001',
            name='Cobrança Nov',
            tags=['cobranca', 'instance:mxf'],
        ),
        recipients=[recipient],
    )


@pytest.fixture
def ctx(template, payload):
    return CampaignCtx(
        config=CHATWOOT_CONFIG,
        template=template,
        payload=payload,
        instancia={'razao_social': 'Empresa XYZ'},
    )


@pytest.fixture
def mock_pb():
    pb = MagicMock()
    config_record = MagicMock()
    config_record.config = CHATWOOT_CONFIG
    pb.client.collection.return_value.get_first_list_item.return_value = config_record
    return pb


def _make_http_session(contact_id=42, conversation_id=99, contact_exists=False):
    """Return a mock requests.Session configured for a successful Chatwoot flow."""
    session = MagicMock()

    search_resp = MagicMock(ok=True)
    search_resp.json.return_value = {'payload': [{'id': contact_id}] if contact_exists else []}
    session.get.return_value = search_resp

    create_contact = MagicMock(ok=True)
    create_contact.json.return_value = {'id': contact_id}
    create_conv = MagicMock(ok=True)
    create_conv.json.return_value = {'id': conversation_id}
    send_msg = MagicMock(ok=True)
    session.post.side_effect = [create_contact, create_conv, send_msg]

    return session


# --------------------------------------------------------------------------- #
# _extract_instance_id
# --------------------------------------------------------------------------- #


def test_extract_instance_id_present(handler):
    assert handler._extract_instance_id(['cobranca', 'instance:mxf']) == 'mxf'


def test_extract_instance_id_absent(handler):
    assert handler._extract_instance_id(['cobranca', 'novembro']) is None


def test_extract_instance_id_none_tags(handler):
    assert handler._extract_instance_id(None) is None


# --------------------------------------------------------------------------- #
# _process_one — happy path
# --------------------------------------------------------------------------- #


def test_process_one_success(handler, recipient, ctx):
    session = _make_http_session(contact_id=42, conversation_id=99)

    result = handler._process_one(recipient, ctx, session)

    assert result is True
    session.get.assert_called_once()
    assert session.post.call_count == CHATWOOT_CALLS_NEW_CONTACT


def test_process_one_uses_existing_contact(handler, recipient, ctx):
    session = _make_http_session(contact_id=42, conversation_id=99, contact_exists=True)

    result = handler._process_one(recipient, ctx, session)

    assert result is True
    assert session.post.call_count == CHATWOOT_CALLS_EXIST_CONTACT


# --------------------------------------------------------------------------- #
# _process_one — skip conditions
# --------------------------------------------------------------------------- #


def test_process_one_skips_when_required_field_missing(handler, payload):
    body = json.dumps({
        'template_name': 't',
        'language': 'pt_BR',
        'category': 'UTILITY',
        'params': {'body': {'1': 'lead.attribs.cpf'}, 'buttons': []},  # required, no default
    })
    local_template = ChatwootTemplateConfig.model_validate_json(body)
    recipient = MessengerRecipient(uuid='r-002', email='a@b.com', name='X', attribs={'phone': '+55'}, status='enabled')
    local_ctx = CampaignCtx(config=CHATWOOT_CONFIG, template=local_template, payload=payload, instancia={})
    session = MagicMock()

    result = handler._process_one(recipient, local_ctx, session)

    assert result is False
    session.get.assert_not_called()
    session.post.assert_not_called()


def test_process_one_skips_when_phone_missing(handler, ctx, payload):
    recipient = MessengerRecipient(uuid='r-003', email='a@b.com', name='X', attribs={}, status='enabled')
    session = MagicMock()

    result = handler._process_one(recipient, ctx, session)

    assert result is False
    session.get.assert_not_called()


def test_process_one_skips_when_contact_create_fails(handler, recipient, ctx):
    session = MagicMock()
    session.get.return_value = MagicMock(ok=True, json=lambda: {'payload': []})
    session.post.return_value = MagicMock(ok=False)

    result = handler._process_one(recipient, ctx, session)

    assert result is False
    assert session.post.call_count == 1  # only contact create attempted


def test_process_one_skips_when_conversation_fails(handler, recipient, ctx):
    session = MagicMock()
    session.get.return_value = MagicMock(ok=True, json=lambda: {'payload': []})
    ok_contact = MagicMock(ok=True, json=lambda: {'id': 42})
    fail_conv = MagicMock(ok=False)
    session.post.side_effect = [ok_contact, fail_conv]

    result = handler._process_one(recipient, ctx, session)

    assert result is False
    assert session.post.call_count == CHATWOOT_CALLS_EXIST_CONTACT


# --------------------------------------------------------------------------- #
# _process_all — batch flow
# --------------------------------------------------------------------------- #


def test_process_all_sends_to_chatwoot(handler, payload, mock_pb):
    session = _make_http_session(contact_id=1, conversation_id=2)

    with (
        patch('app.handlers.chatwoot.handler.get_pocketbase_session', return_value=mock_pb),
        patch('app.handlers.chatwoot.handler.requests.Session', return_value=session),
    ):
        handler._process_all(payload)

    assert session.post.call_count == CHATWOOT_CALLS_NEW_CONTACT


def test_process_all_invalid_body_skips_all(handler, mock_pb):
    bad_payload = MessengerPayload(
        subject='S',
        body='not valid json',
        content_type='plain',
        campaign=MessengerCampaignMeta(uuid='c', name='C', tags=['instance:mxf']),
        recipients=[MessengerRecipient(uuid='r', email='a@b.com', name='X', attribs={}, status='enabled')],
    )

    with (
        patch('app.handlers.chatwoot.handler.get_pocketbase_session', return_value=mock_pb),
        patch('app.handlers.chatwoot.handler.requests.Session') as mock_session_cls,
    ):
        handler._process_all(bad_payload)

    mock_session_cls.return_value.post.assert_not_called()


def test_process_all_missing_instance_tag_skips_all(handler, mock_pb):
    payload_no_tag = MessengerPayload(
        subject='S',
        body=TEMPLATE_BODY,
        content_type='plain',
        campaign=MessengerCampaignMeta(uuid='c', name='C', tags=['cobranca']),
        recipients=[MessengerRecipient(uuid='r', email='a@b.com', name='X', attribs={}, status='enabled')],
    )

    with (
        patch('app.handlers.chatwoot.handler.get_pocketbase_session', return_value=mock_pb),
        patch('app.handlers.chatwoot.handler.requests.Session') as mock_session_cls,
    ):
        handler._process_all(payload_no_tag)

    mock_session_cls.return_value.post.assert_not_called()


def test_process_all_missing_config_skips_all(handler, payload):
    pb = MagicMock()
    pb.client.collection.return_value.get_first_list_item.side_effect = ClientResponseError()

    with (
        patch('app.handlers.chatwoot.handler.get_pocketbase_session', return_value=pb),
        patch('app.handlers.chatwoot.handler.requests.Session') as mock_session_cls,
    ):
        handler._process_all(payload)

    mock_session_cls.return_value.post.assert_not_called()


def test_process_all_one_failure_does_not_abort_others(handler, mock_pb):
    """RNF-02: a failed recipient must not prevent processing of remaining recipients."""
    r_ok = MessengerRecipient(uuid='r-ok', email='ok@x.com', name='OK', attribs={'phone': '+5511111111111'}, status='enabled')
    r_no_phone = MessengerRecipient(uuid='r-skip', email='skip@x.com', name='Skip', attribs={}, status='enabled')
    multi_payload = MessengerPayload(
        subject='S',
        body=TEMPLATE_BODY,
        content_type='plain',
        campaign=MessengerCampaignMeta(uuid='c', name='C', tags=['instance:mxf']),
        recipients=[r_no_phone, r_ok],
    )

    session = _make_http_session(contact_id=1, conversation_id=2)

    with (
        patch('app.handlers.chatwoot.handler.get_pocketbase_session', return_value=mock_pb),
        patch('app.handlers.chatwoot.handler.requests.Session', return_value=session),
    ):
        handler._process_all(multi_payload)

    # r_ok: contact_create + conversation + message; r_no_phone: no calls
    assert session.post.call_count == CHATWOOT_CALLS_NEW_CONTACT


# --------------------------------------------------------------------------- #
# send() — background thread
# --------------------------------------------------------------------------- #


def test_send_starts_background_thread(handler, payload):
    with patch('app.handlers.chatwoot.handler.Thread') as mock_thread:
        handler.send(payload)
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
