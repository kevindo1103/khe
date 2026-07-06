"""Manual + rule-pack obligation API tests (#494).

Covers:
- POST /obligations without document_id requires direction.
- Manual obligation creation (source=user_manual) and event logging.
- Rule-pack obligation creation (source=rule_pack, source_rule_id passthrough).
- Event-triggered obligations without due_date start in waiting_trigger.
- Cross-tenant document_id reference returns 404.
- POST /documents/ manual metadata-only document + embedded terms/obligations.
- POST /documents/{id}/confirm reuses the existing confirm path.
"""
import os
import sys
import uuid

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest

from app.db.database import MasterSessionLocal, get_tenant_session, init_tenant_db
from app.models.master import Tenant
from app.models.tenant import Document, Event, Obligation, Party


def _other_tenant_doc_id() -> int:
    """Create a Document in a separate tenant and return its id."""
    other_tid = f"manual-iso-{uuid.uuid4().hex[:8]}"
    init_tenant_db(other_tid)
    mdb = MasterSessionLocal()
    try:
        mdb.add(Tenant(id=other_tid, name="Manual OB Other", db_path=f"tenants/{other_tid}.db"))
        mdb.commit()
    finally:
        mdb.close()

    odb = get_tenant_session(other_tid)
    try:
        doc = Document(
            tenant_id=other_tid,
            file_name="other.pdf",
            file_path=f"{other_tid}/other.pdf",
            doc_type="manual",
            status="needs_review",
        )
        odb.add(doc)
        odb.commit()
        odb.refresh(doc)
        return doc.id
    finally:
        odb.close()


def test_create_obligation_without_document_requires_direction(auth_client):
    r = auth_client.post("/obligations/", json={
        "description": "Manual obligation",
        "obligation_type": "payment",
        "due_date": "2026-08-01",
    })
    assert r.status_code == 422
    assert "direction" in r.json()["detail"]


def test_create_manual_obligation(auth_client, db):
    r = auth_client.post("/obligations/", json={
        "description": "Manual obligation",
        "obligation_type": "payment",
        "direction": "nghĩa_vụ",
        "due_date": "2026-08-01",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["document_id"] is None
    assert data["direction"] == "nghĩa_vụ"
    assert data["status"] == "pending"
    assert data["source"] == "user_manual"

    ob_id = data["id"]
    ev = (
        db.query(Event)
        .filter(
            Event.entity_id == ob_id,
            Event.entity_type == "obligation",
            Event.event_type == "created",
        )
        .order_by(Event.id.desc())
        .first()
    )
    assert ev is not None


def test_create_rule_pack_obligation(auth_client):
    r = auth_client.post("/obligations/", json={
        "description": "Rule pack obligation",
        "obligation_type": "reporting",
        "direction": "nghĩa_vụ",
        "source": "rule_pack",
        "source_rule_id": "nd70/2025",
        "due_date": "2026-08-01",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["source"] == "rule_pack"
    assert data["source_rule_id"] == "nd70/2025"


def test_create_event_triggered_obligation(auth_client):
    r = auth_client.post("/obligations/", json={
        "description": "Event triggered obligation",
        "obligation_type": "review",
        "direction": "nghĩa_vụ",
        "milestone_trigger": "event",
        "trigger_condition": "Sau khi nghiệm thu",
        "trigger_delay_days": 30,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "waiting_trigger"
    assert data["due_date"] is None


def test_date_trigger_requires_due_date(auth_client):
    r = auth_client.post("/obligations/", json={
        "description": "Date trigger without date",
        "obligation_type": "payment",
        "direction": "nghĩa_vụ",
        "milestone_trigger": "date",
    })
    assert r.status_code == 422
    errors = r.json()["detail"]
    assert any("due_date" in e.get("msg", "") for e in errors)


def test_single_post_rejects_trigger_obligation_ref(auth_client):
    r = auth_client.post("/obligations/", json={
        "description": "Single item with cross-ref",
        "obligation_type": "payment",
        "direction": "nghĩa_vụ",
        "due_date": "2026-08-01",
        "trigger_obligation_ref": 0,
    })
    assert r.status_code == 422
    assert "trigger_obligation_ref" in r.json()["detail"]


def test_create_obligation_with_foreign_document_returns_404(auth_client):
    other_doc_id = _other_tenant_doc_id()
    r = auth_client.post("/obligations/", json={
        "description": "Foreign doc",
        "obligation_type": "payment",
        "direction": "nghĩa_vụ",
        "document_id": other_doc_id,
        "due_date": "2026-08-01",
    })
    assert r.status_code == 404


def test_create_manual_document(auth_client, db):
    r = auth_client.post("/documents/", json={
        "title": "Hợp đồng thuê nhà (nhập tay)",
        "doc_type": "manual",
        "counterparty": "Công ty XYZ",
        "sign_date": "2026-01-01",
        "effective_date": "2026-02-01",
        "terms": [
            {"field_name": "doi_tac", "field_value": "Công ty XYZ", "source": "manual"},
            {"field_name": "ngay_hieu_luc", "field_value": "2026-02-01", "source": "manual"},
        ],
        "obligations": [
            {
                "description": "Trả tiền thuê",
                "obligation_type": "payment",
                "direction": "nghĩa_vụ",
                "due_date": "2026-03-01",
            },
            {
                "description": "Bảo trì",
                "obligation_type": "warranty",
                "milestone_trigger": "event",
                "trigger_condition": "Báo hỏng",
            },
        ],
    })
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Hợp đồng thuê nhà (nhập tay)"
    assert data["status"] == "needs_review"
    assert data["file_url"] is None
    assert len(data["terms"]) == 2
    assert len(data["obligations"]) == 2
    assert data["obligations"][0]["document_id"] == data["id"]
    assert data["obligations"][1]["status"] == "waiting_trigger"
    assert data["parties"][0]["name"] == "Công ty XYZ"

    doc_id = data["id"]
    confirm = auth_client.post(f"/documents/{doc_id}/confirm")
    assert confirm.status_code == 200
    assert confirm.json()["doc_id"] == doc_id

    ev = (
        db.query(Event)
        .filter(
            Event.entity_id == doc_id,
            Event.entity_type == "document",
            Event.event_type == "created",
        )
        .order_by(Event.id.desc())
        .first()
    )
    assert ev is not None


def test_create_manual_document_with_cross_ref(auth_client):
    r = auth_client.post("/documents/", json={
        "title": "HĐ có nghĩa vụ phụ thuộc",
        "doc_type": "manual",
        "counterparty": "Công ty ABC",
        "obligations": [
            {
                "description": "Nghiệm thu",
                "obligation_type": "delivery",
                "direction": "nghĩa_vụ",
                "due_date": "2026-03-01",
            },
            {
                "description": "Trả tiền sau nghiệm thu",
                "obligation_type": "payment",
                "direction": "nghĩa_vụ",
                "milestone_trigger": "event",
                "trigger_condition": "Sau khi nghiệm thu",
                "trigger_delay_days": 7,
                "trigger_obligation_ref": 0,
            },
        ],
    })
    assert r.status_code == 201
    data = r.json()
    first_id = data["obligations"][0]["id"]
    second = data["obligations"][1]
    assert second["trigger_obligation_id"] == first_id
    assert second["status"] == "waiting_trigger"


def test_direction_derived_when_document_id_provided(tenant_with_legal_name, auth_client, db):
    legal_name = "Công ty TNHH Test ABC"
    doc = Document(
        tenant_id=tenant_with_legal_name,
        file_name="self_party.pdf",
        file_path=f"{tenant_with_legal_name}/self_party.pdf",
        doc_type="manual",
        status="needs_review",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    db.add(Party(
        tenant_id=tenant_with_legal_name,
        document_id=doc.id,
        name=legal_name,
        role_label="bên A",
    ))
    db.commit()

    r = auth_client.post("/obligations/", json={
        "description": "Obligation with auto direction",
        "obligation_type": "payment",
        "document_id": doc.id,
        "obligor": legal_name,
        "due_date": "2026-08-01",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["direction"] == "nghĩa_vụ"
