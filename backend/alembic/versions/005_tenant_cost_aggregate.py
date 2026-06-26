"""005 — tenant cost aggregate columns (#255)

Revision ID: 005
Revises: 004
Create Date: 2026-06-24 09:00:00.000000

Per-tenant extraction cost aggregate for pilot margin monitoring.
cost_vnd_month resets calendar-1st with docs_used_month; cost_vnd_total lifetime.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("tenants")}
    if "cost_vnd_month" not in cols:
        op.add_column("tenants", sa.Column("cost_vnd_month", sa.Float(), nullable=False, server_default="0"))
    if "cost_vnd_total" not in cols:
        op.add_column("tenants", sa.Column("cost_vnd_total", sa.Float(), nullable=False, server_default="0"))


def downgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("tenants")}
    if "cost_vnd_total" in cols:
        op.drop_column("tenants", "cost_vnd_total")
    if "cost_vnd_month" in cols:
        op.drop_column("tenants", "cost_vnd_month")
