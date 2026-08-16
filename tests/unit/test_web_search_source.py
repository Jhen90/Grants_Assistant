# ============================================================
# File: tests/unit/test_web_search_source.py
# Version: 1.2.0
# Created: 2026-07-16
# Description: Tests for WebSearchSource — resolves results via an injected search
#   function, fetches+extracts each page, drops ToS-restricted domains, and still
#   surfaces a lead when a page can't be fetched. No real network or search API.
# ============================================================

from __future__ import annotations

from src.discovery.sources.web_search import WebSearchSource
from src.utils.config import get_settings

_ORG: dict = {"city": "Somerville", "state": "MA", "programs": [{"focus_area": "STEM"}]}

_GOOD_HTML = """
<html><body>
<h1>STEM Youth Grant 2026</h1>
<p>Applications are due September 17, 2026. Awards range $10,000 to $50,000.</p>
</body></html>
"""


class _FakeFetcher:
    """Returns HTML for whitelisted hosts, None (unfetchable) otherwise."""

    def __init__(self, html_by_host: dict):
        self._html_by_host = html_by_host

    def get(self, url, use_cache=True):
        for host, html in self._html_by_host.items():
            if host in url:
                return html
        return None

    def close(self):
        pass


def _search_fn(results):
    def _fn(query, limit):
        return results[:limit]
    return _fn


def test_extracts_from_fetchable_result():
    src = WebSearchSource(
        fetcher=_FakeFetcher({"good.org": _GOOD_HTML}),
        search_fn=_search_fn([("STEM Youth Grant", "http://good.org/grant")]),
    )
    cands = src.search("stem grant", _ORG, limit=5)
    assert len(cands) == 1
    assert cands[0].source_url == "http://good.org/grant"
    assert cands[0].extracted.get("title")  # extractor populated fields
    assert cands[0].raw_text  # page text retained for human review


def test_blocked_domains_are_dropped():
    src = WebSearchSource(
        fetcher=_FakeFetcher({"good.org": _GOOD_HTML}),
        search_fn=_search_fn(
            [
                ("Legit", "http://good.org/grant"),
                ("Aggregator", "https://www.instrumentl.com/grants/x"),
                ("Directory", "https://candid.org/y"),
            ]
        ),
    )
    cands = src.search("q", _ORG, limit=10)
    hosts = [c.source_url for c in cands]
    assert any("good.org" in h for h in hosts)
    assert not any("instrumentl.com" in (h or "") for h in hosts)
    assert not any("candid.org" in (h or "") for h in hosts)


def test_unfetchable_page_still_yields_lead():
    src = WebSearchSource(
        fetcher=_FakeFetcher({}),  # nothing fetchable
        search_fn=_search_fn([("Interesting Lead", "http://unreachable.org/grant")]),
    )
    cands = src.search("q", _ORG)
    assert len(cands) == 1
    assert cands[0].raw_title == "Interesting Lead"
    assert cands[0].extracted == {}  # no extraction possible


def test_disabled_returns_empty(monkeypatch):
    monkeypatch.setattr(get_settings(), "source_web_search_enabled", False, raising=False)
    src = WebSearchSource(
        fetcher=_FakeFetcher({"good.org": _GOOD_HTML}),
        search_fn=_search_fn([("x", "http://good.org/x")]),
    )
    assert src.search("q", _ORG) == []


def test_search_provider_failure_is_isolated():
    def _boom(query, limit):
        raise RuntimeError("provider down")

    src = WebSearchSource(fetcher=_FakeFetcher({}), search_fn=_boom)
    assert src.search("q", _ORG) == []  # must not raise
