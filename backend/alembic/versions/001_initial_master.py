"""initial master db

Revision ID: 001
Revises:
Create Date: 2026-06-11 14:44:00.000000

Idempotent: skips tables that already exist. Handles a VPS master.db that was
bootstrapped via SQLAlchemy create_all() (init_master_db) without an
alembic_version stamp — `alembic upgrade head` then re-runs 001 against
pre-existing tables and fails with "table tenants already exists". Guarding each
create_table makes the upgrade a no-op in that case so alembic can stamp the
revision cleanly.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())

    if "tenants" not in existing:
        op.create_table(
            "tenants",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("db_path", sa.String(), nullable=False),
            sa.Column("plan", sa.String(), server_default="starter"),
            sa.Column("is_active", sa.Boolean(), server_default="1"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
        )

    if "tenant_users" not in existing:
        op.create_table(
            "tenant_users",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("username", sa.String(), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("role", sa.String(), server_default="staff"),
            sa.Column("is_active", sa.Boolean(), server_default="1"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("tenant_id", "username", name="uq_tenant_username"),
        )

    if "firm_partners" not in existing:
        op.create_table(
            "firm_partners",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("contact_email", sa.String(), nullable=True),
            sa.Column("contact_phone", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default="1"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
        )

    if "firm_tenant_access" not in existing:
        op.create_table(
            "firm_tenant_access",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("firm_id", sa.Integer(), nullable=False),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("consent_status", sa.String(), server_default="pending"),
            sa.Column("granted_at", sa.DateTime(), nullable=True),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["firm_id"], ["firm_partners.id"]),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("firm_id", "tenant_id", name="uq_firm_tenant"),
        )


def downgrade() -> None:
    op.drop_table("firm_tenant_access")
    op.drop_table("firm_partners")
    op.drop_table("tenant_users")
    op.drop_table("tenants")
