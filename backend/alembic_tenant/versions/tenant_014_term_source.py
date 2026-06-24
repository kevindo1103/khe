"""tenant_014 — terms.source provenance column (#258)

Revision ID: tenant_014
Revises: tenant_013
Create Date: 2026-06-24 10:00:00.000000

Distinguishes how a Term's value originated: "extracted" (vision), "remap"
(clause-remap, text-only #258), "manual" (user edit). NULL for legacy rows.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_014"
down_revision: Union[str, None] = "tenant_013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("terms")}
    if "source" not in cols:
        op.add_column("terms", sa.Column("source", sa.String(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("terms")}
    if "source" in cols:
        op.drop_column("terms", "source")
