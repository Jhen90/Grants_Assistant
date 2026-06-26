# ============================================================
# File: src/models/application.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Application ORM model — grant application lifecycle tracking
# ============================================================

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class ApplicationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    SUBMITTED = "SUBMITTED"
    AWARDED = "AWARDED"
    DECLINED = "DECLINED"
    WITHDRAWN = "WITHDRAWN"


VALID_APP_TRANSITIONS: dict[str, list[str]] = {
    ApplicationStatus.DRAFT:      [ApplicationStatus.IN_REVIEW, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.IN_REVIEW:  [ApplicationStatus.DRAFT, ApplicationStatus.APPROVED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.APPROVED:   [ApplicationStatus.SUBMITTED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.SUBMITTED:  [ApplicationStatus.AWARDED, ApplicationStatus.DECLINED, ApplicationStatus.WITHDRAWN],
    ApplicationStatus.AWARDED:    [],
    ApplicationStatus.DECLINED:   [],
    ApplicationStatus.WITHDRAWN:  [],
}


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    grant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("grants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="app_status_enum"),
        nullable=False,
        default=ApplicationStatus.DRAFT,
        index=True,
    )

    # The entity actually submitting (org name or fiscal sponsor name)
    applying_org_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lead_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Submission details (populated by record_submission)
    submission_method: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submission_confirmation: Mapped[str | None] = mapped_column(String(500), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitted_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Approval details (populated by approve_application — the hard gate)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Outcome details (populated by record_outcome)
    award_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    grant: Mapped[Grant] = relationship("Grant", back_populates="applications")
    draft_versions: Mapped[list[DraftVersion]] = relationship(
        "DraftVersion", back_populates="application", order_by="DraftVersion.version_number"
    )
    review_checklists: Mapped[list[ReviewChecklist]] = relationship(
        "ReviewChecklist", back_populates="application", cascade="all, delete-orphan"
    )
    manifest: Mapped[Manifest | None] = relationship(
        "Manifest", back_populates="application", uselist=False
    )
    document_requirements: Mapped[list[DocumentRequirement]] = relationship(
        "DocumentRequirement", back_populates="application", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Application id={self.id!r} grant_id={self.grant_id!r} status={self.status.value!r}>"


class DocumentRequirement(Base):
    """
    A document that must be collected/prepared before final submission.
    Created in a default set by ApplicationService.create_application().
    Users can add/edit/mark-complete via the Documents tab.
    """

    __tablename__ = "document_requirements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    application: Mapped[Application] = relationship(
        "Application", back_populates="document_requirements"
    )


from src.models.grant import Grant  # noqa: E402, F401
from src.models.draft import DraftVersion  # noqa: E402, F401
from src.models.review import ReviewChecklist  # noqa: E402, F401
from src.models.manifest import Manifest  # noqa: E402, F401
