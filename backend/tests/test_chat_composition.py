"""Cross-filter composition tests for chat query (new schema DEC-027/029/030 + #153 Phase 2).

Tests AND-composition of multiple filters simultaneously:
- direction + obligation_type
- doc_type_filter + direction + status
- series_id + status
- waiting_trigger + doc_type_filter
- direction + due_from/due_to
- obligation_type + series_id
- D-08 when cross-filter yields empty
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
from app.models.tenant import Document, Obligation, Term
from app.services import chat_query
from main import app

TENANT = "compose-tenant"


@pytest.fixture(scope="module", autouse=True)
def _setup_module():
    init_master_db()
    init_tenant_db(TENANT)
    mdb = MasterSessionLocal()
    if not mdb.query(Tenant).filter(Tenant.id == TENANT).first():
        mdb.add(Tenant(id=TENANT, name="Compose Tenant", db_path=f"tenants/{TENANT}.db"))
        mdb.commit()
    if not mdb.query(TenantUser).filter(TenantUser.tenant_id == TENANT, TenantUser.username == "composeuser").first():
        mdb.add(TenantUser(
            tenant_id=TENANT,
            username="composeuser",
            hashed_password=get_password_hash("composepass"),
            role="staff",
        ))
        mdb.commit()
    mdb.close()


@pytest.fixture
def client():
    c = TestClient(app)
    r = c.post("/auth/login", json={"tenant_id": TENANT, "username": "composeuser", "password": "composepass"})
    assert r.status_code == 200
    return c


@pytest.fixture
def db():
    d = get_tenant_session(TENANT)
    try:
        yield d
    finally:
        d.close()


def _mk_doc(db, name, doc_type_group=None):
    """Create a document with optional doc_type_group Term."""
    doc = Document(tenant_id=TENANT, file_name=name, file_path=f"x/{name}", status="extracted")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    if doc_type_group:
        db.add(Term(
            tenant_id=TENANT, document_id=doc.id,
            field_name="doc_type_group", field_value=doc_type_group, confidence=0.95,
        ))
        db.commit()
    return doc


def _mk_ob(db, doc, *, due_date, status="pending", obligation_type="other",
           direction=None, recurrence="once", series_id=None,
           milestone_index=None, milestone_total=None, milestone_trigger="date",
           trigger_condition=None, description="test obligation"):
    ob = Obligation(
        tenant_id=TENANT, document_id=doc.id,
        description=description, recurrence=recurrence,
        obligation_type=obligation_type, direction=direction,
        due_date=due_date, status=status,
        milestone_series_id=series_id,
        milestone_index=milestone_index,
        milestone_total=milestone_total,
        milestone_trigger=milestone_trigger,
        trigger_condition=trigger_condition,
    )
    db.add(ob)
    db.commit()
    return ob


def _mock_tools(calls):
    async def _select(*args, **kwargs):
        return calls, {"in": 50, "out": 10}
    return _select


def _mock_answer(text):
    async def _format(*args, **kwargs):
        return text, {"in": 100, "out": 20}
    return _format


def _base_args(**overrides):
    """Full args dict with all filters null/false, then apply overrides."""
    base = {
        "due_within_days": None, "status": None, "doc_hint": None,
        "due_from": None, "due_to": None,
        "obligation_type": None, "direction": None,
        "doc_type_filter": None, "series_id": None, "waiting_trigger": False,
    }
    base.update(overrides)
    return base


def _ob_sources(data):
    return [s for s in data["sources"] if s["type"] == "obligation"]


class TestDirectionPlusObligationType:
    """direction + obligation_type AND-compose: only rows matching BOTH returned."""

    def test_direction_nghia_vu_and_payment(self, client, db, monkeypatch):
        db.query(Obligation).filter(Obligation.tenant_id == TENANT).delete()
        db.query(Document).filter(Document.tenant_id == TENANT).delete()
        db.commit()

        doc = _mk_doc(db, "compose_dir_type.pdf")
        _mk_ob(db, doc, due_date="2026-09-01", obligation_type="payment",
               direction="nghĩa_vụ", description="Bên A thanh toán")
        _mk_ob(db, doc, due_date="2026-09-01", obligation_type="payment",
               direction="quyền_lợi", description="Bên B thanh toán")
        _mk_ob(db, doc, due_date="2026-09-01", obligation_type="delivery",
               direction="nghĩa_vụ", description="Bên A giao hàng")

        monkeypatch.setattr(chat_query, "_select_tools", _mock_tools([{
            "name": "search_obligations",
            "args": _base_args(obligation_type="payment", direction="nghĩa_vụ"),
        }]))
        monkeypatch.setattr(chat_query, "_format_answer", _mock_answer("1 payment nghĩa vụ."))

        r = client.post("/chat/query", json={"question": "tôi phải thanh toán gì?"})
        assert r.status_code == 200
        sources = _ob_sources(r.json())
        assert len(sources) == 1
        assert sources[0]["value"] == "2026-09-01"

    def test_direction_quyen_loi_and_expiration(self, client, db, monkeypatch):
        db.query(Obligation).filter(Obligation.tenant_id == TENANT).delete()
        db.query(Document).filter(Document.tenant_id == TENANT).delete()
        db.commit()

        doc = _mk_doc(db, "compose_ql_exp.pdf")
        _mk_ob(db, doc, due_date="2026-11-01", obligation_type="expiration",
               direction="quyền_lợi", description="HĐ đối tác hết hạn")
        _mk_ob(db, doc, due_date="2026-11-01", obligation_type="expiration",
               direction="nghĩa_vụ", description="Nghĩa vụ hết hạn")
        _mk_ob(db, doc, due_date="2026-11-01", obligation_type="renewal",
               direction="quyền_lợi", description="Gia hạn quyền lợi")

        monkeypatch.setattr(chat_query, "_select_tools", _mock_tools([{
            "name": "search_obligations",
            "args": _base_args(obligation_type="expiration", direction="quyền_lợi"),
        }]))
        monkeypatch.setattr(chat_query, "_format_answer", _mock_answer("1 expiration quyền lợi."))

        r = client.post("/chat/query", json={"question": "đối tác có hợp đồng nào hết hạn không?"})
        assert r.status_code == 200
        sources = _ob_sources(r.json())
        assert len(sources) == 1

    def test_no_match_returns_d08(self, client, db, monkeypatch):
        """direction=nghĩa_vụ + obligation_type=warranty with no matching row → D-08."""
        db.query(Obligation).filter(Obligation.tenant_id == TENANT).delete()
        db.query(Document).filter(Document.tenant_id == TENANT).delete()
        db.commit()

        doc = _mk_doc(db, "compose_nomatch.pdf")
        _mk_ob(db, doc, due_date="2026-12-01", obligation_type="payment", direction="nghĩa_vụ")

        monkeypatch.setattr(chat_query, "_select_tools", _mock_tools([{
            "name": "search_obligations",
            "args": _base_args(obligation_type="warranty", direction="nghĩa_vụ"),
        }]))
        monkeypatch.setattr(chat_query, "_format_answer", _mock_answer("Không tìm thấy thông tin này trong hồ sơ của bạn."))

        r = client.post("/chat/query", json={"question": "tôi có bảo hành gì không?"})
        assert r.status_code == 200
        data = r.json()
        assert data["found"] is False
        assert data["answer"] == "Không tìm thấy thông tin này trong hồ sơ của bạn."
        assert data["sources"] == []


class TestDocTypeFilterPlusDirection:
    """doc_type_filter + direction: scope by contract type AND party direction."""

    def test_lao_dong_nghia_vu_only(self, client, db, monkeypatch):
        db.query(Obligation).filter(Obligation.tenant_id == TENANT).delete()
        db.query(Document).filter(Document.tenant_id == TENANT).delete()
        db.commit()

        doc_ld = _mk_doc(db, "hop_dong_lao_dong.pdf", doc_type_group="lao_dong")
        doc_tm = _mk_doc(db, "hop_dong_thuong_mai.pdf", doc_type_group="thuong_mai")

        _mk_ob(db, doc_ld, due_date="2026-07-15", direction="nghĩa_vụ",
               obligation_type="payment", description="Trả lương tháng 7")
        _mk_ob(db, doc_ld, due_date="2026-07-15", direction="quyền_lợi",
               obligation_type="payment", description="Nhận thưởng tháng 7")
        _mk_ob(db, doc_tm, due_date="2026-07-15", direction="nghĩa_vụ",
               obligation_type="payment", description="Thanh toán nhà cung cấp")

        monkeypatch.setattr(chat_query, "_select_tools", _mock_tools([{
            "name": "search_obligations",
            "args": _base_args(doc_type_filter="lao_dong", direction="nghĩa_vụ"),
        }]))
        monkeypatch.setattr(chat_query, "_format_answer", _mock_answer("1 lao_dong nghĩa vụ."))

        r = client.post("/chat/query", json={"question": "tôi phải trả gì theo HĐ lao động?"})
        assert r.status_code == 200
        sources = _ob_sources(r.json())
        assert len(sources) == 1
        assert sources[0]["value"] == "2026-07-15"

    def test_unknown_doc_type_d08(self, client, db, monkeypatch):
        """doc_type_filter with no docs of that type → D-08, no crash."""
        db.query(Obligation).filter(Obligation.tenant_id == TENANT).delete()
        db.query(Document).filter(Document.tenant_id == TENANT).delete()
        db.commit()

        doc = _mk_doc(db, "no_type.pdf", doc_type_group="thuong_mai")
        _mk_ob(db, doc, due_date="2026-08-01")

        monkeypatch.setattr(chat_query, "_select_tools", _mock_tools([{
            "name": "search_obligations",
            "args": _base_args(doc_type_filter="xay_dung"),
        }]))
        monkeypatch.setattr(chat_query, "_format_answer", _mock_answer("Không tìm thấy thông tin này trong hồ sơ của bạn."))

        r = client.post("/chat/query", json={"question": "HĐ xây dựng có gì?"})
        assert r.status_code == 200
        assert r.json()["found"] is False


class TestSeriesIdPlusStatus:
    """series_id + status AND-compose: scope to series AND status."""

    def test_series_pending_only(self, client, db, monkeypatch):
        db.query(Obligation).filter(Obligation.tenant_id == TENANT).delete()
        db.query(Document).filter(Document.tenant_id == TENANT).delete()
        db.commit()

        doc = _mk_doc(db, "series_status.pdf")
        _mk_ob(db, doc, due_date="2026-07-01", status="pending",
               series_id="s-xyz", milestone_index=1, milestone_total=3,
               obligation_type="payment", description="Đợt 1 — pending")
        _mk_ob(db, doc, due_date="2026-08-01", status="done",
               series_id="s-xyz", milestone_index=2, milestone_total=3,
               obligation_type="payment", description="Đợt 2 — done")
        _mk_ob(db, doc, due_date="2026-09-01", status="pending",
               series_id="s-xyz", milestone_index=3, milestone_total=3,
               obligation_type="payment", description="Đợt 3 — pending")

        monkeypatch.setattr(chat_query, "_select_tools", _mock_tools([{
            "name": "search_obligations",
            "args": _base_args(series_id="s-xyz", status="pending"),
        }]))
        monkeypatch.setattr(chat_query, "_format_answer", _mock_answer("2 đợt pending."))

        r = client.post("/chat/query", json={"question": "còn bao nhiêu đợt thanh toán chưa xong?"})
        assert r.status_code == 200
        sources = _ob_sources(r.json())
        assert len(sources) == 2
        assert all(s["status"] == "pending" for s in sources)
        values = sorted(s["value"] for s in sources)
        assert values == ["2026-07-01", "2026-09-01"]

    def test_series_done_excludes_pending(self, client, db, monkeypatch):
        db.query(Obligation).filter(Obligation.tenant_id == TENANT).delete()
        db.query(Document).filter(Document.tenant_id == TENANT).delete()
        db.commit()

        doc = _mk_doc(db, "series_done.pdf")
        _mk_ob(db, doc, due_date="2026-06-01", status="done",
               series_id="s-done-check", milestone_index=1, milestone_total=2)
        _mk_ob(db, doc, due_date="2026-07-01", status="pending",
               series_id="s-done-check", milestone_index=2, milestone_total=2)

        monkeypatch.setattr(chat_query, "_select_tools", _mock_tools([{
            "name": "search_obligations",
            "args": _base_args(series_id="s-done-check", status="done"),
        }]))
        monkeypatch.setattr(chat_query, "_format_answer", _mock_answer("1 xong rồi."))

        r = client.post("/chat/query", json={"question": "đợt nào đã hoàn thành?"})
        assert r.status_code == 200
        sources = _ob_sources(r.json())
        assert len(sources) == 1
        assert sources[0]["status"] == "done"


class TestWaitingTriggerPlusDocType:
    """waiting_trigger=True + doc_type_filter: event-gated obligations scoped by contract type."""

    def test_waiting_trigger_lao_dong(self, client, db, monkeypatch):
        db.query(Obligation).filter(Obligation.tenant_id == TENANT).delete()
        db.query(Document).filter(Document.tenant_id == TENANT).delete()
        db.commit()

        doc_ld = _mk_doc(db, "ld_trigger.pdf", doc_type_group="lao_dong")
        doc_tm = _mk_doc(db, "tm_trigger.pdf", doc_type_group="thuong_mai")

        _mk_ob(db, doc_ld, due_date=None, status="waiting_trigger",
               milestone_trigger="event", trigger_condition="Sau khi nghiệm thu",
               obligation_type="delivery", description="Giao hàng chờ nghiệm thu (lao_dong)")
        _mk_ob(db, doc_tm, due_date=None, status="waiting_trigger",
               milestone_trigger="event", trigger_condition="Sau khi ký biên bản",
               obligation_type="payment", description="Thanh toán chờ biên bản (thuong_mai)")
        _mk_ob(db, doc_ld, due_date="2026-08-01", status="pending",
               obligation_type="payment", description="Thanh toán thường (lao_dong)")

        monkeypatch.setattr(chat_query, "_select_tools", _mock_tools([{
            "name": "search_obligations",
            "args": _base_args(doc_type_filter="lao_dong", waiting_trigger=True),
        }]))
        monkeypatch.setattr(chat_query, "_format_answer", _mock_answer("1 chờ sự kiện."))

        r = client.post("/chat/query", json={"question": "HĐ lao động đang chờ sự kiện gì?"})
        assert r.status_code == 200
        sources = _ob_sources(r.json())
        # waiting_trigger=True filters by status="waiting_trigger",
        # doc_type_filter="lao_dong" scopes to lao_dong doc → 1 match
        assert len(sources) == 1


class TestDirectionPlusDueDateRange:
    """direction + due_from/due_to: obligations in a date range filtered by direction."""

    def test_nghia_vu_q3_2026(self, client, db, monkeypatch):
        db.query(Obligation).filter(Obligation.tenant_id == TENANT).delete()
        db.query(Document).filter(Document.tenant_id == TENANT).delete()
        db.commit()

        doc = _mk_doc(db, "q3_direction.pdf")
        _mk_ob(db, doc, due_date="2026-07-15", direction="nghĩa_vụ",
               obligation_type="payment", description="Tháng 7 — nghĩa vụ")
        _mk_ob(db, doc, due_date="2026-07-15", direction="quyền_lợi",
               obligation_type="payment", description="Tháng 7 — quyền lợi")
        _mk_ob(db, doc, due_date="2026-10-01", direction="nghĩa_vụ",
               obligation_type="payment", description="Tháng 10 — ngoài Q3")

        monkeypatch.setattr(chat_query, "_select_tools", _mock_tools([{
            "name": "search_obligations",
            "args": _base_args(
                direction="nghĩa_vụ",
                due_from="2026-07-01", due_to="2026-09-30",
            ),
        }]))
        monkeypatch.setattr(chat_query, "_format_answer", _mock_answer("1 nghĩa vụ Q3."))

        r = client.post("/chat/query", json={"question": "tôi phải làm gì trong Q3?"})
        assert r.status_code == 200
        sources = _ob_sources(r.json())
        assert len(sources) == 1
        assert sources[0]["value"] == "2026-07-15"

    def test_no_quyen_loi_in_q3_returns_d08(self, client, db, monkeypatch):
        db.query(Obligation).filter(Obligation.tenant_id == TENANT).delete()
        db.query(Document).filter(Document.tenant_id == TENANT).delete()
        db.commit()

        doc = _mk_doc(db, "q3_quyen_loi_empty.pdf")
        _mk_ob(db, doc, due_date="2026-07-01", direction="nghĩa_vụ",
               obligation_type="payment", description="Nghĩa vụ Q3")

        monkeypatch.setattr(chat_query, "_select_tools", _mock_tools([{
            "name": "search_obligations",
            "args": _base_args(
                direction="quyền_lợi",
                due_from="2026-07-01", due_to="2026-09-30",
            ),
        }]))
        monkeypatch.setattr(chat_query, "_format_answer", _mock_answer("Không tìm thấy thông tin này trong hồ sơ của bạn."))

        r = client.post("/chat/query", json={"question": "đối tác phải làm gì cho tôi trong Q3?"})
        assert r.status_code == 200
        assert r.json()["found"] is False


class TestObligationTypePlusSeries:
    """obligation_type + series_id: type-scoped installment queries."""

    def test_payment_series_only(self, client, db, monkeypatch):
        db.query(Obligation).filter(Obligation.tenant_id == TENANT).delete()
        db.query(Document).filter(Document.tenant_id == TENANT).delete()
        db.commit()

        doc = _mk_doc(db, "payment_series.pdf")
        _mk_ob(db, doc, due_date="2026-07-01", obligation_type="payment",
               series_id="pay-series-1", milestone_index=1, milestone_total=2)
        _mk_ob(db, doc, due_date="2026-08-01", obligation_type="payment",
               series_id="pay-series-1", milestone_index=2, milestone_total=2)
        _mk_ob(db, doc, due_date="2026-07-15", obligation_type="delivery",
               series_id="pay-series-1", description="Giao hàng cùng series")

        monkeypatch.setattr(chat_query, "_select_tools", _mock_tools([{
            "name": "search_obligations",
            "args": _base_args(obligation_type="payment", series_id="pay-series-1"),
        }]))
        monkeypatch.setattr(chat_query, "_format_answer", _mock_answer("2 đợt thanh toán."))

        r = client.post("/chat/query", json={"question": "các đợt thanh toán trong chuỗi này?"})
        assert r.status_code == 200
        sources = _ob_sources(r.json())
        assert len(sources) == 2
        assert all(s["value"] in ["2026-07-01", "2026-08-01"] for s in sources)
