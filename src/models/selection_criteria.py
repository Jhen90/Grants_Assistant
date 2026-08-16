# ============================================================
# File: src/models/selection_criteria.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: SelectionCriteria ORM model — weighted scoring rule sets
# ============================================================

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.database import Base


class SelectionCriteria(Base):
    """
    A named, versioned set of scoring rules used by the ScoringEngine.
    Only one criteria set is active at a time (is_active=True).
    Each criterion in criteria_json has: name, type, weight, is_hard_filter, config.
    """

    __tablename__ = "selection_criteria"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # JSON list of criterion dicts. Each dict:
    # { "name": str, "type": str, "weight": int, "is_hard_filter": bool, "config": dict }
    criteria_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<SelectionCriteria id={self.id!r} name={self.name!r} "
            f"version={self.version!r} active={self.is_active}>"
        )
