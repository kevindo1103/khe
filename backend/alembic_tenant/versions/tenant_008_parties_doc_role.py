"""tenant_008 — parties table: document_id + role_label columns (#155, DEC-030).

Revision ID: tenant_008
Revises: tenant_007
Create Date: 2026-06-21 00:30:00.000000

Extends the existing parties table (tenant_001) with document_id FK
and role_label to support per-document party persistence and self-party
confirmation (DEC-030).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_008"
down_revision: Union[str, None] = "tenant_007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NEW_COLUMNS = [
    ("document_id", sa.Integer()),
    ("role_label", sa.Text()),
]


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = {c["name"] for c in inspector.get_columns("parties")}

    for name, col_type in _NEW_COLUMNS:
        if name in existing_cols:
            continue
        op.add_column("parties", sa.Column(name, col_type, nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = {c["name"] for c in inspector.get_columns("parties")}

    for name, _ in reversed(_NEW_COLUMNS):
        if name in existing_cols:
            op.drop_column("parties", name)
