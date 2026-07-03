"""tenant_031: add honest completeness flag to documents (#276).

Adds `may_have_unextracted_obligations` (Boolean, nullable=True) to the
documents table only. No default is set so legacy and newly extracted docs
remain NULL until the fast-follow CompletenessVerifier runs.
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "tenant_031"
down_revision: Union[str, None] = "tenant_030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("documents")}
    if "may_have_unextracted_obligations" not in existing:
        op.add_column(
            "documents",
            sa.Column("may_have_unextracted_obligations", sa.Boolean(), nullable=True),
        )


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_column("may_have_unextracted_obligations")
