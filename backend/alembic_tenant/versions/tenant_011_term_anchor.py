"""tenant_011 — terms.ref / page_num / bbox anchor (#217)

Revision ID: tenant_011
Revises: tenant_010
Create Date: 2026-06-23 18:00:00.000000

Stage 3 review ref-link trust gate (FR-EX-05): per-term source anchor so the
review UI can scroll the original PDF to the field + highlight. All nullable →
graceful degrade (NULL = plain text, no dead link). Populated by KHE_AI.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_011"
down_revision: Union[str, None] = "tenant_010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("terms")}
    if "ref" not in cols:
        op.add_column("terms", sa.Column("ref", sa.Text(), nullable=True))
    if "page_num" not in cols:
        op.add_column("terms", sa.Column("page_num", sa.Integer(), nullable=True))
    if "bbox" not in cols:
        op.add_column("terms", sa.Column("bbox", sa.Text(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("terms")}
    for col in ("bbox", "page_num", "ref"):
        if col in cols:
            op.drop_column("terms", col)
