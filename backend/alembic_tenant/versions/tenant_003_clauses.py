"""tenant_003 — clauses table

Revision ID: tenant_003
Revises: tenant_002
Create Date: 2026-06-20 04:00:00.000000

Schema delta for DEC-026 (LLM chat query + clause extraction).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_003"
down_revision: Union[str, None] = "tenant_002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotent: only create the table if it does not exist.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "clauses" in inspector.get_table_names():
        return

    op.create_table(
        "clauses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("clause_num", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page_num", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_clauses_document", "clauses", ["document_id"])
    op.create_index("idx_clauses_tenant", "clauses", ["tenant_id"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "clauses" not in inspector.get_table_names():
        return

    op.drop_index("idx_clauses_tenant", table_name="clauses")
    op.drop_index("idx_clauses_document", table_name="clauses")
    op.drop_table("clauses")
