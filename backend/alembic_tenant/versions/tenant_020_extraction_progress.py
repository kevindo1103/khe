"""tenant_020 — extraction progress columns on documents (#360)

Revision ID: tenant_020
Revises: tenant_019
Create Date: 2026-06-28 10:00:00.000000

Adds 2 nullable columns to `documents` for real-time extraction progress:
  documents.processing_stage    — stage enum string (queued|ocr|llm|saving|done|failed)
  documents.processing_progress — integer 0-100

Forward-only: no backfill. Existing docs keep NULL (FE degrades gracefully).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_020"
down_revision: Union[str, None] = "tenant_019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    if "processing_stage" not in cols:
        op.add_column("documents", sa.Column("processing_stage", sa.String(), nullable=True))
    if "processing_progress" not in cols:
        op.add_column("documents", sa.Column("processing_progress", sa.Integer(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    for col in ("processing_stage", "processing_progress"):
        if col in cols:
            op.drop_column("documents", col)
