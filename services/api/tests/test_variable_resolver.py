# tests/test_variable_resolver.py
import pytest

from app.handlers.resolver import DefaultVariableResolver


@pytest.fixture
def resolver():
    return DefaultVariableResolver()


@pytest.fixture
def full_context():
    return {
        'lead': {
            'uuid': 'abc-123',
            'email': 'joao@example.com',
            'name': 'João',
            'status': 'enabled',
            'attribs': {
                'cpf': '111.222.333-44',
                'payment_link': 'https://pay.example.com/abc',
            },
        },
        'campanha': {
            'uuid': 'camp-456',
            'name': 'Cobrança Nov',
            'subject': 'Sua fatura venceu',
            'tags': ['cobranca', 'novembro'],
        },
        'instancia': {
            'razao_social': 'Empresa XYZ Ltda',
            'cnpj': '12.345.678/0001-99',
        },
    }


# --- campo direto presente ---


def test_resolve_lead_direct_field(resolver, full_context):
    ok, value = resolver.resolve('lead.name', full_context)
    assert ok is True
    assert value == 'João'


def test_resolve_campanha_field(resolver, full_context):
    ok, value = resolver.resolve('campanha.subject', full_context)
    assert ok is True
    assert value == 'Sua fatura venceu'


def test_resolve_instancia_field(resolver, full_context):
    ok, value = resolver.resolve('instancia.razao_social', full_context)
    assert ok is True
    assert value == 'Empresa XYZ Ltda'


# --- campo aninhado em attribs ---


def test_resolve_lead_attrib_nested(resolver, full_context):
    ok, value = resolver.resolve('lead.attribs.cpf', full_context)
    assert ok is True
    assert value == '111.222.333-44'


def test_resolve_lead_attrib_payment_link(resolver, full_context):
    ok, value = resolver.resolve('lead.attribs.payment_link', full_context)
    assert ok is True
    assert value == 'https://pay.example.com/abc'


# --- campo ausente com fallback ---


def test_resolve_missing_field_with_default(resolver, full_context):
    full_context['lead']['name'] = None
    ok, value = resolver.resolve('lead.name:amigo', full_context)
    assert ok is True
    assert value == 'amigo'


def test_resolve_missing_attrib_with_default(resolver, full_context):
    ok, value = resolver.resolve('lead.attribs.ausente:valor_padrao', full_context)
    assert ok is True
    assert value == 'valor_padrao'


def test_resolve_empty_string_with_default(resolver, full_context):
    full_context['lead']['name'] = ''
    ok, value = resolver.resolve('lead.name:amigo', full_context)
    assert ok is True
    assert value == 'amigo'


# --- campo obrigatório ausente ---


def test_resolve_required_field_none(resolver, full_context):
    full_context['lead']['name'] = None
    ok, value = resolver.resolve('lead.name', full_context)
    assert ok is False
    assert not value


def test_resolve_required_field_missing_key(resolver, full_context):
    ok, value = resolver.resolve('instancia.razao_social', {'instancia': {}})
    assert ok is False
    assert not value


def test_resolve_required_field_schema_missing(resolver):
    ok, value = resolver.resolve('instancia.razao_social', {})
    assert ok is False
    assert not value


# --- default com URL (PROB-07: split só no primeiro ':') ---


def test_resolve_url_as_default(resolver, full_context):
    ok, value = resolver.resolve('lead.attribs.link:https://example.com/path', full_context)
    assert ok is True
    assert value == 'https://example.com/path'


def test_resolve_url_default_not_split_multiple_colons(resolver):
    context = {'lead': {'attribs': {}}}
    ok, value = resolver.resolve('lead.attribs.link:https://example.com/path?a=1', context)
    assert ok is True
    assert value == 'https://example.com/path?a=1'


def test_resolve_present_field_ignores_default(resolver, full_context):
    ok, value = resolver.resolve('lead.name:fallback', full_context)
    assert ok is True
    assert value == 'João'


# --- conversão para string ---


def test_resolve_numeric_value_returns_string(resolver):
    context = {'instancia': {'code': 42}}
    ok, value = resolver.resolve('instancia.code', context)
    assert ok is True
    assert value == '42'
