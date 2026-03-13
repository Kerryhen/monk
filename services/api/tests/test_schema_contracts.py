# tests/test_schema_contracts.py
"""
Contract tests: verify our Pydantic schemas can parse every object
currently stored in Listmonk. These catch mismatches between our
schema definitions and what Listmonk actually returns in practice
(e.g. undocumented enum values, nullable fields marked required, etc.).
"""
import pytest

from app.interface import MonkCampaigns, MonkLists
from app.schemas import CampaignSchema, ListSchema


def _fetch_all_campaigns() -> list[dict]:
    response = MonkCampaigns.get({'page': 1, 'per_page': 500})
    response.raise_for_status()
    return response.json()['data']['results'] or []


def _fetch_all_lists() -> list[dict]:
    response = MonkLists.get({'page': 1, 'per_page': 500})
    response.raise_for_status()
    return response.json()['data']['results'] or []


@pytest.mark.parametrize('campaign', _fetch_all_campaigns(), ids=lambda c: f"campaign_{c['id']}")
def test_campaign_schema_parses_listmonk_response(campaign):
    """CampaignSchema must parse every campaign Listmonk returns."""
    CampaignSchema(**campaign)


@pytest.mark.parametrize('lst', _fetch_all_lists(), ids=lambda item: f"list_{item['id']}")
def test_list_schema_parses_listmonk_response(lst):
    """ListSchema must parse every list Listmonk returns."""
    ListSchema(**lst)
