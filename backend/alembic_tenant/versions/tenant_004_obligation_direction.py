"""tenant_004 — obligation direction + recurrence rename (DEC-027/030, #122 resolved)

Revision ID: tenant_004
Revises: tenant_003
Create Date: 2026-06-20 19:00:00.000000

Schema delta for DEC-030:
- Rename cadence axis: obligation_type → recurrence
- Add category axis: obligation_type (payment/expiration/renewal/...)
- Add direction axis: direction (nghĩa_vụ/quyền_lợi/null)
- Add obligor: role_label from parties[]
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_004"
down_revision: Union[str, None] = "tenant_003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {c["name"] for c in inspector.get_columns("obligations")}

    # 1. Rename cadence axis: obligation_type → recurrence
    #    SQLite < 3.25 doesn't support RENAME COLUMN — use batch mode.
    if "obligation_type" in existing_columns and "recurrence" not in existing_columns:
        with op.batch_alter_table("obligations") as batch_op:
            batch_op.alter_column("obligation_type", new_column_name="recurrence")

    # Re-inspect after batch alter (table was rebuilt)
    inspector = sa.inspect(conn)
    existing_columns = {c["name"] for c in inspector.get_columns("obligations")}

    # 2. Add category axis (DEC-027)
    if "obligation_type" not in existing_columns:
        op.add_column("obligations", sa.Column("obligation_type", sa.String(), server_default="other"))

    # 3. Add direction axis (DEC-030)
    if "direction" not in existing_columns:
        op.add_column("obligations", sa.Column("direction", sa.String(), nullable=True))

    # 4. Add obligor (DEC-030)
    if "obligor" not in existing_columns:
        op.add_column("obligations", sa.Column("obligor", sa.String(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {c["name"] for c in inspector.get_columns("obligations")}

    if "obligor" in existing_columns:
        op.drop_column("obligations", "obligor")
    if "direction" in existing_columns:
        op.drop_column("obligations", "direction")
    if "obligation_type" in existing_columns:
        op.drop_column("obligations", "obligation_type")

    if "recurrence" in existing_columns and "obligation_type" not in existing_columns:
        with op.batch_alter_table("obligations") as batch_op:
            batch_op.alter_column("recurrence", new_column_name="obligation_type")
