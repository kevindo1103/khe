"""tenant_009 — chat_sessions table (DEC-031 v2, #201).

Revision ID: tenant_009
Revises: tenant_008
Create Date: 2026-06-23 14:00:00.000000

Result-seeded progressive chat state. Pointer IDs only (no PII text). One row
per device/tab thread; TTL 24h via expires_at + weekly cleanup.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_009"
down_revision: Union[str, None] = "tenant_008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "chat_sessions" in inspector.get_table_names():
        return  # idempotent

    # NOTE: declare the UNIQUE constraint inline — SQLite cannot ALTER-ADD a
    # constraint after table creation (op.create_unique_constraint fails).
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("state_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("session_id", name="uq_chat_sessions_session_id"),
    )
    op.create_index("ix_chat_sessions_tenant_id", "chat_sessions", ["tenant_id"])
    op.create_index(
        "idx_chat_sessions_user",
        "chat_sessions",
        ["tenant_id", "user_id", "updated_at"],
    )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "chat_sessions" not in inspector.get_table_names():
        return
    op.drop_index("idx_chat_sessions_user", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_tenant_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")
