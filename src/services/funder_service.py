# ============================================================
# File: src/services/funder_service.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: FunderService — CRUD for funders and per-funder grant history
# ============================================================

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.application import Application, ApplicationStatus
from src.models.funder import Funder, FunderType
from src.models.grant import Grant
from src.utils.logger import get_logger

log = get_logger(__name__)


class FunderService:
    def get_all(self, db: Session, include_deleted: bool = False) -> list[Funder]:
        q = db.query(Funder)
        if not include_deleted:
            q = q.filter(Funder.is_deleted.is_(False))
        return q.order_by(Funder.priority_tier.nullslast(), Funder.name).all()

    def get_fiscal_sponsors(self, db: Session) -> list[Funder]:
        """Return all funders that can serve as fiscal sponsors (is_fiscal_sponsor=True)."""
        return (
            db.query(Funder)
            .filter(Funder.is_fiscal_sponsor.is_(True), Funder.is_deleted.is_(False))
            .order_by(Funder.name)
            .all()
        )

    def get_by_id(self, db: Session, funder_id: str) -> Funder | None:
        return db.query(Funder).filter_by(id=funder_id).first()

    def get_by_name(self, db: Session, name: str) -> Funder | None:
        return db.query(Funder).filter_by(name=name).first()

    def create(self, db: Session, data: dict) -> Funder:
        funder = Funder(
            name=data["name"],
            funder_type=FunderType(data.get("funder_type", "foundation")),
            is_fiscal_sponsor=bool(data.get("is_fiscal_sponsor", False)),
            is_501c3=bool(data.get("is_501c3", False)),
            website=data.get("website"),
            contact_name=data.get("contact_name"),
            contact_email=data.get("contact_email"),
            relationship_notes=data.get("relationship_notes"),
            priority_tier=data.get("priority_tier"),
        )
        db.add(funder)
        db.commit()
        db.refresh(funder)
        log.info("Funder created: %s (id=%s)", funder.name, funder.id)
        return funder

    def update(self, db: Session, funder_id: str, data: dict) -> Funder | None:
        funder = self.get_by_id(db, funder_id)
        if funder is None:
            return None
        for field in (
            "name", "website", "contact_name", "contact_email",
            "relationship_notes", "priority_tier", "is_fiscal_sponsor", "is_501c3",
        ):
            if field in data:
                setattr(funder, field, data[field])
        if "funder_type" in data:
            funder.funder_type = FunderType(data["funder_type"])
        db.commit()
        db.refresh(funder)
        return funder

    def soft_delete(self, db: Session, funder_id: str) -> None:
        funder = self.get_by_id(db, funder_id)
        if funder:
            funder.is_deleted = True
            db.commit()
            log.info("Funder soft-deleted: %s", funder_id)

    def get_history(self, db: Session, funder_id: str) -> dict:
        """Return grant history summary for a funder."""
        grants = (
            db.query(Grant)
            .filter(Grant.funder_id == funder_id, Grant.is_deleted.is_(False))
            .all()
        )
        awarded_apps = (
            db.query(Application)
            .join(Grant, Application.grant_id == Grant.id)
            .filter(
                Grant.funder_id == funder_id,
                Application.status == ApplicationStatus.AWARDED,
                Application.is_deleted.is_(False),
            )
            .all()
        )
        total_requested = sum(
            (g.amount_max or g.amount_min or 0) for g in grants
        )
        total_awarded = sum(a.award_amount or 0 for a in awarded_apps)
        return {
            "grants_count": len(grants),
            "awarded_count": len(awarded_apps),
            "total_requested": total_requested,
            "total_awarded": total_awarded,
            "win_rate": (
                round(len(awarded_apps) / len(grants) * 100, 1) if grants else 0.0
            ),
        }
