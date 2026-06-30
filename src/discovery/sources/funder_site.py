# ============================================================
# File: src/discovery/sources/funder_site.py
# Version: 1.2.0
# Created: 2026-06-30
# Modified: 2026-06-30
# Description: Targeted fetch + extract for KNOWN funder pages we already track.
#   Fetching a funder's own public grant page for your own application research
#   is legitimate. A small registry maps domains to optional custom parsers;
#   unknown domains fall back to the generic rules-based extractor.
# ============================================================

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urlparse

from src.discovery.base import GrantCandidate, GrantSource
from src.discovery.extractor import extract_fields, html_to_text
from src.discovery.fetcher import PoliteFetcher
from src.utils.config import get_settings
from src.utils.logger import get_logger

log = get_logger(__name__)

# A custom parser takes (text, org_profile) and returns field overrides to merge
# on top of the generic extractor output. Use these to encode site-specific
# knowledge (e.g. a funder whose deadline is always in a known sentence).
CustomParser = Callable[[str, dict], dict]


def _mass_cultural_council(text: str, org_profile: dict) -> dict:
    overrides: dict = {"funder_name": "Mass Cultural Council"}
    if "youthreach" in text.lower():
        overrides["focus_areas"] = ["Youth Development", "arts", "STEM"]
        overrides["fiscal_sponsorship_allowed"] = True
    return overrides


def _cummings(text: str, org_profile: dict) -> dict:
    return {"funder_name": "Cummings Foundation"}


# domain substring -> (label, custom parser)
_REGISTRY: dict[str, tuple[str, CustomParser]] = {
    "massculturalcouncil.org": ("Mass Cultural Council", _mass_cultural_council),
    "cummingsfoundation.org": ("Cummings Foundation", _cummings),
}

# Curated public grant portals swept on every full run ("search everywhere").
# These are public funding-listing pages — fetched for the org's own research.
PUBLIC_PORTALS: list[str] = [
    "https://www.grants.gov/search-grants",
    "https://www.mass.gov/topics/grants-funding",
    "https://www.boston.gov/departments/grants",
    "https://www.somervillema.gov/grants",
    "https://www.cummingsfoundation.org/grants/",
    "https://massculturalcouncil.org/programs-at-a-glance/",
    "https://www.barrfoundation.org/grants",
    "https://www.tbf.org/what-we-do/grants",  # The Boston Foundation
]

# Common sub-paths to try when sweeping a funder's homepage for a grants page.
_GRANT_SUBPATHS = ("/grants", "/grant", "/apply", "/funding", "/grant-opportunities", "/rfp")


class FunderSiteSource(GrantSource):
    name = "funder_site"

    def __init__(self, fetcher: PoliteFetcher | None = None) -> None:
        self._settings = get_settings()
        self._fetcher = fetcher or PoliteFetcher()

    @property
    def enabled(self) -> bool:
        return self._settings.source_funder_sites_enabled

    def search(self, query: str, org_profile: dict, limit: int = 25) -> list[GrantCandidate]:
        # Not a keyword search engine — callers fetch specific known URLs.
        return []

    def fetch_url(self, url: str, org_profile: dict) -> GrantCandidate | None:
        """Fetch one known funder page and extract a candidate from it."""
        if not self.enabled:
            return None
        html = self._fetcher.get(url)
        if not html:
            return None

        text = html_to_text(html)
        host = urlparse(url).netloc.lower()
        funder_hint = next(
            (label for dom, (label, _) in _REGISTRY.items() if dom in host), None
        )

        extracted, conf, ev = extract_fields(text, org_profile, funder_hint=funder_hint)
        extracted.setdefault("source_url", url)

        # Apply site-specific overrides if we have a parser for this domain.
        for dom, (_, parser) in _REGISTRY.items():
            if dom in host:
                overrides = parser(text, org_profile)
                extracted.update(overrides)
                for k in overrides:
                    conf[k] = max(conf.get(k, 0.0), 0.75)
                break

        return GrantCandidate(
            source=self.name,
            source_url=url,
            raw_title=extracted.get("title", url),
            raw_funder=extracted.get("funder_name"),
            extracted=extracted,
            field_confidence=conf,
            evidence=ev,
            raw_text=text[:4000],
        )

    def sweep_urls(
        self, urls: list[str], org_profile: dict, try_subpaths: bool = True
    ) -> list[GrantCandidate]:
        """
        Fetch many funder/portal URLs and extract a candidate from each.
        When `try_subpaths` is set, also probes common grant sub-paths
        (/grants, /apply, …) off each homepage. De-dupes by resolved URL.
        """
        seen: set[str] = set()
        candidates: list[GrantCandidate] = []

        for base in urls:
            for candidate_url in self._expand_url(base, try_subpaths):
                if candidate_url in seen:
                    continue
                seen.add(candidate_url)
                cand = self.fetch_url(candidate_url, org_profile)
                if cand and cand.extracted.get("title"):
                    candidates.append(cand)
        log.info("funder_site sweep: %d candidates from %d base URLs.", len(candidates), len(urls))
        return candidates

    @staticmethod
    def _expand_url(base: str, try_subpaths: bool) -> list[str]:
        urls = [base]
        if not try_subpaths:
            return urls
        parsed = urlparse(base)
        # Only probe sub-paths off a bare homepage (no path), to stay polite.
        if parsed.path in ("", "/"):
            root = f"{parsed.scheme}://{parsed.netloc}"
            urls.extend(root + sp for sp in _GRANT_SUBPATHS)
        return urls

    @staticmethod
    def known_domains() -> list[str]:
        return list(_REGISTRY.keys())
