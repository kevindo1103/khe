"""tenant_006 — obligation series + event-chain columns (DEC-030 Phase 2).

Revision ID: tenant_006
Revises: tenant_005
Create Date: 2026-06-20 21:00:00.000000

Adds 8 columns to the obligations table for milestone series tracking,
event-chaining, and raw amount storage.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_006"
down_revision: Union[str, None] = "tenant_005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NEW_COLUMNS = [
    ("milestone_series_id", sa.Text()),
    ("milestone_index", sa.Integer()),
    ("milestone_total", sa.Integer()),
    ("milestone_trigger", sa.Text(), sa.text("'date'")),
    ("trigger_condition", sa.Text()),
    ("trigger_delay_days", sa.Integer()),
    ("trigger_obligation_id", sa.Integer()),
    ("amount_raw", sa.Text()),
]


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = {c["name"] for c in inspector.get_columns("obligations")}

    for col in _NEW_COLUMNS:
        name = col[0]
        col_type = col[1]
        if name in existing_cols:
            continue
        if len(col) > 2:
            server_default = col[2]
            op.add_column("obligations", sa.Column(name, col_type, server_default=server_default))
        else:
            op.add_column("obligations", sa.Column(name, col_type))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = {c["name"] for c in inspector.get_columns("obligations")}

    for col in reversed(_NEW_COLUMNS):
        name = col[0]
        if name in existing_cols:
            op.drop_column("obligations", name)
