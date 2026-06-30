# ============================================================
# File: tests/unit/test_extractor.py
# Version: 1.2.0
# Created: 2026-06-30
# Description: Tests for the deterministic, rules-based discovery extractor.
# ============================================================

from __future__ import annotations

from datetime import date

import pytest

from src.discovery.extractor import extract_fields, html_to_text

_ORG = {
    "city": "Somerville",
    "state": "MA",
    "programs": [
        {"focus_area": "Youth Development"},
        {"focus_area": "STEM/STEAM"},
        {"focus_area": "Climate Education"},
    ],
}


class TestDeterminism:
    def test_same_input_same_output(self):
        text = "Applications are due September 17, 2026. Awards range $10,000 to $100,000."
        r1 = extract_fields(text, _ORG, title_hint="Test Grant")
        r2 = extract_fields(text, _ORG, title_hint="Test Grant")
        assert r1 == r2


class TestDeadline:
    def test_textual_deadline_with_cue(self):
        text = "The application deadline is September 17, 2026 at 5:00 PM."
        extracted, conf, _ = extract_fields(text, _ORG, title_hint="X")
        assert extracted["deadline"] == date(2026, 9, 17)
        assert conf["deadline"] >= 0.7

    def test_numeric_deadline(self):
        text = "Submit by 04/02/2026 to be considered."
        extracted, _, _ = extract_fields(text, _ORG, title_hint="X")
        assert extracted["deadline"] == date(2026, 4, 2)

    def test_cue_date_preferred_over_noncue(self):
        text = (
            "This program launched January 1, 2020. "
            "Applications are due April 2, 2026."
        )
        extracted, _, _ = extract_fields(text, _ORG, title_hint="X")
        assert extracted["deadline"] == date(2026, 4, 2)

    def test_no_date_means_no_deadline(self):
        text = "This is a grant with no specific dates mentioned here."
        extracted, _, _ = extract_fields(text, _ORG, title_hint="X")
        assert "deadline" not in extracted


class TestAmounts:
    def test_range_extracted(self):
        text = "Annual installments ranging from $10,000 to $100,000."
        extracted, _, _ = extract_fields(text, _ORG, title_hint="X")
        assert extracted["amount_min"] == 10000.0
        assert extracted["amount_max"] == 100000.0

    def test_million_suffix(self):
        text = "A total of $1.5 million will be awarded."
        extracted, _, _ = extract_fields(text, _ORG, title_hint="X")
        assert extracted["amount_max"] == 1_500_000.0

    def test_noise_amounts_ignored(self):
        text = "Call $5 for details."  # below the $500 floor
        extracted, _, _ = extract_fields(text, _ORG, title_hint="X")
        assert "amount_max" not in extracted


class TestEligibility:
    def test_501c3_required_detected(self):
        text = "Applicants must be a registered 501(c)(3) public charity."
        extracted, _, _ = extract_fields(text, _ORG, title_hint="X")
        assert extracted["eligibility_501c3_required"] is True

    def test_fiscal_sponsorship_lowers_501c3_requirement(self):
        text = (
            "Applicants should hold 501(c)(3) status, but organizations with a "
            "fiscal sponsor may also apply."
        )
        extracted, _, _ = extract_fields(text, _ORG, title_hint="X")
        assert extracted["eligibility_501c3_required"] is False
        assert extracted["fiscal_sponsorship_allowed"] is True


class TestGeography:
    def test_city_match(self):
        text = "This grant supports organizations in Somerville and surrounding areas."
        extracted, conf, _ = extract_fields(text, _ORG, title_hint="X")
        assert extracted["target_geography"] == "Somerville"
        assert conf["target_geography"] >= 0.7

    def test_national_fallback(self):
        text = "This is a nationwide funding opportunity open to all states."
        extracted, _, _ = extract_fields(text, _ORG, title_hint="X")
        assert extracted["target_geography"] == "National"


class TestFocusAreas:
    def test_matches_org_vocab(self):
        text = "Funding for youth development and STEM education programs."
        extracted, _, _ = extract_fields(text, _ORG, title_hint="X")
        assert "youth development" in extracted["focus_areas"]
        assert "stem" in extracted["focus_areas"]


class TestHtmlToText:
    def test_strips_scripts_and_tags(self):
        html = "<html><body><script>bad()</script><h1>Grant Title</h1><p>Body text.</p></body></html>"
        text = html_to_text(html)
        assert "Grant Title" in text
        assert "Body text." in text
        assert "bad()" not in text
