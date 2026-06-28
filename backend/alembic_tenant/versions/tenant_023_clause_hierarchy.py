"""tenant_023 — clause hierarchy columns (#365)

Revision ID: tenant_023
Revises: tenant_022
Create Date: 2026-06-28 18:00:00.000000

Adds 3 nullable columns to `clauses` for parent/child hierarchy:
  clauses.parent_id    — Integer self-FK to clauses.id (NULL = top-level)
  clauses.level        — Integer 0=top, 1=sub, 2=sub-sub
  clauses.clause_path  — String dotted path e.g. "2.1.1"

Forward-only: existing clauses stay NULL (flat), no break.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_023"
down_revision: Union[str, None] = "tenant_022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("clauses")}
    if "parent_id" not in cols:
        op.add_column("clauses", sa.Column("parent_id", sa.Integer(), nullable=True))
    if "level" not in cols:
        op.add_column("clauses", sa.Column("level", sa.Integer(), nullable=True))
    if "clause_path" not in cols:
        op.add_column("clauses", sa.Column("clause_path", sa.String(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("clauses")}
    for col in ("parent_id", "level", "clause_path"):
        if col in cols:
            op.drop_column("clauses", col)
