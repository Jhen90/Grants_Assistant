"""Discovered candidates staging table (grant discovery subsystem)

Revision ID: 003
Revises: 002
Create Date: 2026-06-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "discovered_candidates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("raw_title", sa.String(500), nullable=False),
        sa.Column("raw_funder", sa.String(255), nullable=True),
        sa.Column("extracted_json", sa.Text, nullable=False, server_default="{}"),
        sa.Column("raw_text_excerpt", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.Enum("NEW", "IMPORTED", "DISMISSED", "DUPLICATE", name="candidate_status_enum"),
            nullable=False,
            server_default="NEW",
        ),
        sa.Column("linked_grant_id", sa.String(36), nullable=True),
        sa.Column("dedup_note", sa.String(500), nullable=True),
        sa.Column("search_query", sa.String(500), nullable=True),
        sa.Column("discovered_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime, nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_discovered_candidates_source", "discovered_candidates", ["source"])
    op.create_index("ix_discovered_candidates_source_url", "discovered_candidates", ["source_url"])
    op.create_index("ix_discovered_candidates_status", "discovered_candidates", ["status"])


def downgrade() -> None:
    op.drop_table("discovered_candidates")
