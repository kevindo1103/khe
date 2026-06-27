"""Obligation derivation engine (PR-A of #26).

Derives actionable obligations from extracted terms. Chain-aware: uses the
connected amends chain from `relationships._build_connected_chain` so the
latest amendment's terms win over older versions.

Rules:
- If `ngay_het_han` is present → one-time obligation, due_date = ngay_het_han.
- Else if `ngay_hieu_luc` and numeric `thoi_han_hd` are present → derive
  due_date = ngay_hieu_luc + thoi_han_hd, one-time obligation.
- Else if `thoi_han_hd` is non-numeric/open-ended → open_ended_review,
  due_date = NULL.
- Else insufficient data → skip (D-08: never fabricate).

Idempotency: only deletes existing obligations with status="pending";
"done" / "cancelled" obligations are preserved (D-02 — respect SME edits).
"""
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.tenant import Document, Event, Obligation, Term
from app.services.date_parse import add_months, parse_date, parse_duration_months
from app.services.relationships import _build_connected_chain, _get_confirmed_amends_edges


# Fields relevant to obligation derivation.
_DUE_FIELD = "ngay_het_han"
_START_FIELD = "ngay_hieu_luc"
_DURATION_FIELD = "thoi_han_hd"


def _winning_term(
    db: Session,
    tenant_id: str,
    chain_docs: list[Document],
    field_name: str,
) -> "Term | None":
    """Return the effective Term object for a field in the chain.

    Chain docs are ordered base → amendment. The last non-superseded term
    wins (chain resolution already marked older terms as superseded).
    """
    chain_ids = [d.id for d in chain_docs]
    if not chain_ids:
        return None

    terms = (
        db.query(Term)
        .filter(
            Term.tenant_id == tenant_id,
            Term.document_id.in_(chain_ids),
            Term.field_name == field_name,
            Term.field_value.isnot(None),
            Term.is_superseded == False,
        )
        .all()
    )

    order = {doc_id: idx for idx, doc_id in enumerate(chain_ids)}
    terms_sorted = sorted(terms, key=lambda t: order.get(t.document_id, 0))
    return terms_sorted[-1] if terms_sorted else None


def _winning_term_value(
    db: Session,
    tenant_id: str,
    chain_docs: list[Document],
    field_name: str,
) -> str | None:
    """Return the effective value of a field in the chain (value-only shortcut)."""
    t = _winning_term(db, tenant_id, chain_docs, field_name)
    return t.field_value if t else None


def _build_chain_docs(
    db: Session,
    tenant_id: str,
    doc_id: int,
) -> list[Document]:
    """Return the connected amends chain for a document, or just the document."""
    edges = _get_confirmed_amends_edges(db, tenant_id)
    chain = _build_connected_chain(db, tenant_id, doc_id, edges)
    if chain:
        return chain
    # No chain: return the single document in a list.
    doc = db.query(Document).filter(Document.id == doc_id, Document.tenant_id == tenant_id).first()
    return [doc] if doc else []


def derive_obligations(db: Session, tenant_id: str, doc_id: int, *, source_label: str = "ai_extracted") -> dict:
    """Derive obligations for a document.

    Notes:
    - If `ngay_het_han` is present but unparseable, we skip rather than falling
      back to `ngay_hieu_luc + thoi_han_hd`. This follows the literal priority
      in SRS §6.1; revisit if PM wants fallback behavior.
    - For multi-parent chains (one doc amends multiple parents), the chain order
      is depth-sorted and the last non-superseded term wins — deterministic but
      arbitrary when parent terms conflict. This is the seam for the Sprint-2
      conflict UI (DEC-022).

    Returns metadata: {"created": int, "skipped": bool, "reason": str}.
    """
    chain_docs = _build_chain_docs(db, tenant_id, doc_id)
    if not chain_docs:
        return {"created": 0, "skipped": True, "reason": "Document not found"}

    chain_ids = [d.id for d in chain_docs]
    target_doc = chain_docs[-1]  # The amendment (or single doc) is the focal doc.

    due_term = _winning_term(db, tenant_id, chain_docs, _DUE_FIELD)
    start_term = _winning_term(db, tenant_id, chain_docs, _START_FIELD)
    duration_term = _winning_term(db, tenant_id, chain_docs, _DURATION_FIELD)

    due_value = due_term.field_value if due_term else None
    start_value = start_term.field_value if start_term else None
    duration_value = duration_term.field_value if duration_term else None

    due_date: datetime | None = None
    recurrence = "once"
    skip_reason: str | None = None

    if due_value:
        due_date = parse_date(due_value)
        if due_date is None:
            skip_reason = f"Unparseable due date: {due_value!r}"
    elif start_value and duration_value:
        start_date = parse_date(start_value)
        duration_months = parse_duration_months(duration_value)
        if start_date is None:
            skip_reason = f"Unparseable start date: {start_value!r}"
        elif duration_months is None:
            # Non-numeric duration → open-ended review.
            recurrence = "open_ended_review"
            due_date = None
        else:
            due_date = add_months(start_date, duration_months)
    else:
        skip_reason = "Insufficient data for obligation derivation"

    if skip_reason:
        return {"created": 0, "skipped": True, "reason": skip_reason}

    # Description in Vietnamese.
    if recurrence == "open_ended_review":
        description = f"Hợp đồng {target_doc.file_name} vô thời hạn — cần review"
    else:
        due_str = due_date.strftime("%Y-%m-%d") if due_date else None
        description = f"Hợp đồng {target_doc.file_name} hết hạn ngày {due_str}"

    # The obligation belongs to the terminal (newest amendment) document in the
    # chain, not whichever doc_id triggered the derivation. Clear pending
    # obligations on ALL chain docs so stale parent obligations disappear after a
    # chain is confirmed.
    target_doc_id = chain_docs[-1].id
    db.query(Obligation).filter(
        Obligation.tenant_id == tenant_id,
        Obligation.document_id.in_(chain_ids),
        Obligation.status == "pending",
        Obligation.source != "user_manual",
        Obligation.fulfilled_at.is_(None),
    ).delete()

    due_str = due_date.strftime("%Y-%m-%d") if due_date else None
    # Clause provenance (#303): anchor to the clause that provided the winning date field.
    source_clause_num = (
        (due_term.ref if due_term else None)
        or (start_term.ref if start_term else None)
    )
    ob = Obligation(
        tenant_id=tenant_id,
        document_id=target_doc_id,
        description=description,
        recurrence=recurrence,
        obligation_type="expiration",
        due_date=due_str,
        status="pending",
        # DEC-020: open_ended_review = annual review nudge, 365d window.
        # `once` (default) = 30d before a real deadline.
        remind_before_days=365 if recurrence == "open_ended_review" else 30,
        source_doc_chain=json.dumps(chain_ids),
        resolution_method="last_writer_wins" if len(chain_ids) > 1 else None,
        source=source_label,
        source_clause_num=source_clause_num,
        derived_from="original",
    )
    db.add(ob)

    event = Event(
        tenant_id=tenant_id,
        event_type="obligation_derived",
        entity_type="document",
        entity_id=target_doc_id,
        actor="system",
        purpose=None,
        payload=json.dumps(
            {
                "recurrence": recurrence,
                "obligation_type": "expiration",
                "due_date": due_str,
                "chain_doc_ids": chain_ids,
                "resolution_method": ob.resolution_method,
            }
        ),
    )
    db.add(event)

    db.commit()
    return {"created": 1, "skipped": False, "reason": None}


def derive_obligation_from_clause(
    db: Session,
    tenant_id: str,
    doc_id: int,
    clause_num: str,
    *,
    source_label: str = "ai_re_derived",
    derived_from: str = "original",
) -> dict:
    """Derive an obligation using only Terms anchored to a specific clause (#303).

    Scoped re-derive: only Terms where ``ref == clause_num`` are used. Does NOT
    delete other obligations or touch other clauses (KHÔNG churn — AC2 §303).
    Does NOT resolve across amendment chains — operates on this document only.

    Returns ``{"created": int, "skipped": bool, "reason": str | None}``.
    """
    # Fetch Terms scoped to this clause and doc.
    clause_terms = (
        db.query(Term)
        .filter(
            Term.tenant_id == tenant_id,
            Term.document_id == doc_id,
            Term.ref == clause_num,
            Term.field_value.isnot(None),
            Term.is_superseded == False,
        )
        .all()
    )

    term_map: dict[str, Term] = {}
    for t in clause_terms:
        # Last-write-wins when multiple terms share field_name + clause (edge case).
        if t.field_name not in term_map or t.id > term_map[t.field_name].id:
            term_map[t.field_name] = t

    due_term = term_map.get(_DUE_FIELD)
    start_term = term_map.get(_START_FIELD)
    duration_term = term_map.get(_DURATION_FIELD)

    due_value = due_term.field_value if due_term else None
    start_value = start_term.field_value if start_term else None
    duration_value = duration_term.field_value if duration_term else None

    due_date: "datetime | None" = None
    recurrence = "once"
    skip_reason: str | None = None

    if due_value:
        due_date = parse_date(due_value)
        if due_date is None:
            skip_reason = f"Unparseable due date: {due_value!r}"
    elif start_value and duration_value:
        start_date = parse_date(start_value)
        duration_months = parse_duration_months(duration_value)
        if start_date is None:
            skip_reason = f"Unparseable start date: {start_value!r}"
        elif duration_months is None:
            recurrence = "open_ended_review"
        else:
            due_date = add_months(start_date, duration_months)
    else:
        skip_reason = "Insufficient clause-scoped data for obligation derivation"

    if skip_reason:
        return {"created": 0, "skipped": True, "reason": skip_reason}

    doc = db.query(Document).filter(Document.id == doc_id, Document.tenant_id == tenant_id).first()
    file_name = doc.file_name if doc else f"doc#{doc_id}"

    due_str = due_date.strftime("%Y-%m-%d") if due_date else None
    if recurrence == "open_ended_review":
        description = f"Hợp đồng {file_name} vô thời hạn — cần review"
    else:
        description = f"Hợp đồng {file_name} hết hạn ngày {due_str}"

    ob = Obligation(
        tenant_id=tenant_id,
        document_id=doc_id,
        description=description,
        recurrence=recurrence,
        obligation_type="expiration",
        due_date=due_str,
        status="pending",
        remind_before_days=365 if recurrence == "open_ended_review" else 30,
        source=source_label,
        source_clause_num=clause_num,
        derived_from=derived_from,
    )
    db.add(ob)

    db.add(Event(
        tenant_id=tenant_id,
        event_type="obligation_derived",
        entity_type="document",
        entity_id=doc_id,
        actor="system",
        purpose=None,
        payload=json.dumps({
            "recurrence": recurrence,
            "obligation_type": "expiration",
            "due_date": due_str,
            "source_clause_num": clause_num,
        }),
    ))

    db.commit()
    return {"created": 1, "skipped": False, "reason": None}
