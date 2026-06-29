"""tenant_010 — obligations.snoozed_until (#214)

Revision ID: tenant_010
Revises: tenant_009
Create Date: 2026-06-23 17:00:00.000000

"Nhắc lại sau 3 ngày": suppress an obligation's reminder until snoozed_until.
NULL = not snoozed. Auto-expires; snooze never touches status/due_date (D-07).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_010"
down_revision: Union[str, None] = "tenant_009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("obligations")}
    if "snoozed_until" not in cols:
        op.add_column("obligations", sa.Column("snoozed_until", sa.DateTime(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("obligations")}
    if "snoozed_until" in cols:
        op.drop_column("obligations", "snoozed_until")
