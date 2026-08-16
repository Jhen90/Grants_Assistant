# ============================================================
# File: tests/unit/test_state_machine.py
# Version: 1.1.0
# Created: 2026-06-25
# ============================================================

import pytest

from src.engine.state_machine import advance_application_status, advance_grant_status
from src.models.application import ApplicationStatus
from src.models.grant import GrantStatus
from src.utils.error_handler import InvalidStatusTransitionError


class TestGrantStateMachine:
    def test_discovered_to_evaluated(self):
        result = advance_grant_status(GrantStatus.DISCOVERED, GrantStatus.EVALUATED)
        assert result == GrantStatus.EVALUATED

    def test_discovered_to_deferred(self):
        result = advance_grant_status(GrantStatus.DISCOVERED, GrantStatus.DEFERRED)
        assert result == GrantStatus.DEFERRED

    def test_evaluated_to_recommended(self):
        result = advance_grant_status(GrantStatus.EVALUATED, GrantStatus.RECOMMENDED)
        assert result == GrantStatus.RECOMMENDED

    def test_recommended_to_approved_to_apply(self):
        result = advance_grant_status(GrantStatus.RECOMMENDED, GrantStatus.APPROVED_TO_APPLY)
        assert result == GrantStatus.APPROVED_TO_APPLY

    def test_approved_to_apply_to_submitted(self):
        result = advance_grant_status(GrantStatus.APPROVED_TO_APPLY, GrantStatus.SUBMITTED)
        assert result == GrantStatus.SUBMITTED

    def test_submitted_to_awarded(self):
        result = advance_grant_status(GrantStatus.SUBMITTED, GrantStatus.AWARDED)
        assert result == GrantStatus.AWARDED

    def test_submitted_to_declined(self):
        result = advance_grant_status(GrantStatus.SUBMITTED, GrantStatus.DECLINED)
        assert result == GrantStatus.DECLINED

    def test_invalid_transition_raises(self):
        with pytest.raises(InvalidStatusTransitionError):
            advance_grant_status(GrantStatus.DISCOVERED, GrantStatus.SUBMITTED)

    def test_archived_is_terminal(self):
        with pytest.raises(InvalidStatusTransitionError):
            advance_grant_status(GrantStatus.ARCHIVED, GrantStatus.DISCOVERED)

    def test_accepts_string_inputs(self):
        result = advance_grant_status("DISCOVERED", "EVALUATED")
        assert result == GrantStatus.EVALUATED


class TestApplicationStateMachine:
    def test_draft_to_in_review(self):
        result = advance_application_status(
            ApplicationStatus.DRAFT, ApplicationStatus.IN_REVIEW
        )
        assert result == ApplicationStatus.IN_REVIEW

    def test_in_review_to_approved(self):
        result = advance_application_status(
            ApplicationStatus.IN_REVIEW, ApplicationStatus.APPROVED
        )
        assert result == ApplicationStatus.APPROVED

    def test_approved_to_submitted(self):
        result = advance_application_status(
            ApplicationStatus.APPROVED, ApplicationStatus.SUBMITTED
        )
        assert result == ApplicationStatus.SUBMITTED

    def test_submitted_to_awarded(self):
        result = advance_application_status(
            ApplicationStatus.SUBMITTED, ApplicationStatus.AWARDED
        )
        assert result == ApplicationStatus.AWARDED

    def test_awarded_is_terminal(self):
        with pytest.raises(InvalidStatusTransitionError):
            advance_application_status(
                ApplicationStatus.AWARDED, ApplicationStatus.DRAFT
            )

    def test_invalid_transition_raises(self):
        with pytest.raises(InvalidStatusTransitionError):
            advance_application_status(
                ApplicationStatus.DRAFT, ApplicationStatus.AWARDED
            )
