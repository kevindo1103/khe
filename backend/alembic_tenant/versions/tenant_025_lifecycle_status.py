"""tenant_025: contract term + lifecycle status on documents (#371)."""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "tenant_025"
down_revision: Union[str, None] = "tenant_024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    if "contract_term" not in cols:
        op.add_column("documents", sa.Column("contract_term", sa.String(), nullable=True))
    if "lifecycle_status" not in cols:
        op.add_column("documents", sa.Column("lifecycle_status", sa.String(), nullable=True))


def downgrade() -> None:
    pass
