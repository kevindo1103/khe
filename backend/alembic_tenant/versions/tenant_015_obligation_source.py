"""tenant_015 — obligations.source provenance column (#301)

Revision ID: tenant_015
Revises: tenant_014
Create Date: 2026-06-26 21:00:00.000000

Distinguishes how an Obligation originated: "ai_extracted" (derive_obligations),
"user_manual" (user-created), "ai_re_derived" (remap/re-read). NULL for legacy.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_015"
down_revision: Union[str, None] = "tenant_014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("obligations")}
    if "source" not in cols:
        op.add_column("obligations", sa.Column("source", sa.String(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("obligations")}
    if "source" in cols:
        op.drop_column("obligations", "source")
