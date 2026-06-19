"""tenant_002 — consent columns + document_relationships + chain fields

Revision ID: tenant_002
Revises: tenant_001
Create Date: 2026-06-19 04:00:00.000000

Schema delta for DEC-010 (consent), DEC-019/020/021 (chain).
All additions are nullable → no batch_alter_table needed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_002"
down_revision: Union[str, None] = "tenant_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── events ──
    op.add_column("events", sa.Column("purpose", sa.String(), nullable=True))
    op.add_column("events", sa.Column("consent_reference", sa.String(), nullable=True))
    op.add_column("events", sa.Column("consent_text_version", sa.String(), nullable=True))
    op.add_column("events", sa.Column("channel", sa.String(), nullable=True))
    op.add_column("events", sa.Column("channel_target_ref", sa.String(), nullable=True))

    # ── terms ──
    op.add_column("terms", sa.Column("needs_review", sa.Boolean(), nullable=True))
    op.add_column("terms", sa.Column("is_superseded", sa.Boolean(), nullable=True))
    # Note: SQLite ALTER TABLE cannot add columns with FK constraints.
    # App code enforces referential integrity.
    op.add_column("terms", sa.Column("overrides_term_id", sa.Integer(), nullable=True))
    op.add_column("terms", sa.Column("inherited_from_doc_id", sa.Integer(), nullable=True))

    # ── obligations ──
    op.add_column("obligations", sa.Column("source_doc_chain", sa.Text(), nullable=True))
    op.add_column("obligations", sa.Column("resolution_method", sa.String(), nullable=True))

    # ── document_relationships (NEW) ──
    op.create_table(
        "document_relationships",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=False),
        sa.Column("from_doc_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("to_doc_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("unresolved_ref", sa.String(), nullable=True),
        sa.Column("relationship_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="pending"),
        sa.Column("confirmed_by_sme", sa.Boolean(), server_default="0"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_relationships_tenant_id", "document_relationships", ["tenant_id"])
    op.create_index("ix_document_relationships_from_doc_id", "document_relationships", ["from_doc_id"])
    op.create_index("ix_document_relationships_to_doc_id", "document_relationships", ["to_doc_id"])


def downgrade() -> None:
    op.drop_index("ix_document_relationships_to_doc_id", table_name="document_relationships")
    op.drop_index("ix_document_relationships_from_doc_id", table_name="document_relationships")
    op.drop_index("ix_document_relationships_tenant_id", table_name="document_relationships")
    op.drop_table("document_relationships")

    op.drop_column("obligations", "resolution_method")
    op.drop_column("obligations", "source_doc_chain")

    op.drop_column("terms", "inherited_from_doc_id")
    op.drop_column("terms", "overrides_term_id")
    op.drop_column("terms", "is_superseded")
    op.drop_column("terms", "needs_review")

    op.drop_column("events", "channel_target_ref")
    op.drop_column("events", "channel")
    op.drop_column("events", "consent_text_version")
    op.drop_column("events", "consent_reference")
    op.drop_column("events", "purpose")
