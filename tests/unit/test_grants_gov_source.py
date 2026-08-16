# ============================================================
# File: tests/unit/test_grants_gov_source.py
# Version: 1.2.0
# Created: 2026-07-16
# Description: Tests for GrantsGovSource — maps grants.gov Search2 JSON into
#   GrantCandidates. Disabled-safe and tolerant of malformed payloads. No network.
# ============================================================

from __future__ import annotations

from datetime import date

from src.discovery.sources.grants_gov import GrantsGovSource
from src.utils.config import get_settings

_ORG: dict = {"city": "Boston", "state": "MA"}


class _FakeFetcher:
    def __init__(self, payload):
        self._payload = payload
        self.posts: list = []

    def post_json(self, url, payload):
        self.posts.append((url, payload))
        return self._payload

    def close(self):
        pass


_SAMPLE = {
    "data": {
        "oppHits": [
            {
                "id": "355123",
                "title": "Youth STEM Education Program",
                "agencyName": "Department of Education",
                "closeDate": "09/30/2026",
            }
        ]
    }
}


def test_maps_hits_to_candidates():
    src = GrantsGovSource(fetcher=_FakeFetcher(_SAMPLE))
    cands = src.search("youth stem", _ORG, limit=5)
    assert len(cands) == 1
    c = cands[0]
    assert c.raw_title == "Youth STEM Education Program"
    assert c.extracted["funder_name"] == "Department of Education"
    assert c.extracted["deadline"] == date(2026, 9, 30)
    assert "355123" in (c.source_url or "")
    assert c.source == "grants.gov"


def test_disabled_returns_empty(monkeypatch):
    monkeypatch.setattr(get_settings(), "source_grants_gov_enabled", False, raising=False)
    src = GrantsGovSource(fetcher=_FakeFetcher(_SAMPLE))
    assert src.search("anything", _ORG) == []


def test_malformed_payload_returns_empty():
    assert GrantsGovSource(fetcher=_FakeFetcher(None)).search("x", _ORG) == []
    assert GrantsGovSource(fetcher=_FakeFetcher({"data": {}})).search("x", _ORG) == []


def test_missing_close_date_still_maps():
    payload = {"data": {"oppHits": [{"id": "1", "title": "No Deadline Grant", "agencyName": "X"}]}}
    cands = GrantsGovSource(fetcher=_FakeFetcher(payload)).search("x", _ORG)
    assert len(cands) == 1
    assert "deadline" not in cands[0].extracted
