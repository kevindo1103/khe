"""tenant_024: date taxonomy — signing_date + commencement_date on documents (#369)."""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "tenant_024"
down_revision: Union[str, None] = "tenant_023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    if "signing_date" not in cols:
        op.add_column("documents", sa.Column("signing_date", sa.String(), nullable=True))
    if "commencement_date" not in cols:
        op.add_column("documents", sa.Column("commencement_date", sa.String(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    cols = {c["name"] for c in sa.inspect(conn).get_columns("documents")}
    for col in ("signing_date", "commencement_date"):
        if col in cols:
            op.drop_column("documents", col)
