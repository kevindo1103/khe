"""tenant_016 — fulfillment capture + evidence doc columns (#302, DEC-048)

Revision ID: tenant_016
Revises: tenant_015
Create Date: 2026-06-26 22:00:00.000000

Adds:
  obligations.fulfilled_at  — authoritative completion date (G2/T2)
  obligations.fulfilled_by  — actor: username or "operator-for-<username>" (P3)
  obligations.evidence_doc_ids — JSON list of evidence document IDs
  documents.is_evidence     — P2: skip full vision extraction for biên bản
  documents.contains_personal_data — DEC-039 firm-gate guard (conservative default)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_016"
down_revision: Union[str, None] = "tenant_015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    obl_cols = {c["name"] for c in sa.inspect(conn).get_columns("obligations")}
    if "fulfilled_at" not in obl_cols:
        op.add_column("obligations", sa.Column("fulfilled_at", sa.DateTime(), nullable=True))
    if "fulfilled_by" not in obl_cols:
        op.add_column("obligations", sa.Column("fulfilled_by", sa.String(), nullable=True))
    if "evidence_doc_ids" not in obl_cols:
        op.add_column("obligations", sa.Column("evidence_doc_ids", sa.Text(), nullable=True))

    doc_cols = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    if "is_evidence" not in doc_cols:
        op.add_column("documents", sa.Column("is_evidence", sa.Boolean(), nullable=True, server_default="0"))
    if "contains_personal_data" not in doc_cols:
        op.add_column("documents", sa.Column("contains_personal_data", sa.Boolean(), nullable=True, server_default="0"))


def downgrade() -> None:
    conn = op.get_bind()

    obl_cols = {c["name"] for c in sa.inspect(conn).get_columns("obligations")}
    for col in ("fulfilled_at", "fulfilled_by", "evidence_doc_ids"):
        if col in obl_cols:
            op.drop_column("obligations", col)

    doc_cols = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    for col in ("is_evidence", "contains_personal_data"):
        if col in doc_cols:
            op.drop_column("documents", col)
