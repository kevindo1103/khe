"""tenant_012 — documents.confirmed_by_user_at (#238)

Revision ID: tenant_012
Revises: tenant_011
Create Date: 2026-06-23 19:30:00.000000

User-explicit document review confirm (D-02). NULL = not yet confirmed → counts
toward the journey NEEDS_REVIEW gate. Existing docs backfill NULL (forces a
re-confirm — acceptable for staging UAT per #238).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_012"
down_revision: Union[str, None] = "tenant_011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    if "confirmed_by_user_at" not in cols:
        op.add_column("documents", sa.Column("confirmed_by_user_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    if "confirmed_by_user_at" in cols:
        op.drop_column("documents", "confirmed_by_user_at")
