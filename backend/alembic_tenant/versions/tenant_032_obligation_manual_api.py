"""tenant_032: allow document_id NULL + add source_rule_id for manual/rule-pack obligations (#494).

Makes Obligation.document_id nullable so Track-2 rule-pack obligations and
true manual obligations can exist without a parent Document. Adds
source_rule_id so rule-pack obligations can trace back to their originating
rule pack fixture for diff/re-confirm flows (#495).
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
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("obligations")}

    # 1a. document_id nullable — SQLite requires batch_alter_table.
    with op.batch_alter_table("obligations") as batch_op:
        batch_op.alter_column("document_id", existing_type=sa.Integer(), nullable=True)

    # 1b. source_rule_id — traces rule-pack origin for Track 2 (#495).
    if "source_rule_id" not in existing:
        op.add_column("obligations", sa.Column("source_rule_id", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("obligations") as batch_op:
        batch_op.alter_column("document_id", existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column("source_rule_id")
