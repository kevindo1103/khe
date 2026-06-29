"""003 — journey_stage + is_first_session on tenants (#213)

Revision ID: 003
Revises: 002
Create Date: 2026-06-23 16:30:00.000000

Onboarding journey state machine (monotonic forward-only):
NEW → EXTRACTING → NEEDS_REVIEW → CONFIRMED → ACTIVATED → STEADY.
Frontend uses these for nav-lock (first-session only) + home = f(stage) routing.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("tenants")}

    if "journey_stage" not in cols:
        op.add_column(
            "tenants",
            sa.Column("journey_stage", sa.String(), nullable=False, server_default="NEW"),
        )
    if "is_first_session" not in cols:
        op.add_column(
            "tenants",
            sa.Column("is_first_session", sa.Boolean(), nullable=False, server_default="1"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in sa.inspect(bind).get_columns("tenants")}

    if "is_first_session" in cols:
        op.drop_column("tenants", "is_first_session")
    if "journey_stage" in cols:
        op.drop_column("tenants", "journey_stage")
