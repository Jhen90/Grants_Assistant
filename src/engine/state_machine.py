# ============================================================
# File: src/engine/state_machine.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Validates and enforces grant/application status transitions
# ============================================================

from __future__ import annotations

from src.models.application import VALID_APP_TRANSITIONS, ApplicationStatus
from src.models.grant import VALID_TRANSITIONS, GrantStatus
from src.utils.error_handler import InvalidStatusTransitionError
from src.utils.logger import get_logger

log = get_logger(__name__)


def advance_grant_status(current: GrantStatus | str, new: GrantStatus | str) -> GrantStatus:
    """
    Validate a grant status transition and return the new status if valid.
    Raises InvalidStatusTransitionError for invalid transitions.
    """
    current_str = current.value if isinstance(current, GrantStatus) else current
    new_str = new.value if isinstance(new, GrantStatus) else new

    allowed = VALID_TRANSITIONS.get(current_str, [])
    allowed_values = [s.value if isinstance(s, GrantStatus) else s for s in allowed]

    if new_str not in allowed_values:
        log.warning("Invalid grant transition: %s → %s", current_str, new_str)
        raise InvalidStatusTransitionError(current_str, new_str, entity="Grant")

    log.debug("Grant status transition: %s → %s", current_str, new_str)
    return GrantStatus(new_str)


def advance_application_status(
    current: ApplicationStatus | str, new: ApplicationStatus | str
) -> ApplicationStatus:
    """
    Validate an application status transition and return the new status if valid.
    Raises InvalidStatusTransitionError for invalid transitions.
    """
    current_str = current.value if isinstance(current, ApplicationStatus) else current
    new_str = new.value if isinstance(new, ApplicationStatus) else new

    allowed = VALID_APP_TRANSITIONS.get(current_str, [])
    allowed_values = [s.value if isinstance(s, ApplicationStatus) else s for s in allowed]

    if new_str not in allowed_values:
        log.warning("Invalid application transition: %s → %s", current_str, new_str)
        raise InvalidStatusTransitionError(current_str, new_str, entity="Application")

    log.debug("Application status transition: %s → %s", current_str, new_str)
    return ApplicationStatus(new_str)
