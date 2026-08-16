# ============================================================
# File: src/engine/deduplication.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Detects duplicate grants by URL, exact name+funder, or fuzzy name match
# ============================================================

from __future__ import annotations

from dataclasses import dataclass

from thefuzz import fuzz

from src.utils.config import get_settings
from src.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class DuplicateMatch:
    existing_id: str
    existing_title: str
    match_type: str   # "exact" or "fuzzy"
    match_field: str  # "url", "title+funder", "title"
    similarity: float  # 0.0–1.0


def find_duplicates(
    candidate_title: str,
    candidate_url: str | None,
    candidate_funder_id: str | None,
    existing_grants: list[dict],
) -> list[DuplicateMatch]:
    """
    Compare a candidate grant against existing grants and return any duplicate matches.

    existing_grants is a list of dicts with keys:
        id, title, source_url, funder_id, is_deleted

    Returns a list of DuplicateMatch (empty if no duplicates detected).
    Rules (in priority order):
    1. Same non-empty URL → EXACT match on "url"
    2. Same (normalized) title + same funder_id → EXACT match on "title+funder"
    3. Fuzzy title similarity ≥ threshold + same funder_id → FUZZY match on "title"
    """
    settings = get_settings()
    threshold = settings.dedup_fuzzy_threshold
    matches: list[DuplicateMatch] = []

    candidate_title_norm = _normalize(candidate_title)

    for grant in existing_grants:
        if grant.get("is_deleted"):
            continue

        existing_id = grant["id"]
        existing_title = grant["title"]
        existing_url = grant.get("source_url") or ""
        existing_funder_id = grant.get("funder_id")

        # Rule 1: URL match (only when both URLs are non-empty)
        if candidate_url and existing_url and candidate_url.strip() == existing_url.strip():
            matches.append(
                DuplicateMatch(
                    existing_id=existing_id,
                    existing_title=existing_title,
                    match_type="exact",
                    match_field="url",
                    similarity=1.0,
                )
            )
            continue

        # Rules 2 & 3 only apply when both grants share the same funder
        if candidate_funder_id and existing_funder_id:
            if candidate_funder_id != existing_funder_id:
                continue  # Different funder → not a duplicate

        existing_title_norm = _normalize(existing_title)

        # Rule 2: Exact name + same funder
        if candidate_title_norm == existing_title_norm:
            matches.append(
                DuplicateMatch(
                    existing_id=existing_id,
                    existing_title=existing_title,
                    match_type="exact",
                    match_field="title+funder",
                    similarity=1.0,
                )
            )
            continue

        # Rule 3: Fuzzy title match above threshold + same funder
        similarity = fuzz.token_set_ratio(candidate_title_norm, existing_title_norm) / 100.0
        if similarity >= threshold:
            matches.append(
                DuplicateMatch(
                    existing_id=existing_id,
                    existing_title=existing_title,
                    match_type="fuzzy",
                    match_field="title",
                    similarity=similarity,
                )
            )

    return matches


def _normalize(text: str) -> str:
    """Lowercase and strip extra whitespace for comparison."""
    return " ".join(text.lower().split())
