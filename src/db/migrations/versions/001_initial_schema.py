"""Initial schema — organizations, funders, selection_criteria, grants

Revision ID: 001
Revises:
Create Date: 2026-06-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── organizations ────────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("mission", sa.Text, nullable=False),
        sa.Column("values_text", sa.Text, nullable=True),
        sa.Column("programs_json", sa.Text, nullable=True),
        sa.Column("eligibility_json", sa.Text, nullable=True),
        sa.Column("website", sa.String(1000), nullable=True),
        sa.Column("city", sa.String(255), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_organizations_name", "organizations", ["name"])

    # ── org_documents ────────────────────────────────────────────────────────
    op.create_table(
        "org_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("doc_type", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("uploaded_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"]),
    )
    op.create_index("ix_org_documents_org_id", "org_documents", ["org_id"])

    # ── funders ──────────────────────────────────────────────────────────────
    op.create_table(
        "funders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "funder_type",
            sa.Enum(
                "foundation", "government", "corporate", "other", "community_partner",
                name="funder_type_enum",
            ),
            nullable=False,
            server_default="foundation",
        ),
        sa.Column("is_fiscal_sponsor", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("is_501c3", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("website", sa.String(1000), nullable=True),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("relationship_notes", sa.Text, nullable=True),
        sa.Column("priority_tier", sa.Integer, nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_funders_name", "funders", ["name"])

    # ── selection_criteria ───────────────────────────────────────────────────
    op.create_table(
        "selection_criteria",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(50), nullable=False, server_default="1.0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("criteria_json", sa.Text, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_selection_criteria_is_active", "selection_criteria", ["is_active"])

    # ── grants ───────────────────────────────────────────────────────────────
    op.create_table(
        "grants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("funder_id", sa.String(36), nullable=True),
        sa.Column("funder_name", sa.String(255), nullable=True),
        sa.Column("fiscal_sponsor_id", sa.String(36), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "DISCOVERED", "EVALUATED", "RECOMMENDED", "APPROVED_TO_APPLY",
                "DEFERRED", "SUBMITTED", "AWARDED", "DECLINED", "WITHDRAWN", "ARCHIVED",
                name="grant_status_enum",
            ),
            nullable=False,
            server_default="DISCOVERED",
        ),
        sa.Column("fit_score", sa.Float, nullable=True),
        sa.Column("score_breakdown_json", sa.Text, nullable=True),
        sa.Column("deadline", sa.Date, nullable=True),
        sa.Column(
            "deadline_urgency",
            sa.Enum("RED", "YELLOW", "GREEN", "GRAY", name="deadline_urgency_enum"),
            nullable=True,
        ),
        sa.Column("amount_min", sa.Float, nullable=True),
        sa.Column("amount_max", sa.Float, nullable=True),
        sa.Column("focus_areas_json", sa.Text, nullable=True),
        sa.Column("target_geography", sa.String(500), nullable=True),
        sa.Column("eligibility_501c3_required", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("fiscal_sponsorship_allowed", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["funder_id"], ["funders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["fiscal_sponsor_id"], ["funders.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_grants_title", "grants", ["title"])
    op.create_index("ix_grants_status", "grants", ["status"])
    op.create_index("ix_grants_funder_id", "grants", ["funder_id"])


def downgrade() -> None:
    op.drop_table("grants")
    op.drop_table("selection_criteria")
    op.drop_table("funders")
    op.drop_table("org_documents")
    op.drop_table("organizations")
