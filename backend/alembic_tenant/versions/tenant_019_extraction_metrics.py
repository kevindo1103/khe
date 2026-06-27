"""tenant_019 — extraction metrics columns on documents (#346)

Revision ID: tenant_019
Revises: tenant_018
Create Date: 2026-06-27 20:00:00.000000

Adds 3 nullable columns to `documents` for per-doc extraction metrics:
  documents.extraction_model      — LLM model string ("gemini-2.5-flash", ...)
  documents.extraction_latency_ms — total latency in milliseconds
  documents.extraction_warnings   — JSON array of warning strings

The 3 cost/provider/token columns already exist from tenant_013.
Forward-only: no backfill (existing docs keep NULL values).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_019"
down_revision: Union[str, None] = "tenant_018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    if "extraction_model" not in cols:
        op.add_column("documents", sa.Column("extraction_model", sa.String(), nullable=True))
    if "extraction_latency_ms" not in cols:
        op.add_column("documents", sa.Column("extraction_latency_ms", sa.Float(), nullable=True))
    if "extraction_warnings" not in cols:
        op.add_column("documents", sa.Column("extraction_warnings", sa.Text(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    for col in ("extraction_model", "extraction_latency_ms", "extraction_warnings"):
        if col in cols:
            op.drop_column("documents", col)
