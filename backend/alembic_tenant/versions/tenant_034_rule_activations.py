"""tenant_034: rule_activations table for Track 2 compliance (#495).

Tracks which rule packs have been activated per tenant, including declined
obligations and the generated virtual document / obligation IDs.
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op


revision: str = "tenant_034"
down_revision: Union[str, None] = "tenant_033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    tables = sa.inspect(conn).get_table_names()

    if "rule_activations" not in tables:
        op.create_table(
            "rule_activations",
            sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
            sa.Column("rule_pack_id", sa.String(), nullable=False),
            sa.Column("rule_pack_version", sa.String(), nullable=True),
            sa.Column(
                "status",
                sa.String(),
                nullable=False,
                server_default="active",
            ),  # active | declined | paused
            sa.Column("activated_at", sa.DateTime(), nullable=True),
            sa.Column("activated_by", sa.String(), nullable=True),
            sa.Column("obligation_ids", sa.Text(), nullable=True),  # JSON list[int]
            sa.Column(
                "virtual_document_id",
                sa.Integer(),
                sa.ForeignKey("documents.id"),
                nullable=True,
            ),
        )
        op.create_index(
            "uq_rule_activations_pack",
            "rule_activations",
            ["rule_pack_id"],
            unique=True,
        )


def downgrade() -> None:
    op.drop_index("uq_rule_activations_pack", table_name="rule_activations")
    op.drop_table("rule_activations")
