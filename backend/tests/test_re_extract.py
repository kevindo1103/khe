"""POST /documents/{id}/re-extract — admin-only re-trigger (#97).

Uses conftest's per-test isolated tenant + admin auth_client.
"""
import os
import sys
from unittest.mock import patch

import pytest

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal
from app.models.master import Tenant, TenantUser
from app.models.tenant import Document, Event
from app.services.consent import revoke_consent


def _make_stuck_doc(test_tenant, db, status="processing"):
    doc = Document(
        tenant_id=test_tenant,
        file_name="stuck.pdf",
        file_path=f"{test_tenant}/stuck.pdf",
        doc_type="hd_thue",
        status=status,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


class TestReExtract:
    def test_re_extract_flips_status_and_enqueues(self, auth_client, test_tenant, db):
        """Happy path: status flips to 'processing' + background task enqueued."""
        doc = _make_stuck_doc(test_tenant, db, status="processing")

        with patch("app.routers.documents.run_extraction") as mock_run:
            r = auth_client.post(f"/documents/{doc.id}/re-extract")

        assert r.status_code == 202
        body = r.json()
        assert body["ok"] is True
        assert body["doc_id"] == doc.id
        assert body["status"] == "processing"

        db.refresh(doc)
        assert doc.status == "processing"

        # Background task was scheduled with the right args (called via _enqueue_extraction).
        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        assert args[0] == doc.id
        assert args[1] == test_tenant

    def test_re_extract_logs_event_with_previous_status(self, auth_client, test_tenant, db):
        """Audit Event captures the previous status (D-02 user-confirm action)."""
        doc = _make_stuck_doc(test_tenant, db, status="failed")

        with patch("app.routers.documents.run_extraction"):
            r = auth_client.post(f"/documents/{doc.id}/re-extract")

        assert r.status_code == 202
        ev = (
            db.query(Event)
            .filter(
                Event.entity_type == "document",
                Event.entity_id == doc.id,
                Event.event_type == "extraction_retriggered",
            )
            .first()
        )
        assert ev is not None
        assert ev.actor == "qcuser"
        assert '"previous_status": "failed"' in (ev.payload or "")

    def test_re_extract_404_other_tenant(self, auth_client, test_tenant, db):
        """Cross-tenant doc → 404 (D-10)."""
        import uuid

        from app.db.database import get_tenant_session, init_tenant_db

        other_id = f"re-iso-{uuid.uuid4().hex[:8]}"
        init_tenant_db(other_id)
        mdb = MasterSessionLocal()
        mdb.add(Tenant(id=other_id, name="Other", db_path=f"tenants/{other_id}.db"))
        mdb.commit()
        mdb.close()
        odb = get_tenant_session(other_id)
        try:
            other_doc = Document(
                tenant_id=other_id, file_name="x.pdf",
                file_path=f"{other_id}/x.pdf", doc_type="hd_thue", status="processing",
            )
            odb.add(other_doc)
            odb.commit()
            odb.refresh(other_doc)
            target_id = other_doc.id
        finally:
            odb.close()

        r = auth_client.post(f"/documents/{target_id}/re-extract")
        assert r.status_code == 404

        # Cleanup
        from tests.conftest import _reset_tenant_db
        _reset_tenant_db(other_id)
        mdb = MasterSessionLocal()
        mdb.query(Tenant).filter(Tenant.id == other_id).delete()
        mdb.commit()
        mdb.close()

    def test_re_extract_403_for_non_admin(self, test_tenant):
        """Staff role cannot re-trigger (admin-only guard)."""
        mdb = MasterSessionLocal()
        mdb.add(
            TenantUser(
                tenant_id=test_tenant,
                username="staffer",
                hashed_password=get_password_hash("staffpass"),
                role="staff",
            )
        )
        mdb.commit()
        mdb.close()

        c = TestClient(__import__("main").app)
        r = c.post(
            "/auth/login",
            json={"tenant_id": test_tenant, "username": "staffer", "password": "staffpass"},
        )
        assert r.status_code == 200
        r = c.post("/documents/1/re-extract")
        assert r.status_code == 403

    def test_re_extract_403_without_consent(self, auth_client, test_tenant, db):
        """Revoked vision_extraction consent → 403, no run_extraction call."""
        doc = _make_stuck_doc(test_tenant, db, status="failed")
        revoke_consent(db, test_tenant, "vision_extraction", actor="qcuser")

        with patch("app.routers.documents.run_extraction") as mock_run:
            r = auth_client.post(f"/documents/{doc.id}/re-extract")

        assert r.status_code == 403
        mock_run.assert_not_called()
        # Status must NOT have flipped to processing.
        db.refresh(doc)
        assert doc.status == "failed"
