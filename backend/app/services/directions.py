"""Obligation direction re-derivation from stored data (DEC-030 / D-13, #238).

The DB-backed twin of ``extraction_runner._derive_direction``: it re-derives each
obligation's direction by auto-matching the tenant's configured ``legal_name``
(Settings — NOT a per-doc manual pick, per #238 PM ratify) against the stored
``parties`` rows. Used by ``POST /documents/{id}/confirm`` so direction reflects
the legal_name even if it was set after extraction.

D-13 conformance — direction is NULL (needs user review) when it can't be
auto-derived: no legal_name, no matching self-party, or no obligor.

#282 B1 hardening: matching is normalized (case-fold + diacritics-stripped +
whitespace-collapsed). Obligor is matched against both role_label AND party name
so LLMs emitting full company names as obligor are handled correctly.

#471 Q1 fix: Party.aliases (tenant_022/#364, JSON TEXT) are now included in the
match so abbreviated names stored as aliases are treated as self-party identifiers.
"""
from __future__ import annotations

import json
import unicodedata

from sqlalchemy.orm import Session

from app.models.tenant import Obligation, Party


def _norm(s: str) -> str:
    """Case-fold + strip diacritics + collapse whitespace for fuzzy comparison."""
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().split())


def _party_names(p: Party) -> list[str]:
    """All normalized name strings for a party: canonical name + aliases."""
    names = [p.name or ""]
    if p.aliases:
        try:
            parsed = json.loads(p.aliases) if isinstance(p.aliases, str) else p.aliases
            if isinstance(parsed, list):
                names.extend(str(a) for a in parsed if a)
        except (ValueError, TypeError):
            pass
    return [n for n in names if n]


def _self_party_strings(db: Session, tenant_id: str, doc_id: int, legal_name: str | None) -> set[str]:
    """Normalized identifiers (role_labels + party names + aliases) for the self-party.

    Empty when legal_name is unset or nothing matches (→ direction stays NULL).
    Normalized so diacritic variants in legal_name vs extracted party names compare
    correctly (B1 hardening, #282). Aliases included per #471 Q1 fix.
    """
    if not legal_name:
        return set()
    norm_ln = _norm(legal_name)
    result: set[str] = set()
    parties = (
        db.query(Party)
        .filter(Party.tenant_id == tenant_id, Party.document_id == doc_id)
        .all()
    )
    for p in parties:
        all_names = _party_names(p)
        matched = any(
            norm_nm and (norm_ln in norm_nm or norm_nm in norm_ln)
            for norm_nm in (_norm(n) for n in all_names)
        )
        if matched:
            if p.role_label:
                result.add(_norm(p.role_label))
            for n in all_names:
                result.add(_norm(n))
    return result


def rederive_document_directions(
    db: Session, tenant_id: str, doc_id: int, legal_name: str | None
) -> int:
    """Recompute direction for every obligation of a document. Returns # changed.

    nghĩa_vụ if obligor (normalized) matches a self-party identifier; quyền_lợi
    if obligor is present but doesn't match; NULL otherwise (no obligor / no
    legal_name / no self-party match). Does NOT commit — caller owns transaction.
    """
    self_strings = _self_party_strings(db, tenant_id, doc_id, legal_name)
    obligations = (
        db.query(Obligation)
        .filter(Obligation.tenant_id == tenant_id, Obligation.document_id == doc_id)
        .all()
    )
    updated = 0
    for ob in obligations:
        if not ob.obligor or not self_strings:
            new_dir = None
        else:
            new_dir = "nghĩa_vụ" if _norm(ob.obligor) in self_strings else "quyền_lợi"
        if ob.direction != new_dir:
            ob.direction = new_dir
            updated += 1
    return updated
