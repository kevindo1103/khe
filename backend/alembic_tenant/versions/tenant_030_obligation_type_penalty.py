"""tenant_030: add 'penalty' to obligation_type enum (#471, DEC-027).

obligation_type is a TEXT column with no DB-level CHECK constraint — the enum
is enforced in application code. This migration is a no-op in SQLite (no ALTER
needed) but anchors the enum extension in the alembic chain so the change is
visible to migrate_all_tenants.py and reviewers.
"""
from __future__ import annotations

from typing import Union

revision: str = "tenant_030"
down_revision: Union[str, None] = "tenant_029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # obligation_type is TEXT — no schema change needed.
    # Anchor only: 'penalty' is now a valid obligation_type value alongside
    # payment/delivery/handover/expiration/renewal/review/warranty/other.
    pass


def downgrade() -> None:
    pass
