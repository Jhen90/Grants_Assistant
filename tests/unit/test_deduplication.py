# ============================================================
# File: tests/unit/test_deduplication.py
# Version: 1.1.0
# Created: 2026-06-25
# ============================================================

import pytest

from src.engine.deduplication import DuplicateMatch, find_duplicates


_EXISTING: list[dict] = [
    {
        "id": "g1",
        "title": "Youth Workforce Initiative 2026",
        "source_url": "https://foundation.org/rfp/2026",
        "funder_id": "f1",
        "is_deleted": False,
    },
    {
        "id": "g2",
        "title": "Community Arts Program",
        "source_url": None,
        "funder_id": "f2",
        "is_deleted": False,
    },
    {
        "id": "g3",
        "title": "Deleted Grant",
        "source_url": "https://deleted.org/rfp",
        "funder_id": "f1",
        "is_deleted": True,
    },
]


class TestUrlExactMatch:
    def test_url_match_found(self):
        matches = find_duplicates(
            "Some Other Title",
            "https://foundation.org/rfp/2026",
            "f1",
            _EXISTING,
        )
        assert len(matches) >= 1
        assert matches[0].match_field == "url"
        assert matches[0].match_type == "exact"

    def test_url_match_ignores_deleted(self):
        matches = find_duplicates(
            "Deleted Grant Again",
            "https://deleted.org/rfp",
            "f1",
            _EXISTING,
        )
        assert all(m.existing_id != "g3" for m in matches)

    def test_no_url_match_when_different(self):
        matches = find_duplicates(
            "New Grant",
            "https://brand-new-funder.org/rfp/xyz",
            "f1",
            _EXISTING,
        )
        url_matches = [m for m in matches if m.match_field == "url"]
        assert len(url_matches) == 0


class TestTitleExactMatch:
    def test_exact_title_same_funder_matches(self):
        matches = find_duplicates(
            "Youth Workforce Initiative 2026",
            None,
            "f1",
            _EXISTING,
        )
        assert len(matches) >= 1

    def test_exact_title_different_funder_no_match(self):
        matches = find_duplicates(
            "Youth Workforce Initiative 2026",
            None,
            "f99",  # different funder
            _EXISTING,
        )
        title_matches = [m for m in matches if m.match_field == "title+funder"]
        assert len(title_matches) == 0


class TestFuzzyMatch:
    def test_fuzzy_match_with_similar_title(self):
        matches = find_duplicates(
            "Youth Workforce Initiative 2026 (Updated)",
            None,
            "f1",
            _EXISTING,
        )
        fuzzy_matches = [m for m in matches if m.match_type == "fuzzy"]
        assert len(fuzzy_matches) >= 1

    def test_very_different_title_no_fuzzy(self):
        matches = find_duplicates(
            "Senior Housing Support Program",
            None,
            "f1",
            _EXISTING,
        )
        fuzzy_matches = [m for m in matches if m.match_type == "fuzzy"]
        assert len(fuzzy_matches) == 0

    def test_no_false_positive_different_funder(self):
        matches = find_duplicates(
            "Youth Workforce Initiative 2026",
            None,
            "f99",
            _EXISTING,
        )
        fuzzy_matches = [m for m in matches if m.match_type == "fuzzy"]
        assert len(fuzzy_matches) == 0


class TestNoCandidates:
    def test_empty_existing_list_returns_empty(self):
        matches = find_duplicates("Unique Title", "http://unique.org", "f1", [])
        assert matches == []
