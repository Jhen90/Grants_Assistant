# ============================================================
# File: src/models/grant.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Grant ORM model with status state machine and fiscal sponsor FK
# ============================================================

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class GrantStatus(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    EVALUATED = "EVALUATED"
    RECOMMENDED = "RECOMMENDED"
    APPROVED_TO_APPLY = "APPROVED_TO_APPLY"
    DEFERRED = "DEFERRED"
    SUBMITTED = "SUBMITTED"
    AWARDED = "AWARDED"
    DECLINED = "DECLINED"
    WITHDRAWN = "WITHDRAWN"
    ARCHIVED = "ARCHIVED"


class DeadlineUrgency(str, enum.Enum):
    RED = "RED"      # ≤ 30 days
    YELLOW = "YELLOW"  # 31–60 days
    GREEN = "GREEN"    # 61–90 days
    GRAY = "GRAY"      # > 90 days, no deadline, or past deadline


# Valid status transitions (state machine enforced at service layer)
VALID_TRANSITIONS: dict[str, list[str]] = {
    GrantStatus.DISCOVERED:        [GrantStatus.EVALUATED, GrantStatus.DEFERRED, GrantStatus.ARCHIVED],
    GrantStatus.EVALUATED:         [GrantStatus.RECOMMENDED, GrantStatus.DEFERRED, GrantStatus.ARCHIVED],
    GrantStatus.RECOMMENDED:       [GrantStatus.APPROVED_TO_APPLY, GrantStatus.DEFERRED, GrantStatus.ARCHIVED],
    GrantStatus.APPROVED_TO_APPLY: [GrantStatus.SUBMITTED, GrantStatus.WITHDRAWN, GrantStatus.ARCHIVED],
    GrantStatus.DEFERRED:          [
        GrantStatus.DISCOVERED, GrantStatus.EVALUATED,
        GrantStatus.RECOMMENDED, GrantStatus.ARCHIVED,
    ],
    GrantStatus.SUBMITTED: [GrantStatus.AWARDED, GrantStatus.DECLINED, GrantStatus.WITHDRAWN],
    GrantStatus.AWARDED:   [GrantStatus.ARCHIVED],
    GrantStatus.DECLINED:  [GrantStatus.ARCHIVED],
    GrantStatus.WITHDRAWN: [GrantStatus.ARCHIVED],
    GrantStatus.ARCHIVED:  [],
}


class Grant(Base):
    __tablename__ = "grants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)

    # Funder relationship (optional FK — user can enter a funder name not in DB)
    funder_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("funders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    funder_name: Mapped[str | None] = mapped_column(String(255), nullable=True)  # denormalized fallback

    # Per-grant fiscal sponsor (overrides org default if set)
    fiscal_sponsor_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("funders.id", ondelete="SET NULL"), nullable=True
    )

    # Status and scoring
    status: Mapped[GrantStatus] = mapped_column(
        Enum(GrantStatus, name="grant_status_enum"),
        nullable=False,
        default=GrantStatus.DISCOVERED,
        index=True,
    )
    fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_breakdown_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Deadline
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    deadline_urgency: Mapped[DeadlineUrgency | None] = mapped_column(
        Enum(DeadlineUrgency, name="deadline_urgency_enum"), nullable=True
    )

    # Financial
    amount_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    amount_max: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Eligibility and targeting
    focus_areas_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    target_geography: Mapped[str | None] = mapped_column(String(500), nullable=True)
    eligibility_501c3_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fiscal_sponsorship_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Metadata
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    funder: Mapped[Funder | None] = relationship(
        "Funder", back_populates="grants", foreign_keys=[funder_id]
    )
    fiscal_sponsor: Mapped[Funder | None] = relationship(
        "Funder", back_populates="sponsored_grants", foreign_keys=[fiscal_sponsor_id]
    )
    applications: Mapped[list[Application]] = relationship("Application", back_populates="grant")

    def __repr__(self) -> str:
        return (
            f"<Grant id={self.id!r} title={self.title!r} "
            f"status={self.status.value!r} score={self.fit_score}>"
        )


# Deferred imports
from src.models.funder import Funder  # noqa: E402, F401
from src.models.application import Application  # noqa: E402, F401
