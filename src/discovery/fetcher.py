# ============================================================
# File: src/discovery/fetcher.py
# Version: 1.2.0
# Created: 2026-06-30
# Modified: 2026-06-30
# Description: Polite HTTP fetcher for the discovery subsystem.
#   - Honors robots.txt (configurable, default ON)
#   - Identifies itself via a descriptive User-Agent
#   - Rate-limits per host
#   - Caches responses to disk to avoid re-hitting sites
# ============================================================

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from src.utils.config import get_settings
from src.utils.logger import get_logger

log = get_logger(__name__)


class FetchBlockedError(Exception):
    """Raised when robots.txt disallows fetching a URL and robots are respected."""


class PoliteFetcher:
    """
    A courteous HTTP client. Reuse one instance across a discovery run so the
    per-host rate limiter and robots cache stay warm.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._last_hit: dict[str, float] = {}          # host -> monotonic timestamp
        self._robots: dict[str, RobotFileParser | None] = {}
        self._cache_dir = Path(self._settings.discovery_cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._client = httpx.Client(
            headers={"User-Agent": self._settings.discovery_user_agent},
            timeout=self._settings.discovery_fetch_timeout,
            follow_redirects=True,
        )

    # ── public API ───────────────────────────────────────────────────────────

    def get(self, url: str, use_cache: bool = True) -> str | None:
        """
        Fetch a URL as text. Returns None on error or robots-disallow (logged).
        Cached responses skip the network and the rate limiter.
        """
        if use_cache:
            cached = self._read_cache(url)
            if cached is not None:
                log.debug("Discovery cache hit: %s", url)
                return cached

        if self._settings.discovery_respect_robots and not self._robots_allow(url):
            log.warning("robots.txt disallows fetching %s — skipping.", url)
            return None

        self._rate_limit(url)

        try:
            resp = self._client.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            log.warning("Fetch failed for %s: %s", url, exc)
            return None

        text = resp.text
        self._write_cache(url, text)
        return text

    def get_json(self, url: str, params: dict | None = None) -> dict | list | None:
        """GET a JSON API endpoint (no robots check — these are public APIs)."""
        self._rate_limit(url)
        try:
            resp = self._client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("JSON fetch failed for %s: %s", url, exc)
            return None

    def post_json(self, url: str, payload: dict) -> dict | list | None:
        """POST JSON to an API endpoint (grants.gov Search2 uses POST)."""
        self._rate_limit(url)
        try:
            resp = self._client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("JSON POST failed for %s: %s", url, exc)
            return None

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> PoliteFetcher:
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    # ── internals ──────────────────────────────────────────────────────────────

    def _rate_limit(self, url: str) -> None:
        host = urlparse(url).netloc
        interval = self._settings.discovery_min_request_interval
        last = self._last_hit.get(host)
        if last is not None:
            elapsed = time.monotonic() - last
            if elapsed < interval:
                time.sleep(interval - elapsed)
        self._last_hit[host] = time.monotonic()

    def _robots_allow(self, url: str) -> bool:
        parsed = urlparse(url)
        host = parsed.netloc
        if host not in self._robots:
            rp = RobotFileParser()
            robots_url = f"{parsed.scheme}://{host}/robots.txt"
            try:
                rp.set_url(robots_url)
                rp.read()
                self._robots[host] = rp
            except Exception as exc:  # noqa: BLE001 — any failure ⇒ be permissive but log
                log.debug("Could not read robots.txt for %s: %s", host, exc)
                self._robots[host] = None
        rp = self._robots[host]
        if rp is None:
            return True  # no robots.txt available ⇒ allowed
        return rp.can_fetch(self._settings.discovery_user_agent, url)

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
        return self._cache_dir / f"{digest}.html"

    def _read_cache(self, url: str) -> str | None:
        path = self._cache_path(url)
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except OSError:
                return None
        return None

    def _write_cache(self, url: str, text: str) -> None:
        try:
            self._cache_path(url).write_text(text, encoding="utf-8")
        except OSError as exc:
            log.debug("Could not cache %s: %s", url, exc)
