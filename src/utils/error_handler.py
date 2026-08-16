# ============================================================
# File: src/utils/error_handler.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Custom exception hierarchy for GrantNova
# ============================================================


class GmasError(Exception):
    """Base exception for all GrantNova application errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | details={self.details}"
        return self.message


class SubmissionBlockedError(GmasError):
    """
    Raised by ApplicationService.approve_application() when not all pre-conditions
    for submission approval are met. This is the hard gate — raised at the SERVICE
    layer, not just in the UI.
    """

    def __init__(self, reason: str, blockers: list[str] | None = None) -> None:
        super().__init__(
            message=f"Submission blocked: {reason}",
            details={"blockers": blockers or []},
        )
        self.reason = reason
        self.blockers = blockers or []


class InvalidStatusTransitionError(GmasError):
    """Raised when a grant or application status transition is not in VALID_TRANSITIONS."""

    def __init__(self, current: str, attempted: str, entity: str = "Grant") -> None:
        super().__init__(
            message=(
                f"{entity} cannot transition from {current!r} to {attempted!r}"
            ),
            details={"current_status": current, "attempted_status": attempted},
        )
        self.current = current
        self.attempted = attempted


class DuplicateGrantError(GmasError):
    """Raised by GrantService.create_grant() when a duplicate is detected."""

    def __init__(self, match_type: str, match_field: str, existing_id: str) -> None:
        super().__init__(
            message=(
                f"Duplicate grant detected ({match_type} match on {match_field}). "
                f"Existing grant ID: {existing_id}"
            ),
            details={
                "match_type": match_type,
                "match_field": match_field,
                "existing_id": existing_id,
            },
        )
        self.match_type = match_type
        self.match_field = match_field
        self.existing_id = existing_id


class ValidationError(GmasError):
    """Raised when input data fails business validation rules."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(
            message=f"Validation error on '{field}': {message}",
            details={"field": field},
        )
        self.field = field


class ConfigurationError(GmasError):
    """Raised when required configuration is missing or malformed."""

    pass


class IntegrationDisabledError(GmasError):
    """Raised when a Phase 7/8 integration (Ollama, Google Docs) is called but not enabled."""

    def __init__(self, integration: str) -> None:
        super().__init__(
            message=(
                f"The '{integration}' integration is not configured. "
                "See Settings → Integrations for setup instructions."
            ),
            details={"integration": integration},
        )
        self.integration = integration
