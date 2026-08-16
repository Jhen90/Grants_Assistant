# ============================================================
# File: src/discovery/sources/web_search.py
# Version: 1.2.0
# Created: 2026-06-30
# Modified: 2026-06-30
# Description: Web-search discovery. Resolves a query to candidate result URLs,
#   then fetches each page and runs the rules-based extractor on it.
#
#   The search provider is pluggable (inject `search_fn`). The default uses the
#   keyless DuckDuckGo HTML endpoint. Provide your own callable to use a paid
#   search API (SerpAPI/Bing) — it must take (query, limit) -> list[(title,url)].
# ============================================================

from __future__ import annotations

import re
from collections.abc import Callable
from urllib.parse import parse_qs, unquote, urlparse

from src.discovery.base import GrantCandidate, GrantSource
from src.discovery.extractor import extract_fields, html_to_text
from src.discovery.fetcher import PoliteFetcher
from src.utils.config import get_settings
from src.utils.logger import get_logger

log = get_logger(__name__)

SearchFn = Callable[[str, int], list[tuple[str, str]]]  # (query, limit) -> [(title, url)]

# Domains we never auto-fetch — their ToS forbids scraping (use compliant
# connectors instead). Discovered links to these are dropped with a log note.
_BLOCKED_DOMAINS = ("instrumentl.com", "candid.org", "foundationcenter.org")


class WebSearchSource(GrantSource):
    name = "web_search"

    def __init__(
        self,
        fetcher: PoliteFetcher | None = None,
        search_fn: SearchFn | None = None,
    ) -> None:
        self._settings = get_settings()
        self._fetcher = fetcher or PoliteFetcher()
        self._search_fn = search_fn or self._duckduckgo_search

    @property
    def enabled(self) -> bool:
        return self._settings.source_web_search_enabled

    def search(self, query: str, org_profile: dict, limit: int = 10) -> list[GrantCandidate]:
        if not self.enabled:
            return []

        try:
            results = self._search_fn(query, limit)
        except Exception as exc:  # noqa: BLE001 — provider failures must not crash a run
            log.warning("Web search provider failed for %r: %s", query, exc)
            return []

        candidates: list[GrantCandidate] = []
        for title, url in results:
            host = urlparse(url).netloc.lower()
            if any(b in host for b in _BLOCKED_DOMAINS):
                log.info("Skipping ToS-restricted domain in web results: %s", host)
                continue
            html = self._fetcher.get(url)
            if not html:
                # Still surface the lead even if the page couldn't be fetched.
                candidates.append(
                    GrantCandidate(source=self.name, source_url=url, raw_title=title)
                )
                continue
            text = html_to_text(html)
            extracted, conf, ev = extract_fields(text, org_profile, title_hint=title)
            extracted.setdefault("source_url", url)
            candidates.append(
                GrantCandidate(
                    source=self.name,
                    source_url=url,
                    raw_title=extracted.get("title", title),
                    extracted=extracted,
                    field_confidence=conf,
                    evidence=ev,
                    raw_text=text[:4000],
                )
            )
        log.info("web_search: %d candidates for %r.", len(candidates), query)
        return candidates

    # ── default keyless provider: DuckDuckGo HTML ──────────────────────────────

    def _duckduckgo_search(self, query: str, limit: int) -> list[tuple[str, str]]:
        url = "https://html.duckduckgo.com/html/"
        html = self._fetcher.get(f"{url}?q={query.replace(' ', '+')}", use_cache=True)
        if not html:
            return []
        results: list[tuple[str, str]] = []
        # DDG result links look like <a class="result__a" href="...uddg=<encoded>">
        for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html):
            href, title_html = m.group(1), m.group(2)
            real = self._unwrap_ddg(href)
            title = re.sub(r"<[^>]+>", "", title_html).strip()
            if real:
                results.append((title, real))
            if len(results) >= limit:
                break
        return results

    @staticmethod
    def _unwrap_ddg(href: str) -> str | None:
        """DDG wraps targets as /l/?uddg=<url-encoded>. Unwrap to the real URL."""
        if href.startswith("//"):
            href = "https:" + href
        parsed = urlparse(href)
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
        return href if href.startswith("http") else None
