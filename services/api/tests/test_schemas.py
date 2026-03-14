"""Unit tests for Pydantic schema field constraints and defaults.

No HTTP calls, no Doppler — pure Pydantic validation.
"""

import pytest
from pydantic import ValidationError

from app.schemas import LM_CreateCampaignSchema, LM_CreateListSchema

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CAMPAIGN_REQUIRED = {
    'name': 'Test Campaign',
    'subject': 'Hello',
    'lists': [1],
    'content_type': 'richtext',
    'body': '<p>Hi</p>',
}


# ===========================================================================
# LM_CreateListSchema
# ===========================================================================


def test_list_type_defaults_to_private():
    schema = LM_CreateListSchema(name='My List', optin='single')
    assert schema.type == 'private'


def test_list_type_explicit_public():
    schema = LM_CreateListSchema(name='My List', optin='single', type='public')
    assert schema.type == 'public'


def test_list_type_invalid_value():
    with pytest.raises(ValidationError):
        LM_CreateListSchema(name='My List', optin='single', type='protected')


def test_list_optin_required():
    with pytest.raises(ValidationError):
        LM_CreateListSchema(name='My List', type='private')


def test_list_optin_single():
    schema = LM_CreateListSchema(name='My List', type='private', optin='single')
    assert schema.optin == 'single'


def test_list_optin_double():
    schema = LM_CreateListSchema(name='My List', type='private', optin='double')
    assert schema.optin == 'double'


# ===========================================================================
# LM_CreateCampaignSchema
# ===========================================================================


def test_campaign_type_defaults_to_regular():
    schema = LM_CreateCampaignSchema(**CAMPAIGN_REQUIRED)
    assert schema.type == 'regular'


def test_campaign_type_explicit_optin():
    schema = LM_CreateCampaignSchema(**{**CAMPAIGN_REQUIRED, 'type': 'optin'})
    assert schema.type == 'optin'


def test_campaign_type_invalid_value():
    with pytest.raises(ValidationError):
        LM_CreateCampaignSchema(**{**CAMPAIGN_REQUIRED, 'type': 'bulk'})


def test_campaign_content_type_required():
    payload = {k: v for k, v in CAMPAIGN_REQUIRED.items() if k != 'content_type'}
    with pytest.raises(ValidationError):
        LM_CreateCampaignSchema(**payload)


@pytest.mark.parametrize('ct', ['richtext', 'html', 'markdown', 'plain'])
def test_campaign_content_type_all_valid_values(ct):
    schema = LM_CreateCampaignSchema(**{**CAMPAIGN_REQUIRED, 'content_type': ct})
    assert schema.content_type == ct


def test_campaign_messenger_defaults_to_email():
    schema = LM_CreateCampaignSchema(**CAMPAIGN_REQUIRED)
    assert schema.messenger == 'email'


@pytest.mark.parametrize('field', ['name', 'subject', 'lists', 'body'])
def test_campaign_required_fields(field):
    payload = {k: v for k, v in CAMPAIGN_REQUIRED.items() if k != field}
    with pytest.raises(ValidationError):
        LM_CreateCampaignSchema(**payload)


def test_campaign_lists_must_be_nonempty():
    with pytest.raises(ValidationError):
        LM_CreateCampaignSchema(**{**CAMPAIGN_REQUIRED, 'lists': []})
