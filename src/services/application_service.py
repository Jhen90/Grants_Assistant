# ============================================================
# File: src/services/application_service.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: ApplicationService — application lifecycle + hard approval gate
# ============================================================

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from src.engine.state_machine import advance_application_status, advance_grant_status
from src.models.application import Application, ApplicationStatus, DocumentRequirement
from src.models.draft import DraftVersion
from src.models.grant import Grant, GrantStatus
from src.models.review import ReviewChecklist, ReviewStatus
from src.services.manifest_service import ManifestService
from src.utils.error_handler import SubmissionBlockedError
from src.utils.logger import get_logger

log = get_logger(__name__)

_manifest_svc = ManifestService()

# Default document requirements created for every new application
_DEFAULT_DOCUMENT_REQUIREMENTS = [
    "Completed grant application form",
    "IRS 990 (most recent, or fiscal sponsor's 990)",
    "Project/program budget",
    "Organizational budget (current fiscal year)",
    "Letter of support from fiscal sponsor (if applicable)",
    "Brief organizational overview / one-pager",
    "List of board members (if required by funder)",
]


class ApplicationService:
    def create_application(self, db: Session, grant_id: str) -> Application:
        """
        Create an Application for a grant. Also creates:
        - Default DocumentRequirement checklist
        - A Manifest with APPLICATION_CREATED event
        Advances the grant status to APPROVED_TO_APPLY.
        """
        grant = db.query(Grant).filter_by(id=grant_id, is_deleted=False).first()
        if grant is None:
            raise ValueError(f"Grant {grant_id!r} not found.")

        # Advance grant to APPROVED_TO_APPLY
        grant.status = advance_grant_status(grant.status, GrantStatus.APPROVED_TO_APPLY)

        application = Application(
            grant_id=grant_id,
            status=ApplicationStatus.DRAFT,
        )
        db.add(application)
        db.flush()

        # Create default document requirements
        for doc_name in _DEFAULT_DOCUMENT_REQUIREMENTS:
            req = DocumentRequirement(
                application_id=application.id,
                document_name=doc_name,
                is_required=True,
            )
            db.add(req)

        db.flush()

        # Create manifest
        _manifest_svc.create_manifest(db, application.id)

        db.commit()
        db.refresh(application)
        log.info("Application created: %s for grant %s.", application.id, grant_id)
        return application

    def create_draft_version(
        self, db: Session, application_id: str, sections: dict
    ) -> DraftVersion:
        """
        Save a new DraftVersion. Auto-increments version_number.
        Marks previous versions as not current.
        """
        # Determine next version number
        existing_versions = (
            db.query(DraftVersion)
            .filter_by(application_id=application_id)
            .order_by(DraftVersion.version_number.desc())
            .all()
        )
        next_version = (existing_versions[0].version_number + 1) if existing_versions else 1

        # Mark all previous versions not current
        for v in existing_versions:
            v.is_current = False

        word_count = sum(
            len(str(content).split()) for content in sections.values()
        )

        draft = DraftVersion(
            application_id=application_id,
            version_number=next_version,
            sections_json=json.dumps(sections, ensure_ascii=False),
            word_count=word_count,
            is_current=True,
        )
        db.add(draft)
        db.flush()

        _manifest_svc.append_event(
            db, application_id, "DRAFT_SAVED",
            {"version_number": next_version, "word_count": word_count},
        )

        db.commit()
        db.refresh(draft)
        log.info(
            "Draft v%d saved for application %s (%d words).",
            next_version, application_id, word_count,
        )
        return draft

    def approve_application(
        self, db: Session, application_id: str, approver_name: str
    ) -> Application:
        """
        HARD GATE — enforced at service layer per FR-AG-001 through FR-AG-004.

        Checks:
        1. All 4 review checklists exist for the current draft.
        2. All 4 are in COMPLETED status.
        3. None have has_blocking_items=True.

        Raises SubmissionBlockedError with specific reason if any check fails.
        If all pass: sets status=APPROVED, records approver, appends manifest event.
        """
        application = db.query(Application).filter_by(id=application_id).first()
        if application is None:
            raise ValueError(f"Application {application_id!r} not found.")

        # Get current draft version
        current_draft = (
            db.query(DraftVersion)
            .filter_by(application_id=application_id, is_current=True)
            .first()
        )
        if current_draft is None:
            raise SubmissionBlockedError(
                reason="No draft version exists for this application.",
                blockers=["Create and save at least one draft version before approving."],
            )

        # Get all 4 checklists for the current draft
        checklists = (
            db.query(ReviewChecklist)
            .filter_by(application_id=application_id, draft_version_id=current_draft.id)
            .all()
        )

        blockers: list[str] = []

        # Check 1: All 4 review types present
        found_types = {c.review_type for c in checklists}
        from src.models.review import ReviewType
        missing_types = set(ReviewType) - found_types
        if missing_types:
            for t in missing_types:
                blockers.append(f"Review checklist not started: {t.value}")

        # Check 2: All checklists COMPLETED
        for checklist in checklists:
            if checklist.status != ReviewStatus.COMPLETED:
                blockers.append(
                    f"{checklist.review_type.value} review is {checklist.status.value} "
                    f"(must be COMPLETED)."
                )

        # Check 3: No blocking items
        for checklist in checklists:
            if checklist.has_blocking_items:
                blockers.append(
                    f"{checklist.review_type.value} review has unchecked critical items."
                )

        if blockers:
            raise SubmissionBlockedError(
                reason="Not all review requirements are met.",
                blockers=blockers,
            )

        # All checks pass — approve.
        # The state machine requires DRAFT → IN_REVIEW → APPROVED. Reviews are
        # complete at this point, so advance through IN_REVIEW if the application
        # is still in DRAFT (it may not have been explicitly moved during review).
        if application.status == ApplicationStatus.DRAFT:
            application.status = advance_application_status(
                application.status, ApplicationStatus.IN_REVIEW
            )
        application.status = advance_application_status(
            application.status, ApplicationStatus.APPROVED
        )
        application.approved_at = datetime.utcnow()
        application.approved_by = approver_name

        _manifest_svc.append_event(
            db, application_id, "APPROVED",
            {"approver": approver_name, "draft_version": current_draft.version_number},
        )

        db.commit()
        db.refresh(application)
        log.info("Application %s APPROVED by %s.", application_id, approver_name)
        return application

    def record_submission(
        self,
        db: Session,
        application_id: str,
        method: str,
        confirmation: str,
        submitter: str,
    ) -> Application:
        application = db.query(Application).filter_by(id=application_id).first()
        if application is None:
            raise ValueError(f"Application {application_id!r} not found.")

        application.status = advance_application_status(
            application.status, ApplicationStatus.SUBMITTED
        )
        application.submission_method = method
        application.submission_confirmation = confirmation
        application.submitted_at = datetime.utcnow()
        application.submitted_by = submitter

        # Also advance the parent grant status
        grant = db.query(Grant).filter_by(id=application.grant_id).first()
        if grant:
            grant.status = advance_grant_status(grant.status, GrantStatus.SUBMITTED)

        _manifest_svc.append_event(
            db, application_id, "SUBMITTED",
            {"method": method, "confirmation": confirmation, "submitter": submitter},
        )

        db.commit()
        db.refresh(application)
        log.info("Application %s recorded as SUBMITTED.", application_id)
        return application

    def record_outcome(
        self,
        db: Session,
        application_id: str,
        outcome: str,  # "AWARDED" | "DECLINED" | "WITHDRAWN"
        award_amount: float | None = None,
    ) -> Application:
        application = db.query(Application).filter_by(id=application_id).first()
        if application is None:
            raise ValueError(f"Application {application_id!r} not found.")

        new_status = ApplicationStatus(outcome)
        application.status = advance_application_status(application.status, new_status)
        if award_amount is not None:
            application.award_amount = award_amount

        # Advance grant to matching status
        grant = db.query(Grant).filter_by(id=application.grant_id).first()
        if grant:
            grant.status = advance_grant_status(grant.status, GrantStatus(outcome))

        _manifest_svc.append_event(
            db, application_id, f"OUTCOME_{outcome}",
            {"outcome": outcome, "award_amount": award_amount},
        )

        db.commit()
        db.refresh(application)
        log.info("Application %s outcome recorded: %s.", application_id, outcome)
        return application

    def get_by_id(self, db: Session, application_id: str) -> Application | None:
        return db.query(Application).filter_by(id=application_id, is_deleted=False).first()

    def get_for_grant(self, db: Session, grant_id: str) -> list[Application]:
        return (
            db.query(Application)
            .filter_by(grant_id=grant_id, is_deleted=False)
            .order_by(Application.created_at.desc())
            .all()
        )
