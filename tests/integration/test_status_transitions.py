# ============================================================
# File: tests/integration/test_status_transitions.py
# Version: 1.1.0
# Created: 2026-06-25
# Description: Integration test — verify all grant and application state machine transitions
# ============================================================

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from src.models.grant import Grant, GrantStatus, VALID_TRANSITIONS
from src.models.application import Application, ApplicationStatus, VALID_APP_TRANSITIONS
from src.services.grant_service import GrantService
from src.utils.error_handler import InvalidStatusTransitionError


@pytest.fixture()
def grant_svc() -> GrantService:
    return GrantService()


class TestGrantTransitions:
    """Verify every valid transition in VALID_TRANSITIONS works via GrantService."""

    def _set_grant_status(self, db: Session, grant: Grant, status: GrantStatus) -> Grant:
        grant.status = status
        db.commit()
        db.refresh(grant)
        return grant

    def test_all_valid_transitions_succeed(
        self, db: Session, grant_svc: GrantService, sample_grant: Grant
    ):
        for current_str, next_statuses in VALID_TRANSITIONS.items():
            current = GrantStatus(current_str)
            for next_str in next_statuses:
                # Reset grant to current status
                self._set_grant_status(db, sample_grant, current)
                next_status = GrantStatus(next_str)
                updated = grant_svc.advance_status(db, sample_grant.id, next_status)
                assert updated.status == next_status, (
                    f"Expected {next_str} from {current_str}, got {updated.status.value}"
                )

    def test_invalid_transitions_raise(
        self, db: Session, grant_svc: GrantService, sample_grant: Grant
    ):
        invalid_pairs = [
            (GrantStatus.DISCOVERED, GrantStatus.SUBMITTED),
            (GrantStatus.EVALUATED, GrantStatus.AWARDED),
            (GrantStatus.ARCHIVED, GrantStatus.DISCOVERED),
            (GrantStatus.AWARDED, GrantStatus.DISCOVERED),
        ]
        for current, invalid_next in invalid_pairs:
            sample_grant.status = current
            db.commit()
            with pytest.raises(InvalidStatusTransitionError):
                grant_svc.advance_status(db, sample_grant.id, invalid_next)


class TestApplicationTransitions:
    """Verify every valid transition in VALID_APP_TRANSITIONS via the state machine."""

    def test_all_valid_app_transitions_succeed(self, db: Session):
        from src.engine.state_machine import advance_application_status
        for current_str, next_statuses in VALID_APP_TRANSITIONS.items():
            current = ApplicationStatus(current_str)
            for next_str in next_statuses:
                result = advance_application_status(current, ApplicationStatus(next_str))
                assert result == ApplicationStatus(next_str)

    def test_terminal_app_statuses_have_no_transitions(self, db: Session):
        terminal = {"AWARDED", "DECLINED", "WITHDRAWN"}
        for t in terminal:
            assert VALID_APP_TRANSITIONS[t] == []
