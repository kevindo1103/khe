"""Result-seeded progressive chat state (DEC-031 v2, #201).

State is POINTER IDs only — never PII text — so it acts as a soft prior for the
next query, not a memory of content. The working set is re-seeded from each
answer's result set. TTL 24h; a weekly scheduler job purges expired rows.

Key safety rule (D-08): the prior is a *priority hint*, never a hard filter.
``apply_soft_prior`` only narrows to the working set when that set still
contains matching results; otherwise it returns everything, so we never answer
"not found" while data exists outside the working set.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.tenant import ChatSession

logger = logging.getLogger(__name__)

MAX_ACTIVE_DOC_IDS = 20
MAX_ACTIVE_OBLIGATION_IDS = 50
SESSION_TTL_HOURS = 24              # sliding window refreshed on each query
SESSION_MAX_AGE_DAYS = 7           # absolute cap from creation (#203 C3 — PM ratify)


def load_session_state(
    db: Session, tenant_id: str, user_id: int, session_id: str | None
) -> dict | None:
    """Return the parsed state_json for a live (non-expired) session, else None."""
    if not session_id:
        return None
    row = (
        db.query(ChatSession)
        .filter(
            ChatSession.tenant_id == tenant_id,
            ChatSession.user_id == user_id,
            ChatSession.session_id == session_id,
        )
        .first()
    )
    if row is None:
        return None
    if row.expires_at is not None and row.expires_at < datetime.utcnow():
        return None  # expired → cold start; cleanup job will delete the row
    try:
        return json.loads(row.state_json)
    except (json.JSONDecodeError, TypeError):
        return None


def apply_soft_prior(
    all_results: list[dict],
    prior_doc_ids: list[int] | None,
    had_explicit_doc_hint: bool,
) -> tuple[list[dict], bool]:
    """Re-scope already-retrieved results to the working set (soft prior).

    - User explicitly named a doc (doc_hint) → respect intent, no prior.
    - Else if any result falls inside ``prior_doc_ids`` → keep only those
      (the carry-over: a follow-up question stays in the working set).
    - Else → return everything (fallback; never hide data → D-08 safe).

    Returns ``(results, used_prior)``.
    """
    if had_explicit_doc_hint or not prior_doc_ids:
        return all_results, False
    prior = set(prior_doc_ids)
    real_in_prior = any(
        r["type"] != "truncation_hint" and r.get("document_id") in prior
        for r in all_results
    )
    if not real_in_prior:
        return all_results, False  # working set yields nothing → full fallback
    kept = [
        r
        for r in all_results
        if r["type"] == "truncation_hint" or r.get("document_id") in prior
    ]
    return kept, True


def compute_working_set(sources: list[dict]) -> tuple[list[int], list[int], str | None]:
    """Derive (doc_ids, obligation_ids, label) from the response sources.

    The label is ID-ONLY (no PII): VN contract filenames often embed party names
    (#203 C1 / NĐ 13). The FE resolves ``active_doc_ids`` → display names from the
    document list it already holds.
    """
    doc_ids: list[int] = []
    obl_ids: list[int] = []
    for s in sources:
        did = s.get("document_id")
        if did is not None and did not in doc_ids:
            doc_ids.append(did)
        oid = s.get("obligation_id")
        if oid is not None and oid not in obl_ids:
            obl_ids.append(oid)

    if len(doc_ids) == 1:
        label = f"HĐ #{doc_ids[0]}"          # pointer only — never the filename
    elif len(doc_ids) > 1:
        label = f"{len(doc_ids)} tài liệu"
    else:
        label = None
    return doc_ids, obl_ids, label


def over_cap(doc_ids: list[int], obl_ids: list[int]) -> bool:
    """True if the working set is too large to be a meaningful scope."""
    return len(doc_ids) > MAX_ACTIVE_DOC_IDS or len(obl_ids) > MAX_ACTIVE_OBLIGATION_IDS


def build_state(
    doc_ids: list[int],
    obl_ids: list[int],
    label: str | None,
    last_tool_call: str | None,
) -> dict:
    return {
        "active_doc_ids": doc_ids,
        "active_obligation_ids": obl_ids,
        "working_set_label": label,
        "last_tool_call": last_tool_call,
    }


def upsert_session(
    db: Session, tenant_id: str, user_id: int, session_id: str, state: dict
) -> None:
    """Insert/update the chat_sessions row WITHOUT committing.

    The caller commits — this is intentional so the row lands in the same
    transaction as the chat_query_log write (SQLite same-thread lock; CLAUDE.md
    bug pattern).
    """
    now = datetime.utcnow()
    sliding = now + timedelta(hours=SESSION_TTL_HOURS)
    payload = json.dumps(state, ensure_ascii=False)
    row = (
        db.query(ChatSession)
        .filter(
            ChatSession.tenant_id == tenant_id,
            ChatSession.user_id == user_id,
            ChatSession.session_id == session_id,
        )
        .first()
    )
    if row is None:
        db.add(
            ChatSession(
                tenant_id=tenant_id,
                user_id=user_id,
                session_id=session_id,
                state_json=payload,
                expires_at=sliding,  # fresh row → creation cap doesn't bind yet
            )
        )
    else:
        # Sliding 24h window, but never past the absolute max-age from creation
        # (#203 C3): an active daily user gets continuity without an immortal
        # thread (cross-session memory stays Phase 2).
        created = row.created_at or now
        max_expiry = created + timedelta(days=SESSION_MAX_AGE_DAYS)
        row.state_json = payload
        row.expires_at = min(sliding, max_expiry)
        row.updated_at = now


def delete_session(db: Session, tenant_id: str, user_id: int, session_id: str) -> int:
    """Explicit reset ("🔄 Hỏi mới"). Commits. Returns rows deleted."""
    n = (
        db.query(ChatSession)
        .filter(
            ChatSession.tenant_id == tenant_id,
            ChatSession.user_id == user_id,
            ChatSession.session_id == session_id,
        )
        .delete()
    )
    db.commit()
    return n


def cleanup_expired_sessions(db: Session) -> int:
    """Weekly job: drop sessions past their TTL. Commits. Returns rows deleted."""
    n = (
        db.query(ChatSession)
        .filter(ChatSession.expires_at < datetime.utcnow())
        .delete()
    )
    db.commit()
    return n
