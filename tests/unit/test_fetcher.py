# ============================================================
# File: tests/unit/test_fetcher.py
# Version: 1.2.0
# Created: 2026-07-16
# Description: Tests for PoliteFetcher — robots.txt honoring, disk cache, per-host
#   rate limiting, and JSON GET/POST. No test performs real network I/O.
# ============================================================

from __future__ import annotations

import httpx
import pytest

import src.discovery.fetcher as fetcher_mod
from src.discovery.fetcher import PoliteFetcher
from src.utils.config import get_settings


class _ExplodingClient:
    """Stand-in httpx client that fails if the network is touched."""

    def get(self, *a, **k):
        raise AssertionError("network should not have been called")

    def post(self, *a, **k):
        raise AssertionError("network should not have been called")

    def close(self):
        pass


class _Resp:
    def __init__(self, json_data=None, text="", raise_error=False):
        self._json = json_data
        self.text = text
        self._raise = raise_error

    def raise_for_status(self):
        if self._raise:
            raise httpx.HTTPError("boom")

    def json(self):
        return self._json


class _StubClient:
    def __init__(self, resp: _Resp):
        self._resp = resp
        self.calls = 0

    def get(self, url, params=None):
        self.calls += 1
        return self._resp

    def post(self, url, json=None):
        self.calls += 1
        return self._resp

    def close(self):
        pass


@pytest.fixture()
def fetcher(tmp_path, monkeypatch):
    # Redirect the disk cache to a tmp dir so tests never touch data/.
    monkeypatch.setattr(get_settings(), "discovery_cache_dir", str(tmp_path), raising=False)
    f = PoliteFetcher()
    yield f
    f.close()


class TestRobots:
    def test_disallow_returns_none_without_network(self, fetcher):
        class _FakeRP:
            def can_fetch(self, ua, url):
                return False

        fetcher._robots["blocked.org"] = _FakeRP()
        fetcher._client = _ExplodingClient()
        assert fetcher.get("http://blocked.org/rfp", use_cache=False) is None


class TestCache:
    def test_cache_hit_skips_network(self, fetcher):
        url = "http://funder.org/grants"
        fetcher._write_cache(url, "CACHED BODY")
        fetcher._client = _ExplodingClient()  # must not be used
        assert fetcher.get(url) == "CACHED BODY"


class TestRateLimit:
    def test_sleeps_when_within_interval(self, fetcher, monkeypatch):
        interval = get_settings().discovery_min_request_interval
        times = iter([100.0, 100.5, 101.0])
        sleeps: list[float] = []
        monkeypatch.setattr(fetcher_mod.time, "monotonic", lambda: next(times))
        monkeypatch.setattr(fetcher_mod.time, "sleep", lambda s: sleeps.append(s))

        url = "http://host.org/a"
        fetcher._rate_limit(url)  # first hit — no sleep
        fetcher._rate_limit(url)  # second hit 0.5s later — must sleep the remainder
        assert sleeps == [pytest.approx(interval - 0.5)]

    def test_no_sleep_for_first_hit(self, fetcher, monkeypatch):
        sleeps: list[float] = []
        monkeypatch.setattr(fetcher_mod.time, "sleep", lambda s: sleeps.append(s))
        fetcher._rate_limit("http://newhost.org/x")
        assert sleeps == []


class TestJson:
    def test_get_json_success(self, fetcher):
        fetcher._client = _StubClient(_Resp(json_data={"ok": 1}))
        assert fetcher.get_json("http://api.org/x") == {"ok": 1}

    def test_get_json_error_returns_none(self, fetcher):
        fetcher._client = _StubClient(_Resp(raise_error=True))
        assert fetcher.get_json("http://api.org/x") is None

    def test_post_json_success(self, fetcher):
        fetcher._client = _StubClient(_Resp(json_data={"data": {"oppHits": []}}))
        assert fetcher.post_json("http://api.org/search", {"keyword": "x"}) == {
            "data": {"oppHits": []}
        }

    def test_post_json_error_returns_none(self, fetcher):
        fetcher._client = _StubClient(_Resp(raise_error=True))
        assert fetcher.post_json("http://api.org/search", {"k": "v"}) is None
