# ============================================================
# File: tests/unit/test_weekly_grant_email.py
# Version: 1.0.0
# Created: 2026-08-17
# Description: Tests for the weekly grant email body builder — renders title,
#   agency, deadline and apply link; escapes untrusted scraped text; and still
#   produces a real message when the scan finds nothing.
# ============================================================

from __future__ import annotations

from datetime import date

from scripts.send_weekly_grant_email import (
    build_email_bodies,
    build_subject,
    parse_recipients,
)

_DAY = date(2026, 8, 17)


def _item(**overrides) -> dict:
    base = {
        "title": "Youth STEM Innovation Grant",
        "funder": "National Science Foundation",
        "amount": "$10,000–$50,000",
        "deadline": "2026-10-01",
        "urgency": "GREEN",
        "eligibility": "✅ Yes",
        "fit": "8.5",
        "why_fits": "Matches youth development focus.",
        "url": "https://nsf.gov/grants/youth-stem",
    }
    base.update(overrides)
    return base


# ── recipients ─────────────────────────────────────────────────────────────────


def test_parse_recipients_splits_and_strips():
    assert parse_recipients("a@x.com, b@y.com") == ["a@x.com", "b@y.com"]


def test_parse_recipients_handles_empty():
    assert parse_recipients("") == []
    assert parse_recipients("  ,  ") == []


# ── the four required fields ───────────────────────────────────────────────────


def test_body_contains_title_agency_deadline_and_link():
    html, text = build_email_bodies([_item()], today=_DAY)

    for body in (html, text):
        assert "Youth STEM Innovation Grant" in body
        assert "National Science Foundation" in body
        assert "2026-10-01" in body
        assert "https://nsf.gov/grants/youth-stem" in body


def test_html_link_is_clickable():
    html, _ = build_email_bodies([_item()], today=_DAY)
    assert '<a href="https://nsf.gov/grants/youth-stem">' in html


def test_missing_link_does_not_produce_broken_anchor():
    html, text = build_email_bodies([_item(url="(no link)")], today=_DAY)
    assert "No link available" in html
    assert 'href="(no link)"' not in html
    assert "(no link)" in text


# ── untrusted scraped text ─────────────────────────────────────────────────────


def test_scraped_text_is_html_escaped():
    """Titles come from scraped pages — they must not inject markup."""
    html, _ = build_email_bodies(
        [_item(title="Grant <script>alert(1)</script> & More")], today=_DAY
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&amp; More" in html


def test_quotes_in_url_cannot_break_out_of_the_attribute():
    html, _ = build_email_bodies(
        [_item(url='https://x.com/a"onmouseover="evil()')], today=_DAY
    )
    assert 'onmouseover="evil()"' not in html
    assert "&quot;" in html


# ── ordering and volume ────────────────────────────────────────────────────────


def test_items_render_in_the_order_given():
    items = [_item(title="First Grant"), _item(title="Second Grant")]
    html, text = build_email_bodies(items, today=_DAY)
    assert text.index("First Grant") < text.index("Second Grant")
    assert html.index("First Grant") < html.index("Second Grant")


# ── empty week ─────────────────────────────────────────────────────────────────


def test_empty_list_still_sends_a_meaningful_message():
    """Silence must not be ambiguous between 'no grants' and 'job broke'."""
    html, text = build_email_bodies([], today=_DAY)
    assert "No new grants were found" in text
    assert "No new grants were found" in html
    assert "not an error" in text


def test_subject_reflects_count():
    assert "1 grant" in build_subject([_item()], today=_DAY)
    assert "2 grants" in build_subject([_item(), _item()], today=_DAY)
    assert "no new grants found" in build_subject([], today=_DAY)
    assert "2026-08-17" in build_subject([_item()], today=_DAY)
