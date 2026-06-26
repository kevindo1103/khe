"""tenant_017 — obligation clause provenance columns (#303, DEC-048 §13)

Revision ID: tenant_017
Revises: tenant_016
Create Date: 2026-06-26 23:00:00.000000

Adds:
  obligations.source_clause_num — FK-ish to Clause.clause_num in same doc
  obligations.derived_from      — "original" | "user_edit" provenance enum
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_017"
down_revision: Union[str, None] = "tenant_016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    obl_cols = {c["name"] for c in sa.inspect(conn).get_columns("obligations")}
    if "source_clause_num" not in obl_cols:
        op.add_column("obligations", sa.Column("source_clause_num", sa.String(), nullable=True))
    if "derived_from" not in obl_cols:
        op.add_column("obligations", sa.Column("derived_from", sa.String(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    obl_cols = {c["name"] for c in sa.inspect(conn).get_columns("obligations")}
    for col in ("source_clause_num", "derived_from"):
        if col in obl_cols:
            op.drop_column("obligations", col)
