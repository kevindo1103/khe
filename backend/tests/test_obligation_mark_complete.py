"""Tests for POST /obligations/{id}/mark-complete (#281).

Covers:
1. pending → done (happy path), fulfilled_at set, fulfilled_by defaults to username
2. awaiting_confirmation → done (allowed)
3. Custom fulfilled_by stored
4. source="user_manual" set when source is NULL
5. source preserved when already set
6. already done → 409 Conflict
7. cancelled → 409 Conflict
8. waiting_trigger → 400 Bad Request
9. Tenant isolation: other tenant's obligation → 404
10. Event obligation_fulfilled logged
"""
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.models.tenant import Document, Event, Obligation


def _make_doc(db, tenant_id):
    doc = Document(
        tenant_id=tenant_id,
        file_name="test.pdf",
        file_path=f"{tenant_id}/test.pdf",
        status="extracted",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _make_obligation(db, tenant_id, doc_id, *, status="pending", source=None):
    ob = Obligation(
        tenant_id=tenant_id,
        document_id=doc_id,
        description="Thanh toán tháng 7",
        obligation_type="payment",
        recurrence="once",
        status=status,
        due_date="2026-07-05",
        source=source,
    )
    db.add(ob)
    db.commit()
    db.refresh(ob)
    return ob


class TestMarkComplete:
    def test_pending_to_done_happy_path(self, auth_client, test_tenant, db):
        """pending → done: fulfilled_at set, fulfilled_by defaults to 'qcuser'."""
        doc = _make_doc(db, test_tenant)
        ob = _make_obligation(db, test_tenant, doc.id, status="pending")

        r = auth_client.post(f"/obligations/{ob.id}/mark-complete", json={})
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert data["obligation"]["status"] == "done"
        assert data["obligation"]["fulfilled_at"] is not None
        assert data["obligation"]["fulfilled_by"] == "qcuser"

    def test_awaiting_confirmation_to_done(self, auth_client, test_tenant, db):
        """awaiting_confirmation → done is allowed."""
        doc = _make_doc(db, test_tenant)
        ob = _make_obligation(db, test_tenant, doc.id, status="awaiting_confirmation")

        r = auth_client.post(f"/obligations/{ob.id}/mark-complete", json={})
        assert r.status_code == 200
        assert r.json()["obligation"]["status"] == "done"

    def test_custom_fulfilled_by_stored(self, auth_client, test_tenant, db):
        """fulfilled_by from request body is stored."""
        doc = _make_doc(db, test_tenant)
        ob = _make_obligation(db, test_tenant, doc.id, status="pending")

        r = auth_client.post(
            f"/obligations/{ob.id}/mark-complete",
            json={"fulfilled_by": "Nguyễn Văn A"},
        )
        assert r.status_code == 200
        assert r.json()["obligation"]["fulfilled_by"] == "Nguyễn Văn A"

    def test_source_set_to_user_manual_when_null(self, auth_client, test_tenant, db):
        """source=NULL before → set to 'user_manual' on mark-complete."""
        doc = _make_doc(db, test_tenant)
        ob = _make_obligation(db, test_tenant, doc.id, status="pending", source=None)

        r = auth_client.post(f"/obligations/{ob.id}/mark-complete", json={})
        assert r.status_code == 200

        db.refresh(ob)
        assert ob.source == "user_manual"

    def test_source_preserved_when_already_set(self, auth_client, test_tenant, db):
        """source already set → NOT overwritten."""
        doc = _make_doc(db, test_tenant)
        ob = _make_obligation(db, test_tenant, doc.id, status="pending", source="ai_extracted")

        r = auth_client.post(f"/obligations/{ob.id}/mark-complete", json={})
        assert r.status_code == 200

        db.refresh(ob)
        assert ob.source == "ai_extracted"

    def test_already_done_returns_409(self, auth_client, test_tenant, db):
        """done → 409 Conflict."""
        doc = _make_doc(db, test_tenant)
        ob = _make_obligation(db, test_tenant, doc.id, status="done")

        r = auth_client.post(f"/obligations/{ob.id}/mark-complete", json={})
        assert r.status_code == 409

    def test_cancelled_returns_409(self, auth_client, test_tenant, db):
        """cancelled → 409 Conflict."""
        doc = _make_doc(db, test_tenant)
        ob = _make_obligation(db, test_tenant, doc.id, status="cancelled")

        r = auth_client.post(f"/obligations/{ob.id}/mark-complete", json={})
        assert r.status_code == 409

    def test_waiting_trigger_returns_400(self, auth_client, test_tenant, db):
        """waiting_trigger → 400 Bad Request (trigger event first)."""
        doc = _make_doc(db, test_tenant)
        ob = _make_obligation(db, test_tenant, doc.id, status="waiting_trigger")

        r = auth_client.post(f"/obligations/{ob.id}/mark-complete", json={})
        assert r.status_code == 400
        assert "waiting" in r.json()["detail"].lower() or "trigger" in r.json()["detail"].lower()

    def test_tenant_isolation_returns_404(self, auth_client, test_tenant, db):
        """Obligation belonging to another tenant returns 404."""
        doc = Document(
            tenant_id="other-tenant-xyz",
            file_name="other.pdf",
            file_path="other-tenant-xyz/other.pdf",
            status="extracted",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        ob = Obligation(
            tenant_id="other-tenant-xyz",
            document_id=doc.id,
            description="Other tenant ob",
            obligation_type="payment",
            recurrence="once",
            status="pending",
            due_date="2026-07-05",
        )
        db.add(ob)
        db.commit()
        db.refresh(ob)

        r = auth_client.post(f"/obligations/{ob.id}/mark-complete", json={})
        assert r.status_code == 404

    def test_event_obligation_fulfilled_logged(self, auth_client, test_tenant, db):
        """obligation_fulfilled event is written with correct payload."""
        doc = _make_doc(db, test_tenant)
        ob = _make_obligation(db, test_tenant, doc.id, status="pending")

        r = auth_client.post(f"/obligations/{ob.id}/mark-complete", json={})
        assert r.status_code == 200

        event = (
            db.query(Event)
            .filter(
                Event.tenant_id == test_tenant,
                Event.event_type == "obligation_fulfilled",
                Event.entity_id == ob.id,
            )
            .order_by(Event.id.desc())
            .first()
        )
        assert event is not None
        assert event.actor == "qcuser"
        import json
        payload = json.loads(event.payload)
        assert payload["obligation_id"] == ob.id
        assert payload["previous_status"] == "pending"
        assert payload["fulfilled_by"] == "qcuser"
