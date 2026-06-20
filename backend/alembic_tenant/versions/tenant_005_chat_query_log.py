"""tenant_005 — chat_query_log table (DEC-028)

Revision ID: tenant_005
Revises: tenant_004
Create Date: 2026-06-20 20:30:00.000000

Per-tenant chat query log for the learning loop (DEC-028).
Separate from the append-only events ledger — this table is purgeable
(NĐ 13/2023 compliance debt: raw PII, staging/pilot bypass only).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_005"
down_revision: Union[str, None] = "tenant_004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "chat_query_log" in inspector.get_table_names():
        return

    op.create_table(
        "chat_query_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("tool_calls", sa.Text(), nullable=True),
        sa.Column("found", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("result_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_chat_query_log_tenant", "chat_query_log", ["tenant_id"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "chat_query_log" not in inspector.get_table_names():
        return

    op.drop_index("idx_chat_query_log_tenant", table_name="chat_query_log")
    op.drop_table("chat_query_log")
