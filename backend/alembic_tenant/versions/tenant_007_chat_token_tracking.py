"""tenant_007 — chat token tracking columns (DEC-028 / #164).

Revision ID: tenant_007
Revises: tenant_006
Create Date: 2026-06-20 23:30:00.000000

Adds 4 columns to chat_query_log for tokenomics visibility:
input_tokens, output_tokens, cost_vnd, llm_calls.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_007"
down_revision: Union[str, None] = "tenant_006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NEW_COLUMNS = [
    ("input_tokens", sa.Integer(), sa.text("0")),
    ("output_tokens", sa.Integer(), sa.text("0")),
    ("cost_vnd", sa.Float(), sa.text("0.0")),
    ("llm_calls", sa.Integer(), sa.text("0")),
]


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = {c["name"] for c in inspector.get_columns("chat_query_log")}

    for col in _NEW_COLUMNS:
        name = col[0]
        col_type = col[1]
        if name in existing_cols:
            continue
        server_default = col[2]
        op.add_column("chat_query_log", sa.Column(name, col_type, server_default=server_default))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = {c["name"] for c in inspector.get_columns("chat_query_log")}

    for col in reversed(_NEW_COLUMNS):
        name = col[0]
        if name in existing_cols:
            op.drop_column("chat_query_log", name)
