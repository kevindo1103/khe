"""DEC-031 v2 — Result-seeded progressive chat state (#201).

Covers: carry-over, TTL expiry cold-start, size cap, soft-prior fallback,
tenant isolation (D-10), multi-device independence. LLM steps are monkeypatched
so CI stays green without an API key.
"""
import os
import sys
import uuid
from datetime import datetime, timedelta

import pytest

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.models.tenant import ChatSession, Document, Obligation, Term
from app.services import chat_query, chat_session


def _mock_tools(calls):
    async def _select(*args, **kwargs):
        return calls, {}
    return _select


def _mock_format(answer):
    async def _fmt(*args, **kwargs):
        return answer, {}
    return _fmt


def _seed_doc(db, tenant_id, file_name):
    doc = Document(tenant_id=tenant_id, file_name=file_name,
                   file_path=f"x/{file_name}", status="extracted")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    db.add(Term(tenant_id=tenant_id, document_id=doc.id, field_name="ngay_het_han",
                field_value="2026-12-31", confidence=0.9, needs_review=False))
    db.commit()
    return doc


def _ask(auth_client, question, session_id=None):
    body = {"question": question}
    if session_id is not None:
        body["session_id"] = session_id
    r = auth_client.post("/chat/query", json=body)
    assert r.status_code == 200, r.text
    return r.json()


# ── 1. Carry-over ───────────────────────────────────────────────────────────

def test_session_carry_over_sets_then_reads_state(auth_client, test_tenant, db, monkeypatch):
    """Query 1 seeds the working set; the chat_sessions row holds pointer IDs."""
    doc = _seed_doc(db, test_tenant, "lease_q7.pdf")
    monkeypatch.setattr(chat_query, "_select_tools",
                        _mock_tools([{"name": "search_terms",
                                      "args": {"field_name": "ngay_het_han", "doc_hint": None,
                                               "value_contains": None, "party_filter": None}}]))
    monkeypatch.setattr(chat_query, "_format_answer", _mock_format("Hết hạn 2026-12-31."))

    sid = str(uuid.uuid4())
    data = _ask(auth_client, "khi nào hết hạn?", session_id=sid)
    assert data["found"] is True
    assert data["session_id"] == sid
    assert data["context_label"] == f"HĐ #{doc.id}"  # ID-only, no filename PII (#203 C1)

    row = db.query(ChatSession).filter(ChatSession.session_id == sid).first()
    assert row is not None
    import json
    state = json.loads(row.state_json)
    assert state["active_doc_ids"] == [doc.id]
    assert state["working_set_label"] == f"HĐ #{doc.id}"
    # Label must NOT leak the filename (party-name PII).
    assert "lease_q7" not in state["working_set_label"]


# ── 2. TTL expiry → cold start ──────────────────────────────────────────────

def test_expired_session_is_cold(auth_client, test_tenant, db, monkeypatch):
    """An expired session row is ignored (no error, no leak) — cold start."""
    _seed_doc(db, test_tenant, "old.pdf")
    sid = str(uuid.uuid4())
    # Pre-seed an expired session for this user.
    db.add(ChatSession(tenant_id=test_tenant, user_id=_user_id(db, test_tenant),
                       session_id=sid, state_json='{"active_doc_ids":[999]}',
                       expires_at=datetime.utcnow() - timedelta(hours=1)))
    db.commit()

    # load_session_state must treat it as cold.
    assert chat_session.load_session_state(db, test_tenant, _user_id(db, test_tenant), sid) is None

    monkeypatch.setattr(chat_query, "_select_tools",
                        _mock_tools([{"name": "search_terms",
                                      "args": {"field_name": "ngay_het_han", "doc_hint": None,
                                               "value_contains": None, "party_filter": None}}]))
    monkeypatch.setattr(chat_query, "_format_answer", _mock_format("Hết hạn 2026-12-31."))
    data = _ask(auth_client, "khi nào hết hạn?", session_id=sid)
    assert data["found"] is True  # cold start still works


# ── 3. Size cap ─────────────────────────────────────────────────────────────

def test_over_cap_integration_no_state_written(auth_client, test_tenant, db, monkeypatch):
    """End-to-end (#203 M3): >20 doc_ids in sources → context_label null + no row.

    Mock the tool directly so we bypass search_terms' 10-row truncation and
    actually exceed MAX_ACTIVE_DOC_IDS.
    """
    fake = [
        {"type": "term", "document_id": i, "obligation_id": None,
         "file_name": f"d{i}.pdf", "field_name": "ngay_het_han", "value": "2026-12-31"}
        for i in range(25)
    ]
    monkeypatch.setattr(chat_query, "_tool_search_terms", lambda *a, **k: fake)
    monkeypatch.setattr(chat_query, "_select_tools",
                        _mock_tools([{"name": "search_terms",
                                      "args": {"field_name": "ngay_het_han", "doc_hint": None,
                                               "value_contains": None, "party_filter": None}}]))
    monkeypatch.setattr(chat_query, "_format_answer", _mock_format("Nhiều kết quả."))

    sid = str(uuid.uuid4())
    data = _ask(auth_client, "tất cả ngày hết hạn", session_id=sid)
    assert data["found"] is True              # response still succeeds
    assert data["context_label"] is None      # over cap → no working-set chip
    # No chat_sessions row persisted for an over-cap result.
    assert db.query(ChatSession).filter(ChatSession.session_id == sid).first() is None


def test_soft_prior_skipped_on_party_filter_intent():
    """Explicit party_filter intent overrides the prior — don't hide the new target (#203 C2)."""
    results = [
        {"type": "term", "document_id": 7, "value": "penfield"},   # in prior
        {"type": "term", "document_id": 8, "value": "alaska"},     # newly named
    ]
    # The router used party_filter (no doc_hint) → treat as explicit intent.
    out, used = chat_session.apply_soft_prior(results, [7], had_explicit_doc_hint=True)
    assert used is False
    assert {r["document_id"] for r in out} == {7, 8}  # ALASKA not hidden


def test_sliding_ttl_capped_at_max_age(db, test_tenant):
    """Sliding refresh never pushes expiry past creation + SESSION_MAX_AGE_DAYS (#203 C3)."""
    from datetime import datetime, timedelta

    sid = str(uuid.uuid4())
    # Create a row, then back-date its created_at to ~7 days ago.
    chat_session.upsert_session(db, test_tenant, 1, sid, {"active_doc_ids": [1]})
    db.commit()
    row = db.query(ChatSession).filter(ChatSession.session_id == sid).first()
    row.created_at = datetime.utcnow() - timedelta(days=7)
    db.commit()

    # A new query would normally slide expiry to now+24h; the cap must clamp it
    # to created_at + 7d (i.e. roughly now), not now + 24h.
    chat_session.upsert_session(db, test_tenant, 1, sid, {"active_doc_ids": [2]})
    db.commit()
    db.refresh(row)
    assert row.expires_at <= row.created_at + timedelta(days=chat_session.SESSION_MAX_AGE_DAYS) + timedelta(seconds=1)
    assert row.expires_at < datetime.utcnow() + timedelta(hours=24)


def test_over_cap_helper_unit():
    """over_cap trips at 21 docs or 51 obligations."""
    assert chat_session.over_cap(list(range(21)), []) is True
    assert chat_session.over_cap([], list(range(51))) is True
    assert chat_session.over_cap(list(range(20)), list(range(50))) is False


# ── 4. Soft-prior fallback (D-08 safety) ────────────────────────────────────

def test_soft_prior_fallback_when_working_set_misses():
    """Active set yields nothing for this query → return full results (fallback)."""
    results = [
        {"type": "term", "document_id": 7, "value": "a"},
        {"type": "term", "document_id": 8, "value": "b"},
    ]
    # prior points at doc 99 (not in results) → fallback to all.
    out, used = chat_session.apply_soft_prior(results, [99], had_explicit_doc_hint=False)
    assert used is False
    assert out == results


def test_soft_prior_scopes_when_working_set_hits():
    """Active set matches some results → keep only those (carry-over)."""
    results = [
        {"type": "term", "document_id": 7, "value": "a"},
        {"type": "term", "document_id": 8, "value": "b"},
    ]
    out, used = chat_session.apply_soft_prior(results, [7], had_explicit_doc_hint=False)
    assert used is True
    assert [r["document_id"] for r in out] == [7]


def test_soft_prior_skipped_on_explicit_doc_hint():
    """An explicit doc_hint overrides the prior (respect user intent)."""
    results = [{"type": "term", "document_id": 7, "value": "a"}]
    out, used = chat_session.apply_soft_prior(results, [99], had_explicit_doc_hint=True)
    assert used is False
    assert out == results


# ── 5. Tenant isolation (D-10) ──────────────────────────────────────────────

def test_session_tenant_isolation(db, test_tenant):
    """A session_id row in tenant A is invisible to a different tenant scope."""
    sid = str(uuid.uuid4())
    chat_session.upsert_session(db, test_tenant, 1, sid, {"active_doc_ids": [1]})
    db.commit()
    # Same session_id, different tenant → not found (tenant filter).
    assert chat_session.load_session_state(db, "other-tenant", 1, sid) is None
    # Correct tenant → found.
    assert chat_session.load_session_state(db, test_tenant, 1, sid) is not None


# ── 6. Multi-device independence ────────────────────────────────────────────

def test_multi_device_two_sessions_independent(db, test_tenant):
    """Two UUIDs for the same user = two independent rows."""
    uid = 1
    sid_a, sid_b = str(uuid.uuid4()), str(uuid.uuid4())
    chat_session.upsert_session(db, test_tenant, uid, sid_a, {"active_doc_ids": [1]})
    chat_session.upsert_session(db, test_tenant, uid, sid_b, {"active_doc_ids": [2]})
    db.commit()
    a = chat_session.load_session_state(db, test_tenant, uid, sid_a)
    b = chat_session.load_session_state(db, test_tenant, uid, sid_b)
    assert a["active_doc_ids"] == [1]
    assert b["active_doc_ids"] == [2]
    assert db.query(ChatSession).filter(ChatSession.tenant_id == test_tenant).count() == 2


# ── DELETE endpoint ─────────────────────────────────────────────────────────

def test_reset_session_via_post_body(auth_client, test_tenant, db):
    """POST /chat/sessions/reset (JSON body, not query param) removes the row (#203 M1)."""
    sid = str(uuid.uuid4())
    chat_session.upsert_session(db, test_tenant, _user_id(db, test_tenant), sid, {"active_doc_ids": [1]})
    db.commit()
    r = auth_client.post("/chat/sessions/reset", json={"session_id": sid})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    db.expire_all()
    assert db.query(ChatSession).filter(ChatSession.session_id == sid).first() is None


# ── Weekly cleanup ──────────────────────────────────────────────────────────

def test_cleanup_removes_only_expired(db, test_tenant):
    live = str(uuid.uuid4())
    dead = str(uuid.uuid4())
    db.add(ChatSession(tenant_id=test_tenant, user_id=1, session_id=live,
                       state_json="{}", expires_at=datetime.utcnow() + timedelta(hours=5)))
    db.add(ChatSession(tenant_id=test_tenant, user_id=1, session_id=dead,
                       state_json="{}", expires_at=datetime.utcnow() - timedelta(hours=5)))
    db.commit()
    removed = chat_session.cleanup_expired_sessions(db)
    assert removed == 1
    assert db.query(ChatSession).filter(ChatSession.session_id == live).first() is not None
    assert db.query(ChatSession).filter(ChatSession.session_id == dead).first() is None


# ── helper ──────────────────────────────────────────────────────────────────

def _user_id(db, tenant_id) -> int:
    """qcuser's TenantUser.id from master.db (conftest seeds it)."""
    from app.db.database import MasterSessionLocal
    from app.models.master import TenantUser
    mdb = MasterSessionLocal()
    try:
        u = mdb.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id, TenantUser.username == "qcuser"
        ).first()
        return u.id
    finally:
        mdb.close()
