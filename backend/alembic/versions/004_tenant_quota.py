"""004 — ingest quota columns on tenants (#63 / FR-TN-01)

Revision ID: 004
Revises: 003
Create Date: 2026-06-23 17:30:00.000000

Prevents vision-extraction cost runaway (D-11): doc_quota per tenant +
docs_used_month counter (atomic increment on ingest) + quota_reset_at
(calendar-1st reset via APScheduler).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("tenants")}

    if "doc_quota" not in cols:
        op.add_column("tenants", sa.Column("doc_quota", sa.Integer(), nullable=False, server_default="500"))
    if "docs_used_month" not in cols:
        op.add_column("tenants", sa.Column("docs_used_month", sa.Integer(), nullable=False, server_default="0"))
    if "quota_reset_at" not in cols:
        op.add_column("tenants", sa.Column("quota_reset_at", sa.Date(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("tenants")}

    for col in ("quota_reset_at", "docs_used_month", "doc_quota"):
        if col in cols:
            op.drop_column("tenants", col)
