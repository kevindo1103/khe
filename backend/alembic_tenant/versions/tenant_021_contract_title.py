"""tenant_021 — contract title + number columns on documents (#363)

Revision ID: tenant_021
Revises: tenant_020
Create Date: 2026-06-28 14:00:00.000000

Adds 2 nullable columns to `documents`:
  documents.title           — extracted contract title from doc body (tieu_de_hd term)
  documents.contract_number — extracted contract number, e.g. "XX/2025/HDMB" (so_hop_dong term)

Forward-only: no backfill. Existing docs keep NULL values.

Depends on tenant_020 (extraction progress columns, #360) — merge #374 first.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_021"
down_revision: Union[str, None] = "tenant_020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    if "title" not in cols:
        op.add_column("documents", sa.Column("title", sa.String(), nullable=True))
    if "contract_number" not in cols:
        op.add_column("documents", sa.Column("contract_number", sa.String(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    for col in ("title", "contract_number"):
        if col in cols:
            op.drop_column("documents", col)
