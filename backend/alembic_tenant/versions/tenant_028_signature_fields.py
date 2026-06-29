"""tenant_028: signature detection columns on documents (#368, R5)."""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "tenant_028"
down_revision: Union[str, None] = "tenant_027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("documents")}
    if "has_signature" not in existing:
        op.add_column("documents", sa.Column("has_signature", sa.Boolean(), nullable=True))
    if "signature_pages" not in existing:
        op.add_column("documents", sa.Column("signature_pages", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_column("signature_pages")
        batch_op.drop_column("has_signature")
