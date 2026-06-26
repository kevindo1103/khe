"""002 — tenant_profiles table for legal_name (DEC-030)

Revision ID: 002
Revises: 001
Create Date: 2026-06-20 19:00:00.000000

Stores the SME's legal entity name so the obligation engine can match
against extraction parties[] to determine direction (nghĩa_vụ vs quyền_lợi).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())

    if "tenant_profiles" not in existing:
        op.create_table(
            "tenant_profiles",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("legal_name", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("tenant_id", name="uq_tenant_profile_tenant"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())

    if "tenant_profiles" in existing:
        op.drop_table("tenant_profiles")
