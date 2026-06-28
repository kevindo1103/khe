"""tenant_027: clause_cross_refs table (#373, R10)."""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "tenant_027"
down_revision: Union[str, None] = "tenant_026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if sa.inspect(conn).has_table("clause_cross_refs"):
        return
    op.create_table(
        "clause_cross_refs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(), nullable=False, index=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("source_clause_id", sa.Integer(), nullable=False),
        sa.Column("ref_text", sa.String(), nullable=False),
        sa.Column("ref_type", sa.String(), nullable=False),   # "clause" | "appendix" | "document"
        sa.Column("target_clause_id", sa.Integer(), nullable=True),
        sa.Column("target_clause_path", sa.String(), nullable=True),
        sa.Column("target_doc_id", sa.Integer(), nullable=True),
        sa.Column("is_orphan", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("clause_cross_refs")
