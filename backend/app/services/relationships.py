"""Relationship + chain-resolution service (DEC-019/020/021, PR-B of tenant_002).

This module contains only logic — the schema already landed in the tenant_002
migration (PR-A).  It never creates obligations; it produces chain metadata that
the obligation engine (#26) will consume.
"""
import json
import re
from typing import Iterable

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.tenant import Document, DocumentRelationship, Obligation, Term

# MVP relationship types; "supersedes" / "renews" / "related" are Sprint 2.
VALID_RELATIONSHIP_TYPES = {"amends", "references_framework"}

# Heuristic patterns to extract contract references from term values.
# Captures a reference token like "123", "A-2024", "HD-001".
_REFERENCE_PATTERNS = [
    re.compile(
        r"(?:HĐ|HD|hợp đồng|Hợp đồng)\s*(?:số|so|#)?\s*([A-Za-z0-9\-]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:phụ lục|Phụ lục|phu luc|Phu luc)\s*(?:HĐ|HD)?\s*(?:số|so|#)?\s*([A-Za-z0-9\-]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:theo|căn cứ|căn_cứ)\s+(?:HĐ|HD|hợp đồng|Hợp đồng)\s*(?:số|so|#)?\s*([A-Za-z0-9\-]+)",
        re.IGNORECASE,
    ),
]


def _extract_reference_hints(text: str | None) -> set[str]:
    """Return a set of plausible contract reference tokens from free text."""
    if not text:
        return set()
    hints: set[str] = set()
    for pattern in _REFERENCE_PATTERNS:
        for match in pattern.finditer(text):
            token = match.group(1).strip("-_.")
            if token and len(token) >= 2:
                hints.add(token.lower())
    return hints


def _find_matching_document(db: Session, tenant_id: str, hint: str) -> Document | None:
    """Try to match a reference hint to an in-tenant document.

    Matching is intentionally conservative: only file_name contains the hint.
    """
    if not hint:
        return None
    return (
        db.query(Document)
        .filter(
            Document.tenant_id == tenant_id,
            Document.file_name.ilike(f"%{hint}%"),
        )
        .first()
    )


def _relationship_exists(
    db: Session,
    tenant_id: str,
    from_doc_id: int,
    to_doc_id: int | None,
    unresolved_ref: str | None,
    rel_type: str,
) -> bool:
    """Avoid duplicate relationship suggestions."""
    query = db.query(DocumentRelationship).filter(
        DocumentRelationship.tenant_id == tenant_id,
        DocumentRelationship.from_doc_id == from_doc_id,
        DocumentRelationship.relationship_type == rel_type,
    )
    if to_doc_id is not None:
        query = query.filter(DocumentRelationship.to_doc_id == to_doc_id)
    else:
        query = query.filter(
            DocumentRelationship.to_doc_id.is_(None),
            DocumentRelationship.unresolved_ref == unresolved_ref,
        )
    return query.first() is not None


def _build_relationship(
    db: Session,
    tenant_id: str,
    from_doc_id: int,
    hint: str,
    rel_type: str,
    confidence: float,
) -> DocumentRelationship:
    """Create a relationship (linked or orphan) for a single hint."""
    matched_doc = _find_matching_document(db, tenant_id, hint)
    if matched_doc is not None and matched_doc.id == from_doc_id:
        # A document should not reference itself.
        matched_doc = None

    to_doc_id = matched_doc.id if matched_doc else None
    unresolved_ref = None if matched_doc else hint

    if _relationship_exists(
        db, tenant_id, from_doc_id, to_doc_id, unresolved_ref, rel_type
    ):
        # Already suggested; return the existing one.
        existing = (
            db.query(DocumentRelationship)
            .filter(
                DocumentRelationship.tenant_id == tenant_id,
                DocumentRelationship.from_doc_id == from_doc_id,
                DocumentRelationship.relationship_type == rel_type,
                DocumentRelationship.to_doc_id == to_doc_id,
                DocumentRelationship.unresolved_ref == unresolved_ref,
            )
            .first()
        )
        return existing

    rel = DocumentRelationship(
        tenant_id=tenant_id,
        from_doc_id=from_doc_id,
        to_doc_id=to_doc_id,
        unresolved_ref=unresolved_ref,
        relationship_type=rel_type,
        status="pending",
        confirmed_by_sme=False,
        confidence=confidence,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel


def suggest_relationships(
    db: Session,
    tenant_id: str,
    document_id: int,
    rel_type: str = "amends",
) -> list[DocumentRelationship]:
    """Scan a document's terms and create relationship suggestions.

    - If a referenced contract exists in the tenant, link it (`to_doc_id`).
    - Otherwise, create an orphan amendment (`to_doc_id=None`, `unresolved_ref`).
    - All suggestions are `pending` and `confirmed_by_sme=False` (D-02 gate).
    - Returns only the relationships created (or already present) for this call.
    """
    if rel_type not in VALID_RELATIONSHIP_TYPES:
        raise ValueError(f"Invalid relationship_type: {rel_type}")

    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.tenant_id == tenant_id)
        .first()
    )
    if doc is None:
        return []

    terms = (
        db.query(Term)
        .filter(Term.document_id == document_id, Term.tenant_id == tenant_id)
        .all()
    )

    hints: set[str] = set()
    for term in terms:
        if term.field_value:
            hints.update(_extract_reference_hints(term.field_value))
        # Also scan field_name for structural references (e.g. "dieu_khoan_*").
        if term.field_name:
            hints.update(_extract_reference_hints(term.field_name))

    # Also scan the document file_name for embedded references.
    hints.update(_extract_reference_hints(doc.file_name))

    created: list[DocumentRelationship] = []
    for hint in hints:
        confidence = 0.7  # heuristic baseline
        rel = _build_relationship(db, tenant_id, document_id, hint, rel_type, confidence)
        if rel:
            created.append(rel)

    return created


def late_link_orphans(
    db: Session,
    tenant_id: str,
    new_document: Document,
) -> list[DocumentRelationship]:
    """When a new document arrives, try to resolve existing orphan edges.

    Orphans are relationships with `to_doc_id IS NULL` and `unresolved_ref` set.
    If `unresolved_ref` matches the new document's file_name, set `to_doc_id`.
    Status remains `pending` until SME confirms (D-02).
    """
    file_name = (new_document.file_name or "").lower()
    hints = _extract_reference_hints(new_document.file_name)

    orphans = (
        db.query(DocumentRelationship)
        .filter(
            DocumentRelationship.tenant_id == tenant_id,
            DocumentRelationship.to_doc_id.is_(None),
            DocumentRelationship.status == "pending",
        )
        .all()
    )

    updated: list[DocumentRelationship] = []
    for orphan in orphans:
        if not orphan.unresolved_ref:
            continue
        ref = orphan.unresolved_ref.lower()
        # Match if the unresolved_ref is contained in the file_name, or an
        # extracted hint from the file_name is contained in the unresolved_ref.
        matches = (
            ref in file_name
            or file_name in ref
            or any(h in ref for h in hints)
        )
        if matches:
            # Avoid self-reference.
            if orphan.from_doc_id != new_document.id:
                orphan.to_doc_id = new_document.id
                db.commit()
                db.refresh(orphan)
                updated.append(orphan)

    return updated


def _get_confirmed_amends_edges(db: Session, tenant_id: str) -> list[DocumentRelationship]:
    """Return all confirmed amends edges for a tenant."""
    return (
        db.query(DocumentRelationship)
        .filter(
            DocumentRelationship.tenant_id == tenant_id,
            DocumentRelationship.relationship_type == "amends",
            DocumentRelationship.status == "confirmed",
            DocumentRelationship.confirmed_by_sme == True,
        )
        .all()
    )


def _build_connected_chain(
    db: Session,
    tenant_id: str,
    start_doc_id: int,
    edges: list[DocumentRelationship],
) -> list[Document]:
    """Build the connected component of confirmed amends edges containing start_doc_id.

    Returns documents sorted oldest-first (by created_at, then id).
    """
    edge_map: dict[int, int] = {}
    for edge in edges:
        edge_map[edge.from_doc_id] = edge.to_doc_id

    # Collect all doc IDs in the connected chain.
    seen: set[int] = set()
    stack = [start_doc_id]
    while stack:
        current_id = stack.pop()
        if current_id in seen or current_id is None:
            continue
        seen.add(current_id)
        # A -> B means A amends B.  So B is the parent.
        if current_id in edge_map:
            stack.append(edge_map[current_id])
        # Find children (documents that amend current_id).
        for child_id, parent_id in edge_map.items():
            if parent_id == current_id:
                stack.append(child_id)

    if not seen:
        return []

    docs = (
        db.query(Document)
        .filter(
            Document.tenant_id == tenant_id,
            Document.id.in_(list(seen)),
        )
        .order_by(Document.created_at.asc(), Document.id.asc())
        .all()
    )
    return docs


def resolve_chain(
    db: Session,
    tenant_id: str,
    document_id: int,
) -> dict:
    """Resolve term overrides / supersede and build chain metadata.

    - Only acts on confirmed `amends` edges (confirmed_by_sme=True).
    - For overlapping field_names, older terms become `is_superseded=True`;
      newer terms get `overrides_term_id` and `inherited_from_doc_id`.
    - Updates existing obligations' `source_doc_chain` + `resolution_method`
      (does not create obligations).
    - Returns chain metadata: {doc_ids, terms_resolved, obligations_updated}.
    """
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.tenant_id == tenant_id)
        .first()
    )
    if doc is None:
        return {"doc_ids": [], "terms_resolved": 0, "obligations_updated": 0}

    edges = _get_confirmed_amends_edges(db, tenant_id)
    chain_docs = _build_connected_chain(db, tenant_id, document_id, edges)
    chain_ids = [d.id for d in chain_docs]

    if len(chain_docs) < 2:
        return {"doc_ids": chain_ids, "terms_resolved": 0, "obligations_updated": 0}

    # Collect the latest term per field_name for each document in the chain.
    # Chain is oldest -> newest.  Resolve from oldest to newest: each newer term
    # overrides the previous one for the same field_name.
    latest_by_field: dict[str, Term] = {}
    terms_resolved = 0

    for current_doc in chain_docs:
        terms = (
            db.query(Term)
            .filter(
                Term.document_id == current_doc.id,
                Term.tenant_id == tenant_id,
                Term.is_superseded == False,
            )
            .all()
        )
        for term in terms:
            prev_term = latest_by_field.get(term.field_name)
            if prev_term is not None:
                # Newer term overrides older term.
                term.overrides_term_id = prev_term.id
                term.inherited_from_doc_id = prev_term.document_id
                prev_term.is_superseded = True
                terms_resolved += 1
                db.add(prev_term)
            latest_by_field[term.field_name] = term
            db.add(term)

    db.commit()

    # Update source_doc_chain / resolution_method on existing obligations in the chain.
    obligations_updated = 0
    if chain_ids:
        obligations = (
            db.query(Obligation)
            .filter(
                Obligation.tenant_id == tenant_id,
                Obligation.document_id.in_(chain_ids),
            )
            .all()
        )
        for ob in obligations:
            ob.source_doc_chain = json.dumps(chain_ids)
            ob.resolution_method = "last_writer_wins"
            db.add(ob)
            obligations_updated += 1
        db.commit()

    return {
        "doc_ids": chain_ids,
        "terms_resolved": terms_resolved,
        "obligations_updated": obligations_updated,
    }


def get_relationships_for_document(
    db: Session,
    tenant_id: str,
    document_id: int,
) -> list[DocumentRelationship]:
    """Return relationships where the document is either source or target."""
    return (
        db.query(DocumentRelationship)
        .filter(
            DocumentRelationship.tenant_id == tenant_id,
            or_(
                DocumentRelationship.from_doc_id == document_id,
                DocumentRelationship.to_doc_id == document_id,
            ),
        )
        .order_by(DocumentRelationship.created_at.desc())
        .all()
    )


def confirm_relationship(
    db: Session,
    tenant_id: str,
    document_id: int,
    rel_id: int,
    actor: str,
) -> DocumentRelationship | None:
    """SME confirms a relationship.  Triggers chain resolution.

    Returns the confirmed relationship, or None if not found / not accessible.
    """
    rel = (
        db.query(DocumentRelationship)
        .filter(
            DocumentRelationship.id == rel_id,
            DocumentRelationship.tenant_id == tenant_id,
            or_(
                DocumentRelationship.from_doc_id == document_id,
                DocumentRelationship.to_doc_id == document_id,
            ),
        )
        .first()
    )
    if rel is None:
        return None

    rel.confirmed_by_sme = True
    rel.status = "confirmed"
    db.commit()
    db.refresh(rel)

    # Trigger chain resolution for the source document.
    resolve_chain(db, tenant_id, rel.from_doc_id)

    return rel
