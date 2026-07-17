"""Candidate evaluation fields (Grant Scout EVALUATE phase)

Adds pre-review scoring / eligibility / urgency columns to discovered_candidates.

Revision ID: 004
Revises: 003
Create Date: 2026-07-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("discovered_candidates") as batch:
        batch.add_column(sa.Column("fit_score", sa.Float(), nullable=True))
        batch.add_column(
            sa.Column(
                "eligibility_status",
                sa.Enum("ELIGIBLE", "INELIGIBLE", "UNKNOWN", name="eligibility_status_enum"),
                nullable=True,
            )
        )
        batch.add_column(
            sa.Column("is_strong_match", sa.Boolean(), nullable=False, server_default="0")
        )
        batch.add_column(sa.Column("deadline_urgency", sa.String(10), nullable=True))
        batch.add_column(
            sa.Column("act_now", sa.Boolean(), nullable=False, server_default="0")
        )
        batch.add_column(sa.Column("why_fits", sa.String(500), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("discovered_candidates") as batch:
        batch.drop_column("why_fits")
        batch.drop_column("act_now")
        batch.drop_column("deadline_urgency")
        batch.drop_column("is_strong_match")
        batch.drop_column("eligibility_status")
        batch.drop_column("fit_score")
