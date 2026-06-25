"""tenant_013 — documents extraction cost columns (#255)

Revision ID: tenant_013
Revises: tenant_012
Create Date: 2026-06-24 09:00:00.000000

Per-doc extraction cost tracking for pilot margin monitoring. All nullable →
pre-migration / not-yet-extracted docs read NULL (summed as 0 in the report).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_013"
down_revision: Union[str, None] = "tenant_012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COLS = {
    "extraction_provider": sa.String(),
    "extraction_tokens_in": sa.Integer(),
    "extraction_tokens_out": sa.Integer(),
    "extraction_cost_vnd": sa.Float(),
}


def upgrade() -> None:
    conn = op.get_bind()
    existing = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    for name, col_type in _COLS.items():
        if name not in existing:
            op.add_column("documents", sa.Column(name, col_type, nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    existing = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    for name in reversed(list(_COLS)):
        if name in existing:
            op.drop_column("documents", name)
