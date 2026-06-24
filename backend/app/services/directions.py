"""Obligation direction re-derivation from stored data (DEC-030 / D-13, #238).

The DB-backed twin of ``extraction_runner._derive_direction``: it re-derives each
obligation's direction by auto-matching the tenant's configured ``legal_name``
(Settings — NOT a per-doc manual pick, per #238 PM ratify) against the stored
``parties`` rows. Used by ``POST /documents/{id}/confirm`` so direction reflects
the legal_name even if it was set after extraction.

D-13 conformance — direction is NULL (needs user review) when it can't be
auto-derived: no legal_name, no matching self-party, or no obligor.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.tenant import Obligation, Party


def _self_role_labels(db: Session, tenant_id: str, doc_id: int, legal_name: str | None) -> set[str]:
    """Role labels of the document's parties whose name fuzzy-matches legal_name.

    Empty when legal_name is unset or nothing matches (→ direction stays NULL).
    """
    if not legal_name:
        return set()
    ln = legal_name.lower()
    roles: set[str] = set()
    parties = (
        db.query(Party)
        .filter(Party.tenant_id == tenant_id, Party.document_id == doc_id)
        .all()
    )
    for p in parties:
        nm = (p.name or "").lower()
        if nm and (ln in nm or nm in ln):
            if p.role_label:
                roles.add(p.role_label)
    return roles


def rederive_document_directions(
    db: Session, tenant_id: str, doc_id: int, legal_name: str | None
) -> int:
    """Recompute direction for every obligation of a document. Returns # changed.

    nghĩa_vụ if obligor is the self-party role; quyền_lợi if obligor is another
    party; NULL otherwise (no obligor / no legal_name / no self-party match).
    Mirrors extraction-time derivation so confirm is idempotent with it.
    Does NOT commit — the caller owns the transaction.
    """
    self_roles = _self_role_labels(db, tenant_id, doc_id, legal_name)
    obligations = (
        db.query(Obligation)
        .filter(Obligation.tenant_id == tenant_id, Obligation.document_id == doc_id)
        .all()
    )
    updated = 0
    for ob in obligations:
        if not ob.obligor or not self_roles:
            new_dir = None
        else:
            new_dir = "nghĩa_vụ" if ob.obligor in self_roles else "quyền_lợi"
        if ob.direction != new_dir:
            ob.direction = new_dir
            updated += 1
    return updated
