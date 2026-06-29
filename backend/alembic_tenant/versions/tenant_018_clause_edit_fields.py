"""tenant_018 — clause inline edit columns (#324)

Revision ID: tenant_018
Revises: tenant_017
Create Date: 2026-06-27 09:00:00.000000

Adds 3 nullable columns to `clauses` for user inline editing (D-07):
  clauses.edited_by_user   — username who last edited the clause
  clauses.edited_at        — timestamp of last edit
  clauses.original_content — AI-extracted original (snapshot on first edit only)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_018"
down_revision: Union[str, None] = "tenant_017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("clauses")}
    if "edited_by_user" not in cols:
        op.add_column("clauses", sa.Column("edited_by_user", sa.String(), nullable=True))
    if "edited_at" not in cols:
        op.add_column("clauses", sa.Column("edited_at", sa.DateTime(), nullable=True))
    if "original_content" not in cols:
        op.add_column("clauses", sa.Column("original_content", sa.Text(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("clauses")}
    for col in ("edited_by_user", "edited_at", "original_content"):
        if col in cols:
            op.drop_column("clauses", col)
