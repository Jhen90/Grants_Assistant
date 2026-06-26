# ============================================================
# File: tests/unit/test_deadline_classifier.py
# Version: 1.1.0
# Created: 2026-06-25
# ============================================================

from datetime import date, timedelta

import pytest

from src.engine.deadline_classifier import classify_urgency, days_until_deadline
from src.models.grant import DeadlineUrgency


class TestClassifyUrgency:
    def test_none_deadline_is_gray(self):
        assert classify_urgency(None) == DeadlineUrgency.GRAY

    def test_past_deadline_is_gray(self):
        past = date.today() - timedelta(days=1)
        assert classify_urgency(past) == DeadlineUrgency.GRAY

    def test_exactly_30_days_is_red(self):
        d = date.today() + timedelta(days=30)
        assert classify_urgency(d) == DeadlineUrgency.RED

    def test_1_day_is_red(self):
        d = date.today() + timedelta(days=1)
        assert classify_urgency(d) == DeadlineUrgency.RED

    def test_31_days_is_yellow(self):
        d = date.today() + timedelta(days=31)
        assert classify_urgency(d) == DeadlineUrgency.YELLOW

    def test_60_days_is_yellow(self):
        d = date.today() + timedelta(days=60)
        assert classify_urgency(d) == DeadlineUrgency.YELLOW

    def test_61_days_is_green(self):
        d = date.today() + timedelta(days=61)
        assert classify_urgency(d) == DeadlineUrgency.GREEN

    def test_90_days_is_green(self):
        d = date.today() + timedelta(days=90)
        assert classify_urgency(d) == DeadlineUrgency.GREEN

    def test_91_days_is_gray(self):
        d = date.today() + timedelta(days=91)
        assert classify_urgency(d) == DeadlineUrgency.GRAY


class TestDaysUntilDeadline:
    def test_none_returns_none(self):
        assert days_until_deadline(None) is None

    def test_future_returns_positive(self):
        d = date.today() + timedelta(days=10)
        result = days_until_deadline(d)
        assert result == 10

    def test_past_returns_negative(self):
        d = date.today() - timedelta(days=5)
        result = days_until_deadline(d)
        assert result is not None and result < 0
