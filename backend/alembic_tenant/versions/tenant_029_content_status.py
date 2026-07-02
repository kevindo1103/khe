"""tenant_029: clause content_status for two-pass map-reduce extraction (#449, mini-sprint #443)."""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "tenant_029"
down_revision: Union[str, None] = "tenant_028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("clauses")}
    if "content_status" not in existing:
        op.add_column("clauses", sa.Column("content_status", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("clauses") as batch_op:
        batch_op.drop_column("content_status")
