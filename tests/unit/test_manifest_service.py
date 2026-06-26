# ============================================================
# File: tests/unit/test_manifest_service.py
# Version: 1.1.0
# Created: 2026-06-25
# ============================================================

from __future__ import annotations

import json

import pytest
from sqlalchemy.orm import Session

from src.models.application import Application
from src.models.manifest import Manifest
from src.services.manifest_service import ManifestService


@pytest.fixture()
def svc() -> ManifestService:
    return ManifestService()


class TestCreateManifest:
    def test_creates_manifest_record(
        self, db: Session, svc: ManifestService, sample_application: Application
    ):
        manifest = svc.create_manifest(db, sample_application.id)
        assert manifest.id is not None
        assert manifest.application_id == sample_application.id

    def test_initial_event_is_application_created(
        self, db: Session, svc: ManifestService, sample_application: Application
    ):
        svc.create_manifest(db, sample_application.id)
        manifest = db.query(Manifest).filter_by(application_id=sample_application.id).first()
        events = json.loads(manifest.events_json)
        assert len(events) >= 1
        assert events[0]["event_type"] == "APPLICATION_CREATED"


class TestAppendEvent:
    def test_appends_event(
        self, db: Session, svc: ManifestService, sample_application: Application
    ):
        svc.create_manifest(db, sample_application.id)
        svc.append_event(db, sample_application.id, "DRAFT_SAVED", {"version": 1})
        manifest = db.query(Manifest).filter_by(application_id=sample_application.id).first()
        events = json.loads(manifest.events_json)
        event_types = [e["event_type"] for e in events]
        assert "DRAFT_SAVED" in event_types

    def test_events_are_ordered(
        self, db: Session, svc: ManifestService, sample_application: Application
    ):
        svc.create_manifest(db, sample_application.id)
        svc.append_event(db, sample_application.id, "EVENT_A", {})
        svc.append_event(db, sample_application.id, "EVENT_B", {})
        manifest = db.query(Manifest).filter_by(application_id=sample_application.id).first()
        events = json.loads(manifest.events_json)
        types = [e["event_type"] for e in events]
        assert types.index("EVENT_A") < types.index("EVENT_B")


class TestExportMarkdown:
    def test_returns_markdown_table(
        self, db: Session, svc: ManifestService, sample_application: Application
    ):
        svc.create_manifest(db, sample_application.id)
        md = svc.export_markdown(db, sample_application.id)
        assert "|" in md
        assert "APPLICATION_CREATED" in md

    def test_no_manifest_returns_message(
        self, db: Session, svc: ManifestService, sample_application: Application
    ):
        md = svc.export_markdown(db, "nonexistent-id")
        assert "No manifest" in md
