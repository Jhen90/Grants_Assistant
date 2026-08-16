# ============================================================
# File: tests/unit/test_query_expander.py
# Version: 1.2.0
# Created: 2026-06-30
# Description: Tests for org-profile-driven search query expansion.
# ============================================================

from __future__ import annotations

from src.discovery.query_expander import expand_queries

_PROFILE = {
    "city": "Somerville",
    "state": "MA",
    "programs": [
        {"focus_area": "Youth Development"},
        {"focus_area": "STEM/STEAM"},
        {"focus_area": "Climate Education"},
    ],
    "eligibility": {"target_population": "youth ages 13-18"},
}


class TestExpandQueries:
    def test_deterministic(self):
        assert expand_queries(_PROFILE, year=2026) == expand_queries(_PROFILE, year=2026)

    def test_respects_cap(self):
        out = expand_queries(_PROFILE, year=2026, max_queries=10)
        assert len(out) <= 10

    def test_no_duplicates(self):
        out = expand_queries(_PROFILE, year=2026, max_queries=100)
        assert len(out) == len(set(q.lower() for q in out))

    def test_includes_focus_and_geo(self):
        out = " || ".join(expand_queries(_PROFILE, year=2026, max_queries=100)).lower()
        assert "youth development" in out
        assert "somerville" in out
        assert "2026" in out

    def test_includes_broader_scopes(self):
        out = " || ".join(expand_queries(_PROFILE, year=2026, max_queries=100)).lower()
        assert "new england" in out
        assert "national" in out

    def test_empty_programs_uses_defaults(self):
        out = expand_queries({"city": "Boston", "state": "MA", "programs": []}, year=2026)
        assert len(out) > 0
        joined = " ".join(out).lower()
        assert "youth development" in joined or "stem" in joined
