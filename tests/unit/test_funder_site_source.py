# ============================================================
# File: tests/unit/test_funder_site_source.py
# Version: 1.2.0
# Created: 2026-07-16
# Description: Tests for FunderSiteSource — targeted fetch+extract of known funder
#   pages, registry custom-parser overrides, subpath probing, and de-duplication.
#   No real network.
# ============================================================

from __future__ import annotations

from src.discovery.sources.funder_site import FunderSiteSource, _GRANT_SUBPATHS
from src.utils.config import get_settings

_ORG: dict = {"city": "Somerville", "state": "MA", "programs": [{"focus_area": "Youth Development"}]}

_MCC_HTML = """
<html><body>
<h1>YouthReach Grant Program</h1>
<p>Supporting youthreach programs across Massachusetts.</p>
</body></html>
"""

_GENERIC_HTML = """
<html><body><h1>Community Grant Opportunity</h1><p>Apply for funding.</p></body></html>
"""


class _FakeFetcher:
    def __init__(self, html):
        self._html = html
        self.fetched: list[str] = []

    def get(self, url, use_cache=True):
        self.fetched.append(url)
        return self._html

    def close(self):
        pass


def test_registry_custom_parser_overrides_funder():
    src = FunderSiteSource(fetcher=_FakeFetcher(_MCC_HTML))
    cand = src.fetch_url("https://massculturalcouncil.org/programs", _ORG)
    assert cand is not None
    assert cand.extracted["funder_name"] == "Mass Cultural Council"
    # override confidence bumped to >= 0.75
    assert cand.field_confidence.get("funder_name", 0) >= 0.75


def test_unknown_domain_uses_generic_extractor():
    src = FunderSiteSource(fetcher=_FakeFetcher(_GENERIC_HTML))
    cand = src.fetch_url("https://smallfunder.org/grants", _ORG)
    assert cand is not None
    assert cand.extracted.get("title")
    assert cand.source == "funder_site"


def test_sweep_probes_subpaths_off_bare_homepage():
    src = FunderSiteSource(fetcher=_FakeFetcher(_GENERIC_HTML))
    cands = src.sweep_urls(["http://funder.org"], _ORG)
    # base homepage + each grant subpath, all distinct URLs
    assert len(cands) == 1 + len(_GRANT_SUBPATHS)


def test_sweep_dedupes_repeated_urls():
    src = FunderSiteSource(fetcher=_FakeFetcher(_GENERIC_HTML))
    # non-bare paths are not subpath-expanded; duplicates collapse to one
    cands = src.sweep_urls(
        ["http://funder.org/grants", "http://funder.org/grants"], _ORG
    )
    assert len(cands) == 1


def test_disabled_returns_none_and_empty(monkeypatch):
    monkeypatch.setattr(get_settings(), "source_funder_sites_enabled", False, raising=False)
    src = FunderSiteSource(fetcher=_FakeFetcher(_GENERIC_HTML))
    assert src.fetch_url("https://funder.org/grants", _ORG) is None
    assert src.search("q", _ORG) == []  # never a keyword engine
