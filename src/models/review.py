# ============================================================
# File: src/models/review.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Review models — checklists, items, assumption records, ambiguity records
# ============================================================

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class ReviewType(str, enum.Enum):
    FACT_VERIFICATION = "FACT_VERIFICATION"
    ASSUMPTION_LOG = "ASSUMPTION_LOG"
    AMBIGUITY_RESOLUTION = "AMBIGUITY_RESOLUTION"
    COMPLIANCE = "COMPLIANCE"


class ReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class ReviewChecklist(Base):
    """One checklist per review type per application draft version."""

    __tablename__ = "review_checklists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    draft_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("draft_versions.id", ondelete="CASCADE"), nullable=False
    )
    review_type: Mapped[ReviewType] = mapped_column(
        Enum(ReviewType, name="review_type_enum"), nullable=False
    )
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="review_status_enum"),
        nullable=False,
        default=ReviewStatus.PENDING,
        index=True,
    )
    has_blocking_items: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reviewer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    application: Mapped[Application] = relationship("Application", back_populates="review_checklists")
    items: Mapped[list[ChecklistItem]] = relationship(
        "ChecklistItem", back_populates="checklist", cascade="all, delete-orphan"
    )
    assumptions: Mapped[list[AssumptionRecord]] = relationship(
        "AssumptionRecord", back_populates="checklist", cascade="all, delete-orphan"
    )
    ambiguities: Mapped[list[AmbiguityRecord]] = relationship(
        "AmbiguityRecord", back_populates="checklist", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<ReviewChecklist id={self.id!r} type={self.review_type.value!r} "
            f"status={self.status.value!r}>"
        )


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    checklist_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("review_checklists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_critical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_checked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    finding_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    checklist: Mapped[ReviewChecklist] = relationship("ReviewChecklist", back_populates="items")

    def __repr__(self) -> str:
        return f"<ChecklistItem id={self.id!r} critical={self.is_critical} checked={self.is_checked}>"


class AssumptionRecord(Base):
    """Free-form assumption logged during the Assumption Log review."""

    __tablename__ = "assumption_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    checklist_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("review_checklists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    basis: Mapped[str] = mapped_column(Text, nullable=False)  # why the assumption was made
    is_documented: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    checklist: Mapped[ReviewChecklist] = relationship("ReviewChecklist", back_populates="assumptions")


class AmbiguityRecord(Base):
    """Free-form ambiguity logged during the Ambiguity Resolution review."""

    __tablename__ = "ambiguity_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    checklist_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("review_checklists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resolution: Mapped[str] = mapped_column(Text, nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    checklist: Mapped[ReviewChecklist] = relationship("ReviewChecklist", back_populates="ambiguities")


from src.models.application import Application  # noqa: E402, F401
