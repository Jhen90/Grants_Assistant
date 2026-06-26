"""Application, draft, review, manifest, template, and report tables

Revision ID: 002
Revises: 001
Create Date: 2026-06-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── applications ─────────────────────────────────────────────────────────
    op.create_table(
        "applications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("grant_id", sa.String(36), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT", "IN_REVIEW", "APPROVED", "SUBMITTED",
                "AWARDED", "DECLINED", "WITHDRAWN",
                name="app_status_enum",
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("applying_org_name", sa.String(255), nullable=True),
        sa.Column("lead_contact", sa.String(255), nullable=True),
        sa.Column("submission_method", sa.String(255), nullable=True),
        sa.Column("submission_confirmation", sa.String(500), nullable=True),
        sa.Column("submitted_at", sa.DateTime, nullable=True),
        sa.Column("submitted_by", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.DateTime, nullable=True),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("award_amount", sa.Float, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["grant_id"], ["grants.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_applications_grant_id", "applications", ["grant_id"])
    op.create_index("ix_applications_status", "applications", ["status"])

    # ── draft_versions ───────────────────────────────────────────────────────
    op.create_table(
        "draft_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("application_id", sa.String(36), nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("sections_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column("word_count", sa.Integer, nullable=True),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_draft_versions_application_id", "draft_versions", ["application_id"])
    op.create_index("ix_draft_versions_is_current", "draft_versions", ["is_current"])

    # ── review_checklists ─────────────────────────────────────────────────────
    op.create_table(
        "review_checklists",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("application_id", sa.String(36), nullable=False),
        sa.Column("draft_version_id", sa.String(36), nullable=False),
        sa.Column(
            "review_type",
            sa.Enum(
                "FACT_VERIFICATION", "ASSUMPTION_LOG", "AMBIGUITY_RESOLUTION", "COMPLIANCE",
                name="review_type_enum",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("PENDING", "IN_PROGRESS", "COMPLETED", "BLOCKED", name="review_status_enum"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("has_blocking_items", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("reviewer_name", sa.String(255), nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["draft_version_id"], ["draft_versions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_review_checklists_application_id", "review_checklists", ["application_id"])
    op.create_index("ix_review_checklists_status", "review_checklists", ["status"])

    # ── checklist_items ───────────────────────────────────────────────────────
    op.create_table(
        "checklist_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("checklist_id", sa.String(36), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("is_critical", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("is_checked", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("finding_notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["checklist_id"], ["review_checklists.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_checklist_items_checklist_id", "checklist_items", ["checklist_id"])

    # ── assumption_records ───────────────────────────────────────────────────
    op.create_table(
        "assumption_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("checklist_id", sa.String(36), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("basis", sa.Text, nullable=False),
        sa.Column("is_documented", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["checklist_id"], ["review_checklists.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_assumption_records_checklist_id", "assumption_records", ["checklist_id"])

    # ── ambiguity_records ────────────────────────────────────────────────────
    op.create_table(
        "ambiguity_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("checklist_id", sa.String(36), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("resolution", sa.Text, nullable=False),
        sa.Column("decision", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["checklist_id"], ["review_checklists.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ambiguity_records_checklist_id", "ambiguity_records", ["checklist_id"])

    # ── manifests ────────────────────────────────────────────────────────────
    op.create_table(
        "manifests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("application_id", sa.String(36), nullable=False, unique=True),
        sa.Column("events_json", sa.Text, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_manifests_application_id", "manifests", ["application_id"])

    # ── templates ────────────────────────────────────────────────────────────
    op.create_table(
        "templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("variables_json", sa.Text, nullable=False, server_default="[]"),
        sa.Column("word_count_target", sa.Integer, nullable=True),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("version", sa.String(50), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_templates_name", "templates", ["name"])
    op.create_index("ix_templates_category", "templates", ["category"])
    op.create_index("ix_templates_is_active", "templates", ["is_active"])

    # ── weekly_reports ───────────────────────────────────────────────────────
    op.create_table(
        "weekly_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), nullable=False),
        sa.Column("week_start", sa.Date, nullable=False),
        sa.Column("week_end", sa.Date, nullable=False),
        sa.Column("content_markdown", sa.Text, nullable=False),
        sa.Column("generated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("grants_evaluated", sa.Integer, nullable=False, server_default="0"),
        sa.Column("grants_recommended", sa.Integer, nullable=False, server_default="0"),
        sa.Column("grants_in_progress", sa.Integer, nullable=False, server_default="0"),
        sa.Column("grants_submitted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_weekly_reports_org_id", "weekly_reports", ["org_id"])

    # ── document_requirements ────────────────────────────────────────────────
    op.create_table(
        "document_requirements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("application_id", sa.String(36), nullable=False),
        sa.Column("document_name", sa.String(255), nullable=False),
        sa.Column("is_required", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("is_complete", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_document_requirements_application_id", "document_requirements", ["application_id"])


def downgrade() -> None:
    op.drop_table("document_requirements")
    op.drop_table("weekly_reports")
    op.drop_table("templates")
    op.drop_table("manifests")
    op.drop_table("ambiguity_records")
    op.drop_table("assumption_records")
    op.drop_table("checklist_items")
    op.drop_table("review_checklists")
    op.drop_table("draft_versions")
    op.drop_table("applications")
