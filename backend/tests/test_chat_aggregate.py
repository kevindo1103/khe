"""Aggregate-intent chat tests (#199, FR-CQ Stage 6).

Covers QC's 9-case acceptance surface. Critical guards:
- T-zero: 0-of-category (e.g. 0 overdue while other obligations exist) → found=true,
  total=0, NEVER the D-08 "không tìm thấy" string.
- cold_start (tenant_empty) vs aggregate-zero vs retrieval no-match stay distinct.
- D-06: amount_raw is never summed.
- D-10: aggregate counts only the caller's tenant.

LLM routing is mocked (`_select_tools`); the aggregate path is deterministic and
calls no formatting LLM, so no `_format_answer` mock is needed.
"""
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Document, Obligation
from app.services import chat_query
from main import app

TENANT = "chat-agg-tenant"
_NOT_FOUND = "Không tìm thấy thông tin này trong hồ sơ của bạn."


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT)
    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT).first():
        db.add(Tenant(id=TENANT, name="Agg Tenant", db_path=f"tenants/{TENANT}.db"))
        db.commit()
    if not db.query(TenantUser).filter(TenantUser.tenant_id == TENANT, TenantUser.username == "agguser").first():
        db.add(TenantUser(tenant_id=TENANT, username="agguser",
                          hashed_password=get_password_hash("aggpass"), role="staff"))
        db.commit()
    db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT, "username": "agguser", "password": "aggpass"})
    assert r.status_code == 200
    return c


@pytest.fixture
def db():
    d = get_tenant_session(TENANT)
    try:
        yield d
    finally:
        d.close()


def _wipe(db):
    db.query(Obligation).filter(Obligation.tenant_id == TENANT).delete()
    db.query(Document).filter(Document.tenant_id == TENANT).delete()
    db.commit()


def _doc(db, name="agg.pdf"):
    d = Document(tenant_id=TENANT, file_name=name, file_path="x/y.pdf", status="extracted")
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def _ob(db, doc, **kw):
    defaults = dict(tenant_id=TENANT, document_id=doc.id, description="nghĩa vụ", recurrence="once", status="pending")
    defaults.update(kw)
    o = Obligation(**defaults)
    db.add(o)
    db.commit()
    return o


def _mock_route(args):
    async def _select(*a, **k):
        return [{"name": "aggregate_obligations", "args": args}], {"in": 80, "out": 15}
    return _select


def _agg_args(**over):
    base = {"group_by": "direction", "status": None, "direction": None,
            "obligation_type": None, "due_within_days": None, "series_id": None}
    base.update(over)
    return base


def _ask(auth_client, monkeypatch, args, question="tổng quan nghĩa vụ"):
    monkeypatch.setattr(chat_query, "_select_tools", _mock_route(args))
    r = auth_client.post("/chat/query", json={"question": question})
    assert r.status_code == 200
    return r.json()


# ── T1 / T6 — group_by=direction count ──────────────────────────────────────
def test_aggregate_by_direction(auth_client, db, monkeypatch):
    _wipe(db)
    doc = _doc(db)
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-12-31")
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-11-30")
    _ob(db, doc, direction="quyền_lợi", due_date="2026-10-01")

    data = _ask(auth_client, monkeypatch, _agg_args(group_by="direction"))
    assert data["intent"] == "aggregate"
    assert data["found"] is True
    assert data["summary"]["total"] == 3
    groups = {g["key"]: g["count"] for g in data["summary"]["groups"]}
    assert groups == {"nghĩa_vụ": 2, "quyền_lợi": 1}
    labels = {g["key"]: g["label"] for g in data["summary"]["groups"]}
    assert labels["nghĩa_vụ"] == "Bạn cần"
    assert labels["quyền_lợi"] == "Đối tác cần làm cho bạn"
    assert data["source"]["obligation_count"] == 3
    assert data["source"]["doc_count"] == 1
    assert data["source"]["label"] == "3 nghĩa vụ · 1 hợp đồng"
    # drill-down sources kept (FR-CQ-02)
    assert len(data["sources"]) == 3


# ── T-zero ⭐ — 0 overdue while other obligations exist → found=true, NOT D-08 ─
def test_aggregate_zero_overdue_is_not_d08(auth_client, db, monkeypatch):
    _wipe(db)
    doc = _doc(db)
    # Both future-dated → none overdue, but the tenant DOES have obligations.
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-12-31")
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-11-30")

    data = _ask(auth_client, monkeypatch, _agg_args(group_by="status", status="overdue"),
                question="có mấy nghĩa vụ quá hạn?")
    assert data["found"] is True                       # ⭐ not D-08
    assert data["intent"] == "aggregate"
    assert data["summary"]["total"] == 0
    assert data["answer"] != _NOT_FOUND
    assert "quá hạn" in data["answer"]
    assert data["sources"] == []


def test_overdue_derived_from_due_date_not_status(auth_client, db, monkeypatch):
    """A past-due active obligation counts as overdue; a done one does not (DEC-027)."""
    _wipe(db)
    doc = _doc(db)
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-01-01", status="pending")   # overdue
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-01-02", status="done")      # closed, not overdue
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-12-31", status="pending")   # future

    data = _ask(auth_client, monkeypatch, _agg_args(group_by="status", status="overdue"))
    assert data["found"] is True
    assert data["summary"]["total"] == 1               # only the pending past-due one


# ── T2 / cold_start — tenant with 0 documents ────────────────────────────────
def test_cold_start_tenant_empty(auth_client, db, monkeypatch):
    _wipe(db)  # no docs at all
    data = _ask(auth_client, monkeypatch, _agg_args(group_by="direction"))
    assert data["found"] is True
    assert data["tenant_empty"] is True
    assert data["summary"]["total"] == 0
    assert data["answer"] != _NOT_FOUND


def test_aggregate_zero_not_cold_start(auth_client, db, monkeypatch):
    """Tenant has docs+obligations but 0 match the filter → aggregate-zero, tenant_empty False."""
    _wipe(db)
    doc = _doc(db)
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-12-31")
    data = _ask(auth_client, monkeypatch, _agg_args(group_by="direction", direction="quyền_lợi"))
    assert data["found"] is True
    assert data["tenant_empty"] is False
    assert data["summary"]["total"] == 0


# ── T3 — series grouping ─────────────────────────────────────────────────────
def test_aggregate_by_series(auth_client, db, monkeypatch):
    _wipe(db)
    doc = _doc(db)
    for i in (1, 2, 3):
        _ob(db, doc, obligation_type="payment", milestone_series_id="S1",
            milestone_index=i, milestone_total=3,
            due_date=f"2026-0{i+6}-01", status="done" if i == 1 else "pending")
    data = _ask(auth_client, monkeypatch,
                _agg_args(group_by="series", obligation_type="payment"),
                question="còn mấy đợt thanh toán?")
    assert data["found"] is True
    assert data["summary"]["total"] == 3
    assert data["summary"]["groups"][0]["key"] == "S1"
    assert data["summary"]["groups"][0]["count"] == 3


# ── T4 — waiting_trigger count ───────────────────────────────────────────────
def test_aggregate_waiting_trigger(auth_client, db, monkeypatch):
    _wipe(db)
    doc = _doc(db)
    _ob(db, doc, status="waiting_trigger", due_date=None, trigger_condition="sau nghiệm thu")
    _ob(db, doc, status="pending", due_date="2026-12-31")
    data = _ask(auth_client, monkeypatch, _agg_args(group_by="status", status="waiting_trigger"),
                question="bao nhiêu việc đang chờ sự kiện?")
    assert data["found"] is True
    assert data["summary"]["total"] == 1
    assert data["summary"]["status_breakdown"]["waiting_trigger"] == 1


# ── status_breakdown derivation ──────────────────────────────────────────────
def test_status_breakdown(auth_client, db, monkeypatch):
    _wipe(db)
    doc = _doc(db)
    _ob(db, doc, due_date="2026-01-01", status="pending")     # overdue
    _ob(db, doc, due_date="2026-07-01", status="pending")     # due_soon (<=30d from 06-23)
    _ob(db, doc, due_date="2026-12-31", status="pending")     # scheduled
    _ob(db, doc, status="waiting_trigger", due_date=None)     # waiting
    data = _ask(auth_client, monkeypatch, _agg_args(group_by="direction"))
    sb = data["summary"]["status_breakdown"]
    assert sb["overdue"] == 1
    assert sb["due_soon"] == 1
    assert sb["waiting_trigger"] == 1


# ── nearest highlight ────────────────────────────────────────────────────────
def test_nearest_upcoming_in_group(auth_client, db, monkeypatch):
    _wipe(db)
    doc = _doc(db)
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-12-31", description="xa")
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-07-10", description="gần nhất")
    data = _ask(auth_client, monkeypatch, _agg_args(group_by="direction", direction="nghĩa_vụ"))
    g = data["summary"]["groups"][0]
    assert g["nearest"]["title"] == "gần nhất"
    assert g["nearest"]["days_left"] >= 0


# ── D-06 — amount_raw never summed ───────────────────────────────────────────
def test_no_amount_sum(auth_client, db, monkeypatch):
    _wipe(db)
    doc = _doc(db)
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-12-31", amount_raw="50 triệu")
    _ob(db, doc, direction="nghĩa_vụ", due_date="2026-11-30", amount_raw="50000000")
    data = _ask(auth_client, monkeypatch, _agg_args(group_by="direction"))
    summary = data["summary"]
    # No total-money field anywhere in the aggregate response.
    assert "amount" not in summary
    assert "total_amount" not in summary
    assert "total_amount" not in data["source"]
    assert "tiền" not in data["answer"].lower()


# ── T5 — retrieval no-match still D-08 (aggregate path didn't swallow it) ─────
def test_retrieval_still_d08(auth_client, db, monkeypatch):
    _wipe(db)
    _doc(db)

    async def _select(*a, **k):
        return [{"name": "search_obligations",
                 "args": {"due_within_days": 30, "status": "pending", "doc_hint": "khong_ton_tai"}}], {"in": 10, "out": 5}
    monkeypatch.setattr(chat_query, "_select_tools", _select)

    async def _fmt(*a, **k):
        return "", {"in": 0, "out": 0}
    monkeypatch.setattr(chat_query, "_format_answer", _fmt)

    r = auth_client.post("/chat/query", json={"question": "deadline HĐ không tồn tại?"})
    data = r.json()
    assert data["found"] is False
    assert data["answer"] == _NOT_FOUND
    assert data.get("intent", "retrieval") == "retrieval"
    assert data["sources"] == []
