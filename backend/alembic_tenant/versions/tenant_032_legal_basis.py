"""tenant_032: add legal_basis to obligations (#502).

Adds `legal_basis` (String, nullable=True) to the obligations table.
Populated by rule-pack flow (DEC-057) with legal citation strings
e.g. "Điều 15, NĐ 70/2025". User-manual obligations leave it NULL.
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "tenant_032"
down_revision: Union[str, None] = "tenant_031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    existing = {c["name"] for c in sa.inspect(conn).get_columns("obligations")}
    if "legal_basis" not in existing:
        op.add_column(
            "obligations",
            sa.Column("legal_basis", sa.String(), nullable=True),
        )


def downgrade() -> None:
    with op.batch_alter_table("obligations") as batch_op:
        batch_op.drop_column("legal_basis")
