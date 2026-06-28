"""tenant_022 — extended party details + self-mapping columns (#364)

Revision ID: tenant_022
Revises: tenant_021
Create Date: 2026-06-28 16:00:00.000000

Adds 6 nullable columns to `parties` for full party details and self-mapping:
  parties.address         — địa chỉ pháp lý
  parties.contact         — SĐT / email liên hệ
  parties.representative  — người đại diện (tên + chức vụ)
  parties.tax_code        — mã số thuế (MST)
  parties.is_self         — bool: auto-mapped from tenant_profile.legal_name
  parties.aliases         — JSON array of alternative names / abbreviations

Forward-only: no backfill. Existing parties keep NULL / False.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_022"
down_revision: Union[str, None] = "tenant_021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("parties")}
    if "address" not in cols:
        op.add_column("parties", sa.Column("address", sa.Text(), nullable=True))
    if "contact" not in cols:
        op.add_column("parties", sa.Column("contact", sa.String(), nullable=True))
    if "representative" not in cols:
        op.add_column("parties", sa.Column("representative", sa.String(), nullable=True))
    if "tax_code" not in cols:
        op.add_column("parties", sa.Column("tax_code", sa.String(), nullable=True))
    if "is_self" not in cols:
        op.add_column("parties", sa.Column("is_self", sa.Boolean(), nullable=True, server_default="0"))
    if "aliases" not in cols:
        op.add_column("parties", sa.Column("aliases", sa.Text(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("parties")}
    for col in ("address", "contact", "representative", "tax_code", "is_self", "aliases"):
        if col in cols:
            op.drop_column("parties", col)
