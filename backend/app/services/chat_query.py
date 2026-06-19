"""Chat query MVP — retrieve-only answer engine (#27).

- D-06: returns only extracted fields, never generates or interprets legal content.
- D-08: returns a fixed "not found" message when no reliable match is found.
- Tenant-scoped: only searches within the caller's tenant.

MVP intent: "hợp đồng [X] hết hạn khi nào?" -> reads Obligation.due_date
(derived from Term ngay_het_han). Sprint 2+ adds semantic search.
"""
from __future__ import annotations

import re
from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.tenant import Document, Obligation, Term


_NOT_FOUND = "Không tìm thấy thông tin này trong hồ sơ của bạn."


def _normalize(text: str) -> str:
    return text.lower().strip()


def _extract_doc_hint(question: str) -> str | None:
    """Try to extract a document name/reference from the question.

    Handles: 'hợp đồng X', 'hợp đồng số X', quoted strings, bare file-name tokens.
    """
    text = _normalize(question)

    # Quoted text
    quoted = re.findall(r'["“”]([^"“”]+)["“”]', question)
    if quoted:
        return quoted[0].strip()

    # "hợp đồng (số) X" / "hop dong X" / "hđ X"
    # Capture a single filename-like token (stops before the first Vietnamese word).
    patterns = [
        r"(?:hợp đồng|hợp_đồng|hop dong|hop_dong|hđ|hd|hợpđồng)\s*(?:số|so)?\s*[:\-]?\s*([a-z0-9\-_\.]+)",
        r"(?:hợp đồng|hợp_đồng|hop dong|hop_dong|hđ|hd|hợpđồng)\s*(?:tên|ten|file)?\s*[:\-]?\s*([a-z0-9\-_\.]+)",
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            hint = match.group(1).strip()
            if len(hint) >= 2:
                return hint

    return None


def _detect_intent(question: str) -> str:
    """Detect the user's intent from keyword patterns.

    MVP intents: expiry, start_date, duration, parties, status.
    """
    text = _normalize(question)
    # Expiry must be explicit (avoid matching "thời hạn" which contains "hạn").
    if re.search(r"hết hạn|het han|đáo hạn|dao han|expir|due date|ngày hết hạn", text):
        return "expiry"
    if re.search(r"hiệu lực|hieu luc|có hiệu lực|bat dau|bắt đầu|start|có hiệu lực từ", text):
        return "start_date"
    if re.search(r"thời hạn hợp đồng|thời hạn|thoi han|duration|kéo dài|bao lâu", text):
        return "duration"
    if re.search(r"đối tác|doi tac|bên|bên thuê|bên cho thuê|parties|partner", text):
        return "parties"
    if re.search(r"trạng thái|trang thai|status|tình trạng", text):
        return "status"
    return "unknown"


def _find_document_by_hint(db: Session, tenant_id: str, hint: str) -> Document | None:
    """Search for a document whose file_name contains the hint."""
    if not hint or len(hint) < 2:
        return None

    # Exact-ish first
    doc = (
        db.query(Document)
        .filter(
            Document.tenant_id == tenant_id,
            Document.file_name.ilike(hint),
        )
        .order_by(Document.created_at.desc())
        .first()
    )
    if doc:
        return doc

    # Substring — deterministic "most recent match".
    return (
        db.query(Document)
        .filter(
            Document.tenant_id == tenant_id,
            Document.file_name.ilike(f"%{hint}%"),
        )
        .order_by(Document.created_at.desc())
        .first()
    )


def _count_extracted_documents(db: Session, tenant_id: str) -> int:
    """Return the number of extracted documents for the tenant."""
    return (
        db.query(Document)
        .filter(
            Document.tenant_id == tenant_id,
            Document.status == "extracted",
        )
        .count()
    )


def _find_document_without_hint(db: Session, tenant_id: str) -> Document | None:
    """Fallback: only safe when the tenant has exactly one extracted document.

    D-08: if multiple documents exist and none is named, we must not guess which
    document the user means.
    """
    if _count_extracted_documents(db, tenant_id) != 1:
        return None

    return (
        db.query(Document)
        .filter(
            Document.tenant_id == tenant_id,
            Document.status == "extracted",
        )
        .order_by(Document.created_at.desc())
        .first()
    )


def _answer_expiry(db: Session, tenant_id: str, doc: Document) -> tuple[str, list[dict]]:
    """Answer expiry intent using the document's obligation (derived from ngay_het_han)."""
    ob = (
        db.query(Obligation)
        .filter(
            Obligation.tenant_id == tenant_id,
            Obligation.document_id == doc.id,
            Obligation.status.in_(["pending", "overdue"]),
        )
        .order_by(Obligation.created_at.desc())
        .first()
    )
    if ob and ob.due_date:
        return (
            f"Hợp đồng {doc.file_name} hết hạn ngày {ob.due_date}.",
            [
                {
                    "type": "obligation",
                    "document_id": doc.id,
                    "file_name": doc.file_name,
                    "field_name": "due_date",
                    "value": ob.due_date,
                }
            ],
        )

    # Fallback to term if obligation missing.
    term = (
        db.query(Term)
        .filter(
            Term.tenant_id == tenant_id,
            Term.document_id == doc.id,
            Term.field_name == "ngay_het_han",
            Term.is_superseded == False,
        )
        .order_by(Term.created_at.desc())
        .first()
    )
    if term and term.field_value:
        return (
            f"Hợp đồng {doc.file_name} hết hạn ngày {term.field_value}.",
            [
                {
                    "type": "term",
                    "document_id": doc.id,
                    "file_name": doc.file_name,
                    "field_name": "ngay_het_han",
                    "value": term.field_value,
                }
            ],
        )

    return _NOT_FOUND, []


def _answer_start_date(db: Session, tenant_id: str, doc: Document) -> tuple[str, list[dict]]:
    term = (
        db.query(Term)
        .filter(
            Term.tenant_id == tenant_id,
            Term.document_id == doc.id,
            Term.field_name == "ngay_hieu_luc",
            Term.is_superseded == False,
        )
        .order_by(Term.created_at.desc())
        .first()
    )
    if term and term.field_value:
        return (
            f"Hợp đồng {doc.file_name} có hiệu lực từ ngày {term.field_value}.",
            [
                {
                    "type": "term",
                    "document_id": doc.id,
                    "file_name": doc.file_name,
                    "field_name": "ngay_hieu_luc",
                    "value": term.field_value,
                }
            ],
        )
    return _NOT_FOUND, []


def _answer_duration(db: Session, tenant_id: str, doc: Document) -> tuple[str, list[dict]]:
    term = (
        db.query(Term)
        .filter(
            Term.tenant_id == tenant_id,
            Term.document_id == doc.id,
            Term.field_name == "thoi_han_hd",
            Term.is_superseded == False,
        )
        .order_by(Term.created_at.desc())
        .first()
    )
    if term and term.field_value:
        return (
            f"Thời hạn hợp đồng {doc.file_name}: {term.field_value}.",
            [
                {
                    "type": "term",
                    "document_id": doc.id,
                    "file_name": doc.file_name,
                    "field_name": "thoi_han_hd",
                    "value": term.field_value,
                }
            ],
        )
    return _NOT_FOUND, []


def _answer_parties(db: Session, tenant_id: str, doc: Document) -> tuple[str, list[dict]]:
    terms = (
        db.query(Term)
        .filter(
            Term.tenant_id == tenant_id,
            Term.document_id == doc.id,
            Term.field_name == "doi_tac",
            Term.is_superseded == False,
        )
        .order_by(Term.created_at.desc())
        .all()
    )
    if terms:
        values = [t.field_value for t in terms if t.field_value]
        return (
            f"Đối tác trong hợp đồng {doc.file_name}: {', '.join(values)}.",
            [
                {
                    "type": "term",
                    "document_id": doc.id,
                    "file_name": doc.file_name,
                    "field_name": "doi_tac",
                    "value": t.field_value,
                }
                for t in terms
            ],
        )
    return _NOT_FOUND, []


def _answer_status(db: Session, tenant_id: str, doc: Document) -> tuple[str, list[dict]]:
    return (
        f"Trạng thái hợp đồng {doc.file_name}: {doc.status}.",
        [
            {
                "type": "document",
                "document_id": doc.id,
                "file_name": doc.file_name,
                "field_name": "status",
                "value": doc.status,
            }
        ],
    )


def answer_question(db: Session, tenant_id: str, question: str) -> dict:
    """Answer a chat query within a tenant scope.

    Returns {"answer": str, "sources": list[dict], "found": bool}.
    """
    if not question or not question.strip():
        return {"answer": _NOT_FOUND, "sources": [], "found": False}

    hint = _extract_doc_hint(question)
    intent = _detect_intent(question)

    doc: Document | None = None
    if hint:
        doc = _find_document_by_hint(db, tenant_id, hint)
        # If user explicitly named a document and it does not exist, stop here (D-08).
        if doc is None:
            return {"answer": _NOT_FOUND, "sources": [], "found": False}
    else:
        # No document named: only allow fallback for the primary M0 use case.
        if intent in {"expiry", "start_date", "duration"}:
            doc = _find_document_without_hint(db, tenant_id)

    if doc is None:
        return {"answer": _NOT_FOUND, "sources": [], "found": False}

    answer: str
    sources: list[dict]

    if intent == "expiry":
        answer, sources = _answer_expiry(db, tenant_id, doc)
    elif intent == "start_date":
        answer, sources = _answer_start_date(db, tenant_id, doc)
    elif intent == "duration":
        answer, sources = _answer_duration(db, tenant_id, doc)
    elif intent == "parties":
        answer, sources = _answer_parties(db, tenant_id, doc)
    elif intent == "status":
        answer, sources = _answer_status(db, tenant_id, doc)
    else:
        return {"answer": _NOT_FOUND, "sources": [], "found": False}

    if not sources:
        return {"answer": _NOT_FOUND, "sources": [], "found": False}

    return {"answer": answer, "sources": sources, "found": True}
