# ============================================================
# File: src/engine/deadline_classifier.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Classifies grant deadlines into urgency bands (RED/YELLOW/GREEN/GRAY)
# ============================================================

from __future__ import annotations

from datetime import date

from src.models.grant import DeadlineUrgency


# Urgency thresholds (days until deadline)
_RED_MAX = 30
_YELLOW_MAX = 60
_GREEN_MAX = 90


def days_until_deadline(deadline: date | None) -> int | None:
    """
    Returns the number of days from today until the deadline.
    Returns None if deadline is None.
    Negative values mean the deadline has already passed.
    """
    if deadline is None:
        return None
    return (deadline - date.today()).days


def classify_urgency(deadline: date | None) -> DeadlineUrgency:
    """
    Classifies a deadline date into a DeadlineUrgency band.

    RED    — deadline within 30 days (urgent)
    YELLOW — deadline 31–60 days out (approaching)
    GREEN  — deadline 61–90 days out (comfortable)
    GRAY   — deadline > 90 days out, no deadline set, or deadline already passed

    Past deadlines return GRAY (not ERROR) — the grant remains visible but
    urgency badge signals inaction, not an error condition.
    """
    days = days_until_deadline(deadline)

    if days is None or days < 0:
        return DeadlineUrgency.GRAY

    if days <= _RED_MAX:
        return DeadlineUrgency.RED
    if days <= _YELLOW_MAX:
        return DeadlineUrgency.YELLOW
    if days <= _GREEN_MAX:
        return DeadlineUrgency.GREEN
    return DeadlineUrgency.GRAY
