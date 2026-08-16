# ============================================================
# File: src/models/funder.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Funder ORM model — grant-making organizations and community partners
# ============================================================

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


class FunderType(str, enum.Enum):
    FOUNDATION = "foundation"
    GOVERNMENT = "government"
    CORPORATE = "corporate"
    OTHER = "other"
    COMMUNITY_PARTNER = "community_partner"


class Funder(Base):
    __tablename__ = "funders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    funder_type: Mapped[FunderType] = mapped_column(
        Enum(FunderType, name="funder_type_enum"), nullable=False, default=FunderType.FOUNDATION
    )

    # Fiscal sponsor flags (Section 9.4)
    is_fiscal_sponsor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_501c3: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    website: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    relationship_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority_tier: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1=highest priority
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    grants: Mapped[list[Grant]] = relationship(
        "Grant", back_populates="funder", foreign_keys="Grant.funder_id"
    )
    sponsored_grants: Mapped[list[Grant]] = relationship(
        "Grant", back_populates="fiscal_sponsor", foreign_keys="Grant.fiscal_sponsor_id"
    )

    def __repr__(self) -> str:
        return (
            f"<Funder id={self.id!r} name={self.name!r} "
            f"type={self.funder_type.value!r} fiscal_sponsor={self.is_fiscal_sponsor}>"
        )


# Deferred import to avoid circular dependency
from src.models.grant import Grant  # noqa: E402, F401
