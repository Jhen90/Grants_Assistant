# ============================================================
# File: src/discovery/extractor.py
# Version: 1.2.0
# Created: 2026-06-30
# Modified: 2026-06-30
# Description: Deterministic, rules-based extraction of grant application fields
#   from HTML/plain text. NO AI. Same input always yields the same output.
#   Every value carries a confidence score and the evidence snippet it came
#   from, so a human can verify before the candidate is imported.
# ============================================================

from __future__ import annotations

import re
from datetime import date, datetime

from bs4 import BeautifulSoup

# ── Month lookup for textual dates ───────────────────────────────────────────
_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12, "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

# Words that signal a date is a *deadline* (vs an open date or some other date)
_DEADLINE_CUES = (
    "deadline", "due", "close", "closes", "closing", "submit by", "submitted by",
    "applications due", "loi due", "letters of inquiry", "apply by", "no later than",
)

# "Month DD, YYYY"  e.g. September 17, 2026
_RE_TEXT_DATE = re.compile(
    r"\b("
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    r"aug(?:ust)?|sep(?:t)?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
    r")\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b",
    re.IGNORECASE,
)
# Numeric dates: MM/DD/YYYY or MM-DD-YYYY
_RE_NUM_DATE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b")

# Dollar amounts: $10,000 or $10,000.00 or $1.5 million
_RE_MONEY = re.compile(
    r"\$\s?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)(\s?(?:million|m|k|thousand))?",
    re.IGNORECASE,
)


def html_to_text(html: str) -> str:
    """Strip HTML to readable text, dropping script/style/nav noise."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # Collapse excess whitespace
    lines = [ln.strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def extract_fields(
    text: str,
    org_profile: dict,
    title_hint: str | None = None,
    funder_hint: str | None = None,
) -> tuple[dict, dict, dict]:
    """
    Extract grant fields from page text.

    Returns (extracted, confidence, evidence) where:
      extracted  → dict keyed for GrantService.create_grant()
      confidence → {field: 0.0–1.0}
      evidence   → {field: "snippet the value came from"}
    """
    extracted: dict = {}
    confidence: dict = {}
    evidence: dict = {}

    lower = text.lower()

    # ── Title ────────────────────────────────────────────────────────────────
    if title_hint:
        extracted["title"] = title_hint.strip()
        confidence["title"] = 0.9
    else:
        first_line = next((ln for ln in text.splitlines() if len(ln) > 8), "")[:200]
        extracted["title"] = first_line.strip()
        confidence["title"] = 0.3
    evidence["title"] = extracted["title"]

    if funder_hint:
        extracted["funder_name"] = funder_hint.strip()
        confidence["funder_name"] = 0.8
        evidence["funder_name"] = funder_hint.strip()

    # ── Deadline ───────────────────────────────────────────────────────────────
    deadline, dl_conf, dl_evidence = _extract_deadline(text)
    if deadline is not None:
        extracted["deadline"] = deadline
        confidence["deadline"] = dl_conf
        evidence["deadline"] = dl_evidence

    # ── Amount range ───────────────────────────────────────────────────────────
    amounts, amt_evidence = _extract_amounts(text)
    if amounts:
        extracted["amount_min"] = min(amounts)
        extracted["amount_max"] = max(amounts)
        confidence["amount_min"] = 0.6
        confidence["amount_max"] = 0.6
        evidence["amount_min"] = amt_evidence
        evidence["amount_max"] = amt_evidence

    # ── 501(c)(3) requirement ──────────────────────────────────────────────────
    if re.search(r"501\s?\(?c\)?\s?\(?3\)?", lower) or "tax-exempt" in lower:
        requires = not bool(
            re.search(r"fiscal\s+spons|fiscal\s+agent|fiscally\s+sponsored", lower)
        )
        extracted["eligibility_501c3_required"] = requires
        confidence["eligibility_501c3_required"] = 0.55
        evidence["eligibility_501c3_required"] = _snippet(text, "501")

    # ── Fiscal sponsorship allowed ─────────────────────────────────────────────
    if re.search(r"fiscal\s+spons|fiscal\s+agent|fiscally\s+sponsored", lower):
        extracted["fiscal_sponsorship_allowed"] = True
        confidence["fiscal_sponsorship_allowed"] = 0.7
        evidence["fiscal_sponsorship_allowed"] = _snippet(text, "fiscal spons")

    # ── Geography ──────────────────────────────────────────────────────────────
    geo, geo_conf, geo_ev = _extract_geography(text, org_profile)
    if geo:
        extracted["target_geography"] = geo
        confidence["target_geography"] = geo_conf
        evidence["target_geography"] = geo_ev

    # ── Focus areas (matched against the org's own vocabulary) ─────────────────
    focus, focus_ev = _extract_focus_areas(lower, org_profile)
    if focus:
        extracted["focus_areas"] = focus
        confidence["focus_areas"] = 0.5
        evidence["focus_areas"] = focus_ev

    return extracted, confidence, evidence


# ── helpers ──────────────────────────────────────────────────────────────────

def _extract_deadline(text: str) -> tuple[date | None, float, str]:
    """
    Find the most likely application deadline. Dates near deadline cue-words
    score higher. Returns the soonest high-confidence future-ish date.
    """
    candidates: list[tuple[date, float, str]] = []

    for m in _RE_TEXT_DATE.finditer(text):
        parsed = _parse_text_date(m.group(1), m.group(2), m.group(3))
        if parsed:
            conf, ev = _deadline_context(text, m.start(), m.end())
            candidates.append((parsed, conf, ev))

    for m in _RE_NUM_DATE.finditer(text):
        try:
            mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
            parsed = date(yy, mm, dd)
        except ValueError:
            continue
        conf, ev = _deadline_context(text, m.start(), m.end())
        candidates.append((parsed, conf, ev))

    if not candidates:
        return None, 0.0, ""

    # Prefer cue-associated dates; among those, the soonest.
    cued = [c for c in candidates if c[1] >= 0.7]
    pool = cued if cued else candidates
    pool.sort(key=lambda c: (-c[1], c[0]))
    best = pool[0]
    return best[0], best[1], best[2]


def _deadline_context(text: str, start: int, end: int) -> tuple[float, str]:
    window = text[max(0, start - 60):end + 20].replace("\n", " ").strip()
    has_cue = any(cue in window.lower() for cue in _DEADLINE_CUES)
    return (0.8 if has_cue else 0.4), window


def _parse_text_date(month_str: str, day_str: str, year_str: str) -> date | None:
    month = _MONTHS.get(month_str.lower().rstrip("."))
    if not month:
        return None
    try:
        return date(int(year_str), month, int(day_str))
    except ValueError:
        return None


def _extract_amounts(text: str) -> tuple[list[float], str]:
    amounts: list[float] = []
    evidence = ""
    for m in _RE_MONEY.finditer(text):
        raw = m.group(1).replace(",", "")
        try:
            value = float(raw)
        except ValueError:
            continue
        suffix = (m.group(2) or "").strip().lower()
        if suffix in ("million", "m"):
            value *= 1_000_000
        elif suffix in ("k", "thousand"):
            value *= 1_000
        # Ignore implausible/noise amounts (e.g. phone-ish or tiny)
        if 500 <= value <= 50_000_000:
            amounts.append(value)
            if not evidence:
                evidence = text[max(0, m.start() - 30):m.end() + 30].replace("\n", " ").strip()
    return amounts, evidence


def _extract_geography(text: str, org_profile: dict) -> tuple[str | None, float, str]:
    city = (org_profile.get("city") or "").strip()
    state = (org_profile.get("state") or "").strip()
    lower = text.lower()

    # Strong: explicit city or county match
    for term, conf in (
        (city, 0.8),
        ("middlesex county", 0.8),
        ("greater boston", 0.7),
        ("somerville", 0.85),
        (state, 0.5),
        ("massachusetts", 0.5),
    ):
        if term and term.lower() in lower:
            return term, conf, _snippet(text, term.lower())

    if "national" in lower or "nationwide" in lower or "united states" in lower:
        return "National", 0.5, _snippet(text, "national")

    return None, 0.0, ""


def _extract_focus_areas(lower: str, org_profile: dict) -> tuple[list[str], str]:
    """Match against the org's program focus areas plus a youth-funding lexicon."""
    vocab: set[str] = set()
    for program in org_profile.get("programs", []) or []:
        fa = program.get("focus_area") if isinstance(program, dict) else None
        if fa:
            vocab.add(fa.lower())
    vocab.update({
        "youth development", "stem", "steam", "climate", "workforce",
        "girls in stem", "mentorship", "after-school", "afterschool",
        "education", "arts", "mental health", "violence prevention",
    })

    found: list[str] = []
    for term in sorted(vocab):
        if term in lower and term not in found:
            found.append(term)
    evidence = ", ".join(found[:6])
    return found[:8], evidence


def _snippet(text: str, needle: str, width: int = 120) -> str:
    idx = text.lower().find(needle.lower())
    if idx == -1:
        return ""
    start = max(0, idx - width // 2)
    return text[start:start + width].replace("\n", " ").strip()
