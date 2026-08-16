# ============================================================
# File: src/discovery/sources/__init__.py
# Version: 1.2.0
# Created: 2026-06-30
# Modified: 2026-06-30
# Description: Discovery source connectors registry.
# ============================================================

from src.discovery.sources.aggregator import CandidApiSource, InstrumentlCsvImporter
from src.discovery.sources.funder_site import FunderSiteSource
from src.discovery.sources.grants_gov import GrantsGovSource
from src.discovery.sources.web_search import WebSearchSource

__all__ = [
    "GrantsGovSource",
    "WebSearchSource",
    "FunderSiteSource",
    "CandidApiSource",
    "InstrumentlCsvImporter",
]
