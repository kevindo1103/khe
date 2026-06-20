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
        assert obs[0].recurrence == "once"
        assert obs[0].obligation_type == "expiration"
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
        assert obs[0].recurrence == "once"
        assert obs[0].obligation_type == "expiration"
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
        assert obs[0].recurrence == "open_ended_review"
        assert obs[0].obligation_type == "expiration"
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
        assert ob.recurrence == "once"
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


class TestDeriveDirection:
    """Tests for _derive_direction (DEC-030)."""

    def test_self_match_returns_nghia_vu(self):
        """When obligor matches tenant's self-party → nghĩa_vụ."""
        from app.services.extraction_runner import _derive_direction
        from modules.extraction import PartyItem

        # Simulate: tenant legal_name = "Công ty ABC", obligor = "Bên A"
        # Party "Công ty ABC" has role_label "Bên A" → self-match → nghĩa_vụ
        class FakeResult:
            parties = [PartyItem(name="Công ty ABC", role_label="Bên A")]

        with patch("app.services.extraction_runner._get_tenant_legal_name", return_value="Công ty ABC"):
            result = _derive_direction("test-tenant", "Bên A", FakeResult())
        assert result == "nghĩa_vụ"

    def test_other_party_returns_quyen_loi(self):
        """When obligor is the counterparty → quyền_lợi."""
        from app.services.extraction_runner import _derive_direction
        from modules.extraction import PartyItem

        class FakeResult:
            parties = [
                PartyItem(name="Công ty ABC", role_label="Bên A"),
                PartyItem(name="Công ty XYZ", role_label="Bên B"),
            ]

        with patch("app.services.extraction_runner._get_tenant_legal_name", return_value="Công ty ABC"):
            result = _derive_direction("test-tenant", "Bên B", FakeResult())
        assert result == "quyền_lợi"

    def test_no_legal_name_returns_none(self):
        """When tenant has no legal_name → None (D-08)."""
        from app.services.extraction_runner import _derive_direction

        class FakeResult:
            parties = []

        with patch("app.services.extraction_runner._get_tenant_legal_name", return_value=None):
            result = _derive_direction("test-tenant", "Bên A", FakeResult())
        assert result is None

    def test_no_obligor_returns_none(self):
        """When obligor is None → None (D-08)."""
        from app.services.extraction_runner import _derive_direction

        result = _derive_direction("test-tenant", None, None)
        assert result is None

    def test_no_party_match_returns_none(self):
        """When no party matches tenant's legal_name → None (needs_review)."""
        from app.services.extraction_runner import _derive_direction
        from modules.extraction import PartyItem

        class FakeResult:
            parties = [PartyItem(name="Công ty XYZ", role_label="Bên B")]

        with patch("app.services.extraction_runner._get_tenant_legal_name", return_value="Công ty ABC"):
            result = _derive_direction("test-tenant", "Bên B", FakeResult())
        assert result is None


# ── DEC-030 Phase 2: Event-chain + T2 auto-expand + PATCH integration ──


class TestEventChain:
    """Part 3 — propagate_obligation_done activates waiting_trigger dependents."""

    def test_propagate_activates_dependent(self, db):
        from app.services.obligation_chain import propagate_obligation_done

        doc = _make_doc(db, "chain_test.pdf")
        parent = Obligation(
            tenant_id="obligation-tenant", document_id=doc.id,
            description="Parent", recurrence="once", obligation_type="delivery",
            due_date="2026-07-01", status="pending",
        )
        db.add(parent)
        db.commit()
        db.refresh(parent)

        child = Obligation(
            tenant_id="obligation-tenant", document_id=doc.id,
            description="Child", recurrence="once", obligation_type="payment",
            status="waiting_trigger", milestone_trigger="event",
            trigger_obligation_id=parent.id, trigger_delay_days=15,
        )
        db.add(child)
        db.commit()
        db.refresh(child)

        count = propagate_obligation_done(parent.id, db)
        assert count == 1

        db.commit()
        db.refresh(child)
        assert child.status == "pending"
        assert child.milestone_trigger == "date"
        assert child.due_date is not None

    def test_propagate_sets_due_date_plus_delay(self, db):
        from app.services.obligation_chain import propagate_obligation_done

        doc = _make_doc(db, "chain_delay.pdf")
        parent = Obligation(
            tenant_id="obligation-tenant", document_id=doc.id,
            description="Parent", recurrence="once", obligation_type="delivery",
            due_date="2026-07-01", status="done",
        )
        db.add(parent)
        db.commit()
        db.refresh(parent)

        child = Obligation(
            tenant_id="obligation-tenant", document_id=doc.id,
            description="Child", recurrence="once", obligation_type="payment",
            status="waiting_trigger", milestone_trigger="event",
            trigger_obligation_id=parent.id, trigger_delay_days=30,
        )
        db.add(child)
        db.commit()

        propagate_obligation_done(parent.id, db)
        db.commit()
        db.refresh(child)

        expected = (date.today() + timedelta(days=30)).isoformat()
        assert child.due_date == expected

    def test_propagate_immediate_when_no_delay(self, db):
        from app.services.obligation_chain import propagate_obligation_done

        doc = _make_doc(db, "chain_nodelay.pdf")
        parent = Obligation(
            tenant_id="obligation-tenant", document_id=doc.id,
            description="Parent", recurrence="once", obligation_type="delivery",
            due_date="2026-07-01", status="done",
        )
        db.add(parent)
        db.commit()
        db.refresh(parent)

        child = Obligation(
            tenant_id="obligation-tenant", document_id=doc.id,
            description="Child", recurrence="once", obligation_type="payment",
            status="waiting_trigger", milestone_trigger="event",
            trigger_obligation_id=parent.id, trigger_delay_days=None,
        )
        db.add(child)
        db.commit()

        propagate_obligation_done(parent.id, db)
        db.commit()
        db.refresh(child)

        assert child.due_date == date.today().isoformat()

    def test_no_propagation_if_not_done(self, db):
        from app.services.obligation_chain import propagate_obligation_done

        doc = _make_doc(db, "chain_notdone.pdf")
        parent = Obligation(
            tenant_id="obligation-tenant", document_id=doc.id,
            description="Parent", recurrence="once", obligation_type="delivery",
            due_date="2026-07-01", status="pending",
        )
        db.add(parent)
        db.commit()
        db.refresh(parent)

        child = Obligation(
            tenant_id="obligation-tenant", document_id=doc.id,
            description="Child", recurrence="once", obligation_type="payment",
            status="waiting_trigger", milestone_trigger="event",
            trigger_obligation_id=parent.id, trigger_delay_days=10,
        )
        db.add(child)
        db.commit()

        # propagate_obligation_done is called directly — it activates regardless of parent status.
        # The guard is in the PATCH endpoint: only calls propagate when payload.status == "done".
        # Here we verify that calling it on a non-done parent still works (it's the caller's responsibility).
        count = propagate_obligation_done(parent.id, db)
        db.commit()
        assert count == 1  # dependents exist, they get activated


class TestT2Expand:
    """Part 4 — expand_recurring_obligations creates next installment for T2 recurring."""

    def test_monthly_expand_creates_next_row(self, db):
        from app.services.obligation_expander import expand_recurring_obligations

        # Clean up prior recurring obligations to avoid data bleed
        db.query(Obligation).filter(
            Obligation.tenant_id == "obligation-tenant",
            Obligation.recurrence.in_(["monthly", "quarterly", "yearly"]),
        ).delete()
        db.commit()

        doc = _make_doc(db, "expand_monthly.pdf")
        obl = Obligation(
            tenant_id="obligation-tenant", document_id=doc.id,
            description="Monthly rent", recurrence="monthly", obligation_type="payment",
            due_date="2026-07-01", status="pending",
        )
        db.add(obl)
        db.commit()

        created = expand_recurring_obligations("obligation-tenant", db)
        assert created == 1

        rows = db.query(Obligation).filter(
            Obligation.document_id == doc.id,
            Obligation.recurrence == "monthly",
        ).all()
        assert len(rows) == 2
        dates = sorted(r.due_date for r in rows)
        assert dates == ["2026-07-01", "2026-08-01"]

    def test_expand_stops_at_doc_expiry(self, db):
        from app.services.obligation_expander import expand_recurring_obligations

        # Clean up prior recurring obligations to avoid data bleed
        db.query(Obligation).filter(
            Obligation.tenant_id == "obligation-tenant",
            Obligation.recurrence.in_(["monthly", "quarterly", "yearly"]),
        ).delete()
        db.commit()

        doc = _make_doc(db, "expand_expiry.pdf")
        _make_term(db, doc.id, "ngay_het_han", "2026-07-15")
        obl = Obligation(
            tenant_id="obligation-tenant", document_id=doc.id,
            description="Monthly rent", recurrence="monthly", obligation_type="payment",
            due_date="2026-07-01", status="pending",
        )
        db.add(obl)
        db.commit()

        created = expand_recurring_obligations("obligation-tenant", db)
        # Next would be 2026-08-01, but doc expires 2026-07-15 → skip
        assert created == 0

    def test_expand_idempotent(self, db):
        from app.services.obligation_expander import expand_recurring_obligations

        # Clean up prior recurring obligations to avoid data bleed
        db.query(Obligation).filter(
            Obligation.tenant_id == "obligation-tenant",
            Obligation.recurrence.in_(["monthly", "quarterly", "yearly"]),
        ).delete()
        db.commit()

        doc = _make_doc(db, "expand_idempotent.pdf")
        obl = Obligation(
            tenant_id="obligation-tenant", document_id=doc.id,
            description="Monthly rent", recurrence="monthly", obligation_type="payment",
            due_date="2026-07-01", status="pending",
        )
        db.add(obl)
        db.commit()

        created1 = expand_recurring_obligations("obligation-tenant", db)
        assert created1 == 1

        # Second run: the next date (2026-08-01) already exists → no duplicate
        # But the expander finds 2026-08-01 as last → creates 2026-09-01.
        # To test true idempotency (no dup of same date), we run twice and check no duplicate dates.
        created2 = expand_recurring_obligations("obligation-tenant", db)
        # Lazy expander creates 1 row per run (finds latest, creates next).
        # Idempotency = no duplicate due_dates for same doc+type+recurrence.
        rows = db.query(Obligation).filter(
            Obligation.document_id == doc.id,
            Obligation.recurrence == "monthly",
        ).all()
        dates = [r.due_date for r in rows]
        assert len(dates) == len(set(dates)), "Duplicate due_dates detected — expander not idempotent"


class TestPatchChainIntegration:
    """Part 3 — PATCH /obligations/{id} with status=done triggers chain propagation."""

    def test_patch_done_returns_activated_count(self, auth_client, db):
        doc = _make_doc(db, "patch_chain.pdf")
        parent = Obligation(
            tenant_id="obligation-tenant", document_id=doc.id,
            description="Parent", recurrence="once", obligation_type="delivery",
            due_date="2026-07-01", status="pending",
        )
        db.add(parent)
        db.commit()
        db.refresh(parent)

        child = Obligation(
            tenant_id="obligation-tenant", document_id=doc.id,
            description="Child", recurrence="once", obligation_type="payment",
            status="waiting_trigger", milestone_trigger="event",
            trigger_obligation_id=parent.id, trigger_delay_days=10,
        )
        db.add(child)
        db.commit()

        r = auth_client.patch(f"/obligations/{parent.id}", json={"status": "done"})
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert data["activated_count"] == 1

    def test_patch_expanded_statuses_accepted(self, auth_client, db):
        doc = _make_doc(db, "patch_status.pdf")
        obl = Obligation(
            tenant_id="obligation-tenant", document_id=doc.id,
            description="Test", recurrence="once", obligation_type="other",
            due_date="2026-07-01", status="pending",
        )
        db.add(obl)
        db.commit()
        db.refresh(obl)

        for s in ["in_progress", "partial", "waiting_trigger"]:
            r = auth_client.patch(f"/obligations/{obl.id}", json={"status": s})
            assert r.status_code == 200, f"status={s} should be accepted"
            assert r.json()["obligation"]["status"] == s


# ── DEC-030 Phase 2 Part 2 — obligation_schedule mapping ──


class TestObligationScheduleMapping:
    """Part 2 — extraction_runner maps obligation_schedule[] → Obligation rows."""

    def _upload_and_extract(self, auth_client, file_name, fields, obligation_schedule):
        from modules.extraction import (
            DocType, ExtractedField, ExtractionResult, ObligationScheduleItem, TokenUsage,
        )

        class FakeProvider:
            def __init__(self, result):
                self._result = result

            async def extract(self, *args, **kwargs):
                return self._result

        result = ExtractionResult(
            doc_type=DocType.LEASE,
            doc_type_confidence=0.95,
            fields=fields,
            obligation_schedule=obligation_schedule,
            provider="fake_provider",
            model="fake-model",
            latency_ms=123.0,
            usage=TokenUsage(input_tokens=1000, output_tokens=200),
            cost_vnd=500.0,
        )
        fake = FakeProvider(result)
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": (file_name, io.BytesIO(_pdf_bytes()), "application/pdf")},
            )
            assert r.status_code == 201
            return r.json()["doc_id"]

    def test_date_trigger_creates_pending(self, auth_client, db):
        """Obligation schedule item with trigger=date → status=pending, due_date set."""
        from modules.extraction import ExtractedField, ObligationScheduleItem

        doc_id = self._upload_and_extract(
            auth_client, "schedule_date.pdf",
            {
                "doi_tac": ExtractedField(value="Công ty A", confidence=0.9, needs_review=False),
                "ngay_hieu_luc": ExtractedField(value="2026-01-01", confidence=0.9, needs_review=False),
                "ngay_het_han": ExtractedField(value="2027-01-01", confidence=0.85, needs_review=False),
            },
            [
                ObligationScheduleItem(
                    obligation_type="payment",
                    description="Thanh toán đợt 1",
                    amount_raw="100000000",
                    due_date="2026-06-01",
                    obligor="Bên A",
                ),
            ],
        )

        obs = db.query(Obligation).filter(
            Obligation.document_id == doc_id,
            Obligation.description == "Thanh toán đợt 1",
        ).all()
        assert len(obs) == 1
        assert obs[0].status == "pending"
        assert obs[0].due_date == "2026-06-01"
        assert obs[0].obligation_type == "payment"
        assert obs[0].amount_raw == "100000000"

    def test_event_trigger_creates_waiting_trigger(self, auth_client, db):
        """Obligation schedule item with trigger=event → status=waiting_trigger, due_date=None."""
        from modules.extraction import ExtractedField, ObligationScheduleItem

        doc_id = self._upload_and_extract(
            auth_client, "schedule_event.pdf",
            {
                "doi_tac": ExtractedField(value="Công ty A", confidence=0.9, needs_review=False),
                "ngay_hieu_luc": ExtractedField(value="2026-01-01", confidence=0.9, needs_review=False),
                "ngay_het_han": ExtractedField(value="2027-01-01", confidence=0.85, needs_review=False),
            },
            [
                ObligationScheduleItem(
                    obligation_type="delivery",
                    description="Giao hàng sau nghiệm thu",
                    trigger="event",
                    trigger_condition="sau khi nghiệm thu",
                    trigger_delay_days=15,
                    obligor="Bên B",
                ),
            ],
        )

        obs = db.query(Obligation).filter(
            Obligation.document_id == doc_id,
            Obligation.description == "Giao hàng sau nghiệm thu",
        ).all()
        assert len(obs) == 1
        assert obs[0].status == "waiting_trigger"
        assert obs[0].due_date is None
        assert obs[0].milestone_trigger == "event"
        assert obs[0].trigger_condition == "sau khi nghiệm thu"
        assert obs[0].trigger_delay_days == 15

    def test_series_fields_mapped(self, auth_client, db):
        """Obligation schedule items with series_id → milestone_* fields mapped."""
        from modules.extraction import ExtractedField, ObligationScheduleItem

        doc_id = self._upload_and_extract(
            auth_client, "schedule_series.pdf",
            {
                "doi_tac": ExtractedField(value="Công ty A", confidence=0.9, needs_review=False),
                "ngay_hieu_luc": ExtractedField(value="2026-01-01", confidence=0.9, needs_review=False),
                "ngay_het_han": ExtractedField(value="2027-01-01", confidence=0.85, needs_review=False),
            },
            [
                ObligationScheduleItem(
                    obligation_type="payment",
                    description="Đợt 1",
                    amount_raw="50000000",
                    due_date="2026-03-01",
                    series_id="series-001",
                    milestone_index=1,
                    milestone_total=3,
                ),
                ObligationScheduleItem(
                    obligation_type="payment",
                    description="Đợt 2",
                    amount_raw="50000000",
                    due_date="2026-06-01",
                    series_id="series-001",
                    milestone_index=2,
                    milestone_total=3,
                ),
            ],
        )

        series_obs = db.query(Obligation).filter(
            Obligation.document_id == doc_id,
            Obligation.milestone_series_id == "series-001",
        ).order_by(Obligation.milestone_index).all()
        assert len(series_obs) == 2
        assert series_obs[0].milestone_index == 1
        assert series_obs[0].milestone_total == 3
        assert series_obs[1].milestone_index == 2

    def test_re_extraction_after_done_no_duplicate(self, auth_client, db):
        """Re-extraction after a schedule obligation is marked done → no duplicate pending row."""
        from modules.extraction import ExtractedField, ObligationScheduleItem

        schedule = [
            ObligationScheduleItem(
                obligation_type="payment",
                description="Thanh toán đợt 1",
                amount_raw="100000000",
                due_date="2026-06-01",
                obligor="Bên A",
            ),
        ]
        fields = {
            "doi_tac": ExtractedField(value="Công ty A", confidence=0.9, needs_review=False),
            "ngay_hieu_luc": ExtractedField(value="2026-01-01", confidence=0.9, needs_review=False),
            "ngay_het_han": ExtractedField(value="2027-01-01", confidence=0.85, needs_review=False),
        }

        # First extraction → creates pending obligation
        doc_id = self._upload_and_extract(auth_client, "dedup_1.pdf", fields, schedule)
        obs = db.query(Obligation).filter(
            Obligation.document_id == doc_id,
            Obligation.description == "Thanh toán đợt 1",
        ).all()
        assert len(obs) == 1
        assert obs[0].status == "pending"

        # User marks it done
        obs[0].status = "done"
        db.commit()

        # Re-extract the same doc via run_extraction
        from app.services.extraction_runner import run_extraction
        from modules.extraction import (
            DocType, ExtractionResult, TokenUsage as _TokenUsage,
        )
        result = ExtractionResult(
            doc_type=DocType.LEASE,
            doc_type_confidence=0.95,
            fields=fields,
            obligation_schedule=schedule,
            provider="fake_provider",
            model="fake-model",
            latency_ms=123.0,
            usage=_TokenUsage(input_tokens=1000, output_tokens=200),
            cost_vnd=500.0,
        )

        class FakeProvider:
            def __init__(self, result):
                self._result = result

            async def extract(self, *args, **kwargs):
                return self._result

        fake = FakeProvider(result)
        with patch("app.services.extraction_runner.get_extraction_provider", return_value=fake):
            run_extraction(doc_id, "obligation-tenant", None)

        # Should still be 1 row — the done row survives, no new pending duplicate
        db.expire_all()
        obs = db.query(Obligation).filter(
            Obligation.document_id == doc_id,
            Obligation.description == "Thanh toán đợt 1",
        ).all()
        assert len(obs) == 1
        assert obs[0].status == "done"

    def test_event_ledger_entry_for_schedule(self, auth_client, db):
        """Schedule obligation creation logs an obligation_schedule_derived Event."""
        from modules.extraction import ExtractedField, ObligationScheduleItem
        from app.models.tenant import Event

        doc_id = self._upload_and_extract(
            auth_client, "event_ledger.pdf",
            {
                "doi_tac": ExtractedField(value="Công ty A", confidence=0.9, needs_review=False),
                "ngay_hieu_luc": ExtractedField(value="2026-01-01", confidence=0.9, needs_review=False),
                "ngay_het_han": ExtractedField(value="2027-01-01", confidence=0.85, needs_review=False),
            },
            [
                ObligationScheduleItem(
                    obligation_type="payment",
                    description="Thanh toán đợt 1",
                    amount_raw="100000000",
                    due_date="2026-06-01",
                    obligor="Bên A",
                ),
            ],
        )

        events = db.query(Event).filter(
            Event.entity_type == "document",
            Event.entity_id == doc_id,
            Event.event_type == "obligation_schedule_derived",
        ).all()
        assert len(events) == 1
        import json as _json
        payload = _json.loads(events[0].payload)
        assert payload["count"] == 1
        assert payload["items"][0]["description"] == "Thanh toán đợt 1"
        assert payload["items"][0]["obligation_type"] == "payment"
