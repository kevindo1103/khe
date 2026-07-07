"""006 — TenantProfile compliance fields (#495)

Revision ID: 006
Revises: 005
Create Date: 2026-07-07

Adds compliance-profile fields to tenant_profiles in master.db:
legal_form, has_employees, vat_period, fiscal_year_start.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("tenant_profiles")}

    if "legal_form" not in cols:
        op.add_column(
            "tenant_profiles",
            sa.Column("legal_form", sa.String(), nullable=True),
        )
    if "has_employees" not in cols:
        op.add_column(
            "tenant_profiles",
            sa.Column("has_employees", sa.Boolean(), nullable=True),
        )
    if "vat_period" not in cols:
        op.add_column(
            "tenant_profiles",
            sa.Column("vat_period", sa.String(), nullable=True),
        )
    if "fiscal_year_start" not in cols:
        op.add_column(
            "tenant_profiles",
            sa.Column("fiscal_year_start", sa.Date(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("tenant_profiles")}

    for col_name in ("fiscal_year_start", "vat_period", "has_employees", "legal_form"):
        if col_name in cols:
            op.drop_column("tenant_profiles", col_name)
