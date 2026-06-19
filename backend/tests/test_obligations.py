"""Obligation engine + endpoint tests (#26 PR-A)."""
import io
import os
import sys
from datetime import date, timedelta
from unittest.mock import patch

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Document, Obligation, Term
from app.services.consent import record_consent
from app.services.obligation_engine import derive_obligations
from main import app


def _pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db("obligation-tenant")

    db = MasterSessionLocal()
    tenant = db.query(Tenant).filter(Tenant.id == "obligation-tenant").first()
    if not tenant:
        db.add(Tenant(id="obligation-tenant", name="Obligation Tenant", db_path="tenants/obligation-tenant.db"))
        db.commit()

    user = db.query(TenantUser).filter(TenantUser.tenant_id == "obligation-tenant", TenantUser.username == "obluser").first()
    if not user:
        db.add(
            TenantUser(
                tenant_id="obligation-tenant",
                username="obluser",
                hashed_password=get_password_hash("oblpass"),
                role="staff",
            )
        )
        db.commit()
    db.close()

    tenant_db = get_tenant_session("obligation-tenant")
    record_consent(tenant_db, "obligation-tenant", "vision_extraction", actor="obluser", entity_id=1)
    tenant_db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post(
        "/auth/login",
        json={"tenant_id": "obligation-tenant", "username": "obluser", "password": "oblpass"},
    )
    assert r.status_code == 200
    return c


@pytest.fixture
def db():
    d = get_tenant_session("obligation-tenant")
    try:
        yield d
    finally:
        d.close()


def _make_doc(db, file_name, doc_type=None, status="extracted"):
    doc = Document(tenant_id="obligation-tenant", file_name=file_name, file_path="x/y.pdf", doc_type=doc_type, status=status)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _make_term(db, doc_id, field_name, value, confidence=0.9, needs_review=False):
    t = Term(
        tenant_id="obligation-tenant",
        document_id=doc_id,
        field_name=field_name,
        field_value=value,
        confidence=confidence,
        needs_review=needs_review,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


# ── Derivation logic ──

class TestDeriveObligations:
    def test_direct_due_date(self, db):
        doc = _make_doc(db, "direct_due.pdf")
        _make_term(db, doc.id, "ngay_het_han", "2026-12-31")

        result = derive_obligations(db, "obligation-tenant", doc.id)
        assert result["created"] == 1
        assert result["skipped"] is False

        obs = db.query(Obligation).filter(Obligation.document_id == doc.id).all()
        assert len(obs) == 1
        assert obs[0].obligation_type == "once"
        assert obs[0].due_date == "2026-12-31"
        assert obs[0].status == "pending"
        assert "hết hạn ngày" in obs[0].description

    def test_derive_from_start_and_duration(self, db):
        doc = _make_doc(db, "derived_due.pdf")
        _make_term(db, doc.id, "ngay_hieu_luc", "2026-01-01")
        _make_term(db, doc.id, "thoi_han_hd", "12 tháng")

        result = derive_obligations(db, "obligation-tenant", doc.id)
        assert result["created"] == 1

        obs = db.query(Obligation).filter(Obligation.document_id == doc.id).all()
        assert len(obs) == 1
        assert obs[0].obligation_type == "once"
        # 12 months from 2026-01-01 -> 2027-01-01 (add_months semantics).
        assert obs[0].due_date == "2027-01-01"

    def test_open_ended_review(self, db):
        doc = _make_doc(db, "open_ended.pdf")
        _make_term(db, doc.id, "ngay_hieu_luc", "2026-01-01")
        _make_term(db, doc.id, "thoi_han_hd", "vô thời hạn")

        result = derive_obligations(db, "obligation-tenant", doc.id)
        assert result["created"] == 1

        obs = db.query(Obligation).filter(Obligation.document_id == doc.id).all()
        assert len(obs) == 1
        assert obs[0].obligation_type == "open_ended_review"
        assert obs[0].due_date is None
        # DEC-020: annual review nudge → 365 days, not the `once` default of 30.
        assert obs[0].remind_before_days == 365
        assert "vô thời hạn" in obs[0].description

    def test_once_obligation_uses_30day_window(self, db):
        """Regression: a `once` obligation keeps the 30-day reminder window
        (the DEC-020 365d branch is for open_ended_review only)."""
        doc = _make_doc(db, "once_30d.pdf")
        _make_term(db, doc.id, "ngay_het_han", "2026-12-31")
        derive_obligations(db, "obligation-tenant", doc.id)
        ob = db.query(Obligation).filter(Obligation.document_id == doc.id).first()
        assert ob.obligation_type == "once"
        assert ob.remind_before_days == 30

    def test_insufficient_data_skips(self, db):
        doc = _make_doc(db, "insufficient.pdf")
        _make_term(db, doc.id, "doi_tac", "Công ty A")

        result = derive_obligations(db, "obligation-tenant", doc.id)
        assert result["created"] == 0
        assert result["skipped"] is True
        assert "Insufficient" in result["reason"]

        obs = db.query(Obligation).filter(Obligation.document_id == doc.id).all()
        assert obs == []

    def test_chain_aware_latest_wins(self, db):
        from app.models.tenant import DocumentRelationship
        from app.services.relationships import confirm_relationship

        # Parent doc: expiry 2026-06-01
        parent = _make_doc(db, "parent.pdf")
        _make_term(db, parent.id, "ngay_het_han", "2026-06-01")
        derive_obligations(db, "obligation-tenant", parent.id)

        # Amendment doc: expiry 2026-12-31
        amendment = _make_doc(db, "amendment.pdf")
        _make_term(db, amendment.id, "ngay_het_han", "2026-12-31")

        # Create + confirm amends relationship amendment -> parent
        rel = DocumentRelationship(
            tenant_id="obligation-tenant",
            from_doc_id=amendment.id,
            to_doc_id=parent.id,
            relationship_type="amends",
            status="pending",
            confirmed_by_sme=False,
        )
        db.add(rel)
        db.commit()
        db.refresh(rel)

        confirm_relationship(db, "obligation-tenant", amendment.id, rel.id, actor="obluser")

        # Exactly one obligation per chain, attached to the terminal (amendment) doc.
        all_obs = db.query(Obligation).filter(
            Obligation.tenant_id == "obligation-tenant",
            Obligation.document_id.in_([parent.id, amendment.id]),
        ).all()
        assert len(all_obs) == 1
        ob = all_obs[0]
        assert ob.document_id == amendment.id
        assert ob.due_date == "2026-12-31"
        assert ob.resolution_method == "last_writer_wins"
        assert ob.source_doc_chain is not None
        assert str(parent.id) in ob.source_doc_chain
        assert str(amendment.id) in ob.source_doc_chain

    def test_idempotency_preserves_done(self, db):
        doc = _make_doc(db, "idempotent.pdf")
        _make_term(db, doc.id, "ngay_het_han", "2026-12-31")

        derive_obligations(db, "obligation-tenant", doc.id)
        ob = db.query(Obligation).filter(Obligation.document_id == doc.id).first()
        assert ob is not None

        # Mark as done and update term to a new due date.
        ob.status = "done"
        db.commit()
        db.query(Term).filter(Term.document_id == doc.id, Term.field_name == "ngay_het_han").update(
            {"field_value": "2027-01-01"}
        )
        db.commit()

        # Re-derive should create a new pending obligation, not delete the done one.
        result = derive_obligations(db, "obligation-tenant", doc.id)
        assert result["created"] == 1

        obs = db.query(Obligation).filter(Obligation.document_id == doc.id).order_by(Obligation.id).all()
        assert len(obs) == 2
        assert obs[0].status == "done"
        assert obs[0].due_date == "2026-12-31"
        assert obs[1].status == "pending"
        assert obs[1].due_date == "2027-01-01"


# ── Endpoints ──

class TestObligationEndpoints:
    def _upload_and_extract(self, auth_client, file_name, fields):
        from modules.extraction import DocType, ExtractedField, ExtractionResult, TokenUsage

        class FakeProvider:
            name = "fake"

            def __init__(self, result):
                self._result = result

            async def extract(self, image_bytes, doc_type="auto"):
                return self._result

        result = ExtractionResult(
            doc_type=DocType.LEASE,
            doc_type_confidence=0.95,
            fields={k: ExtractedField(value=v, confidence=0.9, needs_review=False) for k, v in fields.items()},
            provider="fake",
            model="fake",
            latency_ms=1.0,
            usage=TokenUsage(input_tokens=1, output_tokens=1),
            cost_vnd=0.0,
        )
        fake = FakeProvider(result)
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": (file_name, io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            return r.json()["doc_id"]

    def test_list_obligations(self, auth_client):
        doc_id = self._upload_and_extract(
            auth_client,
            "list_obl.pdf",
            {"ngay_het_han": "2026-12-31", "ngay_hieu_luc": "2026-01-01"},
        )

        r = auth_client.get("/obligations")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        assert any(ob["document_id"] == doc_id for ob in data["items"])

    def test_list_due_within_filter(self, auth_client):
        today_str = date.today().strftime("%Y-%m-%d")
        doc_id = self._upload_and_extract(auth_client, "due_today.pdf", {"ngay_het_han": today_str})

        r = auth_client.get("/obligations?due_within=0")
        assert r.status_code == 200
        data = r.json()
        assert any(ob["document_id"] == doc_id for ob in data["items"])

        r2 = auth_client.get("/obligations?due_within=0&status=pending")
        assert r2.status_code == 200
        assert any(ob["document_id"] == doc_id for ob in r2.json()["items"])

    def test_patch_obligation(self, auth_client):
        doc_id = self._upload_and_extract(auth_client, "patch_obl.pdf", {"ngay_het_han": "2026-12-31"})

        r = auth_client.get("/obligations")
        ob = next(ob for ob in r.json()["items"] if ob["document_id"] == doc_id)

        r2 = auth_client.patch(f"/obligations/{ob['id']}", json={"status": "done"})
        assert r2.status_code == 200
        assert r2.json()["obligation"]["status"] == "done"

        r3 = auth_client.patch(f"/obligations/{ob['id']}", json={"status": "invalid"})
        assert r3.status_code == 400

    def test_document_rollup(self, auth_client):
        doc_id = self._upload_and_extract(auth_client, "rollup.pdf", {"ngay_het_han": "2026-12-31"})

        r = auth_client.get("/documents")
        assert r.status_code == 200
        item = next(i for i in r.json()["items"] if i["id"] == doc_id)
        assert item["obligation_count"] >= 1

        r2 = auth_client.get(f"/documents/{doc_id}")
        assert r2.status_code == 200
        assert len(r2.json()["obligations"]) >= 1

    def test_cross_tenant_isolation(self, auth_client):
        # Create another tenant with a user.
        init_tenant_db("other-obl-tenant")
        db = MasterSessionLocal()
        if not db.query(Tenant).filter(Tenant.id == "other-obl-tenant").first():
            db.add(Tenant(id="other-obl-tenant", name="Other", db_path="tenants/other-obl-tenant.db"))
            db.commit()
        if not db.query(TenantUser).filter(TenantUser.tenant_id == "other-obl-tenant", TenantUser.username == "otheruser").first():
            db.add(
                TenantUser(
                    tenant_id="other-obl-tenant",
                    username="otheruser",
                    hashed_password=get_password_hash("otherpass"),
                    role="staff",
                )
            )
            db.commit()
        db.close()

        # Upload as obligation-tenant
        doc_id = self._upload_and_extract(auth_client, "cross.pdf", {"ngay_het_han": "2026-12-31"})
        r = auth_client.get("/obligations")
        ob = next(o for o in r.json()["items"] if o["document_id"] == doc_id)

        # Login as other tenant
        other_client = TestClient(app)
        login = other_client.post(
            "/auth/login",
            json={"tenant_id": "other-obl-tenant", "username": "otheruser", "password": "otherpass"},
        )
        assert login.status_code == 200

        r2 = other_client.get("/obligations")
        assert r2.status_code == 200
        assert not any(o["id"] == ob["id"] for o in r2.json()["items"])

        r3 = other_client.patch(f"/obligations/{ob['id']}", json={"status": "done"})
        assert r3.status_code == 404
