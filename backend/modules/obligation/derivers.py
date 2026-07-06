"""StandingObligationDeriver — derive standing commitments from clauses (#274).

Standing obligations are ongoing commitments without a fixed due date:
confidentiality, non-compete, exclusivity, periodic reporting, compliance.

D-06 boundary (critical): description = clause title + verbatim first sentence
of clause content only. No LLM inference on legal effect. No paraphrasing.
No legal characterization.

Input: ExtractionResult.clauses[] (verbatim clause text, already in DB from
Gemini extraction).
Output: Obligation rows with:
  - obligation_type = "standing" (or "reporting" for periodic reporting)
  - status = "in_progress" (ongoing, no due_date)
  - due_date = NULL
  - direction = NULL (rederived via directions.py at confirm-time, D-13)
  - description = clause title + verbatim first sentence only
"""
from __future__ import annotations

import json
import re

from sqlalchemy.orm import Session

from app.models.tenant import Clause, Event, Obligation


# ── Clause title patterns → obligation_type mapping ──────────────────────
# Normalized (case-fold + diacritics-stripped) matching against clause titles.
# Conservative: only match patterns we're confident about (D-08 spirit).
_STANDING_PATTERNS: list[tuple[list[str], str]] = [
    # confidentiality / NDA — normalized-ASCII only; diacritics/CJK stripped by _norm()
    (["bao mat", "nda", "non-disclosure", "khong tiet lo"], "standing"),
    # non-compete
    (["khong canh tranh", "non-compete", "non compete"], "standing"),
    # exclusivity — "doc quyen" requires đ→d fix in _norm() for "độc quyền"
    (["doc quyen", "exclusiv"], "standing"),
    # compliance / general standing commitments — "dap ung" requires đ→d fix for "đáp ứng"
    (["tuan thu", "compliance", "dap ung"], "standing"),
    # periodic reporting — "dinh ky" requires đ→d fix for "định kỳ"
    (["bao cao dinh ky", "bao cao", "reporting", "periodic report"], "reporting"),
]


def _norm(s: str) -> str:
    """Case-fold + strip diacritics for fuzzy Vietnamese comparison.

    đ/Đ (U+0111/U+0110, LATIN LETTER D WITH STROKE) has no NFD decomposition
    and is silently dropped by encode("ascii","ignore"). Pre-replace before NFD.
    """
    import unicodedata
    s = s.replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().split())


def _first_sentence(text: str) -> str:
    """Extract the first sentence from clause content (verbatim, D-06).

    Splits on Vietnamese sentence terminators: . ! ? 。
    Returns the first non-empty, non-list-marker sentence, stripped.
    Skips pure digit segments that result from splitting "1. Bên A..." style
    Vietnamese numbered clauses.
    """
    if not text:
        return ""
    parts = re.split(r'[.!?。]', text.strip())
    for part in parts:
        s = part.strip()
        if s and not re.match(r'^\d+[)\.]?\s*$', s):
            return s
    return text.strip()


def _match_clause_type(title: str | None, content: str) -> str | None:
    """Check if a clause title matches any standing obligation pattern.

    Returns the obligation_type ("standing" or "reporting") or None if no match.
    Matching is against the clause TITLE primarily, with content as fallback
    for clauses where the title is None but the content starts with a keyword.
    """
    check_text = _norm(title or "")
    if not check_text:
        # Fallback: check first 100 chars of content for keyword presence.
        check_text = _norm(content[:100])

    for patterns, obl_type in _STANDING_PATTERNS:
        if any(p in check_text for p in patterns):
            return obl_type
    return None


def derive_standing_obligations(
    db: Session,
    tenant_id: str,
    doc_id: int,
    *,
    source_label: str = "ai_standing_derived",
) -> dict:
    """Derive standing obligations from persisted Clause rows for a document.

    Called after extraction_runner.py persists clauses + schedule-derived
    obligations. Idempotent: clears existing standing-type obligations for
    this doc (status=in_progress, source=ai_standing_derived) before
    re-inserting.

    D-06: description = clause title + verbatim first sentence only.
    No LLM. No legal characterization. No paraphrasing.

    Returns {"created": int, "skipped": bool, "reason": str | None}.
    """
    clauses = (
        db.query(Clause)
        .filter(
            Clause.tenant_id == tenant_id,
            Clause.document_id == doc_id,
        )
        .order_by(Clause.id.asc())
        .all()
    )

    if not clauses:
        return {"created": 0, "skipped": True, "reason": "No clauses found"}

    # Idempotency: clear existing standing-derived rows for this doc.
    # D-15 guard: fulfilled obligations are audit records — never delete them.
    db.query(Obligation).filter(
        Obligation.tenant_id == tenant_id,
        Obligation.document_id == doc_id,
        Obligation.obligation_type.in_(["standing", "reporting"]),
        Obligation.source == source_label,
        Obligation.fulfilled_at.is_(None),
    ).delete(synchronize_session=False)

    created = 0
    created_items: list[dict] = []

    for clause in clauses:
        obl_type = _match_clause_type(clause.title, clause.content)
        if obl_type is None:
            continue

        # D-06: description = clause title + verbatim first sentence only.
        title_part = clause.title or clause.clause_num or ""
        first_sent = _first_sentence(clause.content)
        if title_part and first_sent:
            description = f"{title_part} — {first_sent}"
        elif first_sent:
            description = first_sent
        else:
            description = title_part or "(Không có nội dung)"

        # Dedup guard: skip if a done/cancelled row with same description already exists.
        existing = db.query(Obligation).filter(
            Obligation.tenant_id == tenant_id,
            Obligation.document_id == doc_id,
            Obligation.description == description,
            Obligation.obligation_type == obl_type,
            Obligation.status.in_(["done", "cancelled"]),
        ).first()
        if existing:
            continue

        ob = Obligation(
            tenant_id=tenant_id,
            document_id=doc_id,
            description=description,
            obligation_type=obl_type,
            recurrence="open_ended_review",  # standing = ongoing, reviewed continuously
            direction=None,     # rederived at confirm-time (D-13)
            obligor=None,
            due_date=None,      # standing = no due date
            status="in_progress",
            remind_before_days=0,  # no reminders for standing obligations
            source=source_label,
            source_clause_num=clause.clause_num,
            derived_from="original",
        )
        db.add(ob)
        created += 1
        created_items.append({
            "obligation_type": obl_type,
            "source_clause_num": clause.clause_num,
            "description": description,
        })

    if created:
        db.add(Event(
            tenant_id=tenant_id,
            event_type="standing_obligation_derived",
            entity_type="document",
            entity_id=doc_id,
            actor="system",
            purpose=None,
            payload=json.dumps({
                "count": created,
                "items": created_items,
            }),
        ))

    db.commit()
    return {"created": created, "skipped": False, "reason": None}
