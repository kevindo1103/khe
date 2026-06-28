"""tenant_026: definitions glossary table (#372, R9)."""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "tenant_026"
down_revision: Union[str, None] = "tenant_025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if sa.inspect(conn).has_table("definitions"):
        return
    op.create_table(
        "definitions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(), nullable=False, index=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("term", sa.String(), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("source_clause_num", sa.String(), nullable=True),
        sa.Column("source_clause_id", sa.Integer(), nullable=True),  # app-level ref, no FK constraint
        sa.Column("edited_by_user", sa.String(), nullable=True),
        sa.Column("edited_at", sa.DateTime(), nullable=True),
        sa.Column("original_definition", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    pass
