"""Tests for extended party details + self-mapping (#364 R2)."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.database import get_tenant_session
from app.models.tenant import Document, Event, Party


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_doc(db, tenant_id, status="pending"):
    doc = Document(
        tenant_id=tenant_id,
        file_name="contract.pdf",
        file_path=f"{tenant_id}/contract.pdf",
        status=status,
        is_evidence=False,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _make_party(db, tenant_id, doc_id, name="Test Party", role_label="Bên A", is_self=False):
    party = Party(
        tenant_id=tenant_id,
        document_id=doc_id,
        name=name,
        role_label=role_label,
        is_self=is_self,
    )
    db.add(party)
    db.commit()
    db.refresh(party)
    return party


def _make_mock_result(parties=None):
    """Build ExtractionResult mock with optional party list."""
    from modules.extraction.schemas import TokenUsage
    result = MagicMock()
    result.is_error = False
    result.doc_type = MagicMock()
    result.doc_type.value = "supply"
    result.provider = "mock"
    result.model = "mock-model"
    result.cost_vnd = 0.0
    result.latency_ms = 100.0
    result.warnings = []
    result.usage = TokenUsage(input_tokens=10, output_tokens=5)
    result.clauses = []
    result.fields = {}
    result.obligation_schedule = []
    result.parties = parties or []
    result.defined_terms = []
    result.cross_references = []
    result.has_signature = False
    result.signature_pages = []
    result.ocr_text = None
    return result


def _make_party_item(name, role_label=None, address=None, contact=None,
                     representative=None, tax_code=None, aliases=None):
    p = MagicMock()
    p.name = name
    p.role_label = role_label
    p.address = address
    p.contact = contact
    p.representative = representative
    p.tax_code = tax_code
    p.aliases = aliases
    return p


def _run_mock_extraction(tenant_id, tmp_path, mock_result):
    """Run extraction with a given mock result and return the doc record."""
    from app.services.extraction_runner import run_extraction

    db = get_tenant_session(tenant_id)
    try:
        doc = Document(
            tenant_id=tenant_id,
            file_name="contract.pdf",
            file_path=f"{tenant_id}/contract.pdf",
            status="pending",
            is_evidence=False,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        doc_id = doc.id
    finally:
        db.close()

    fake_file = tmp_path / tenant_id / "contract.pdf"
    fake_file.parent.mkdir(parents=True, exist_ok=True)
    fake_file.write_bytes(b"fake pdf content")

    mock_provider = AsyncMock()
    mock_provider.extract = AsyncMock(return_value=mock_result)

    with patch("app.services.extraction_runner.settings") as mock_settings, \
         patch("app.services.extraction_runner.get_extraction_provider", return_value=mock_provider), \
         patch("app.services.extraction_runner.check_extraction_consent", return_value=True), \
         patch("app.services.extraction_runner.get_active_consent_reference", return_value="ref-1"), \
         patch("app.services.extraction_runner.quota.add_extraction_cost_standalone"), \
         patch("app.services.extraction_runner.tenant_journey.advance_stage_standalone"), \
         patch("app.services.extraction_runner.derive_obligations"), \
         patch("app.services.extraction_runner.resolve_date_anchored_obligations"):
        mock_settings.STORAGE_DIR = tmp_path
        run_extraction(doc_id, tenant_id)

    db2 = get_tenant_session(tenant_id)
    try:
        db2.expire_all()
        parties = (
            db2.query(Party)
            .filter(Party.document_id == doc_id, Party.tenant_id == tenant_id)
            .all()
        )
        # Detach from session by converting to plain dicts
        return [
            {
                "name": p.name,
                "role_label": p.role_label,
                "address": p.address,
                "contact": p.contact,
                "representative": p.representative,
                "tax_code": p.tax_code,
                "is_self": p.is_self,
                "aliases": p.aliases,
            }
            for p in parties
        ]
    finally:
        db2.close()


# ── Model column tests ────────────────────────────────────────────────────────


def test_party_has_extended_columns(test_tenant, db):
    """Party model has the 6 new columns from tenant_022."""
    doc = _make_doc(db, test_tenant, status="extracted")
    party = _make_party(db, test_tenant, doc.id)
    for col in ("address", "contact", "representative", "tax_code", "is_self", "aliases"):
        assert hasattr(party, col), f"Party missing column: {col}"
    assert party.address is None
    assert party.contact is None
    assert party.representative is None
    assert party.tax_code is None
    assert party.is_self is False or party.is_self == 0
    assert party.aliases is None


# ── Extraction runner: new fields populated ───────────────────────────────────


def test_extraction_populates_party_details(test_tenant, tmp_path):
    """Extraction populates address/contact/representative/tax_code from result."""
    party_item = _make_party_item(
        name="Công ty ABC",
        role_label="Bên A",
        address="123 Nguyễn Huệ, Q.1, TP.HCM",
        contact="028-1234567",
        representative="Nguyễn Văn A - Giám đốc",
        tax_code="0123456789",
    )
    result = _make_mock_result(parties=[party_item])
    parties = _run_mock_extraction(test_tenant, tmp_path, result)

    assert len(parties) == 1
    p = parties[0]
    assert p["address"] == "123 Nguyễn Huệ, Q.1, TP.HCM"
    assert p["contact"] == "028-1234567"
    assert p["representative"] == "Nguyễn Văn A - Giám đốc"
    assert p["tax_code"] == "0123456789"


def test_extraction_populates_aliases(test_tenant, tmp_path):
    """Extraction stores aliases as JSON array."""
    party_item = _make_party_item(
        name="TRAVELODGE HOLDINGS",
        role_label="Bên Cấp phép",
        aliases=["TL", "Bên Cấp phép"],
    )
    result = _make_mock_result(parties=[party_item])
    parties = _run_mock_extraction(test_tenant, tmp_path, result)

    assert len(parties) == 1
    raw = parties[0]["aliases"]
    assert raw is not None
    parsed = json.loads(raw)
    assert "TL" in parsed


def test_extraction_null_aliases_when_absent(test_tenant, tmp_path):
    """aliases stays NULL when not provided by AI."""
    party_item = _make_party_item(name="Bên không có alias", role_label="Bên B", aliases=None)
    result = _make_mock_result(parties=[party_item])
    parties = _run_mock_extraction(test_tenant, tmp_path, result)

    assert len(parties) == 1
    assert parties[0]["aliases"] is None


# ── is_self auto-mapping ──────────────────────────────────────────────────────


def test_extraction_is_self_auto_mapped_on_name_match(tenant_with_legal_name, tmp_path):
    """Party whose name matches tenant legal_name gets is_self=True."""
    tenant_id = tenant_with_legal_name  # legal_name = "Công ty TNHH Test ABC"
    party_items = [
        _make_party_item(name="Công ty TNHH Test ABC", role_label="Bên A"),
        _make_party_item(name="Đối tác XYZ", role_label="Bên B"),
    ]
    result = _make_mock_result(parties=party_items)
    parties = _run_mock_extraction(tenant_id, tmp_path, result)

    self_parties = [p for p in parties if p["is_self"]]
    other_parties = [p for p in parties if not p["is_self"]]
    assert len(self_parties) == 1
    assert self_parties[0]["name"] == "Công ty TNHH Test ABC"
    assert len(other_parties) == 1


def test_extraction_is_self_false_when_no_legal_name(test_tenant, tmp_path):
    """No legal_name in tenant_profile → is_self stays False for all parties."""
    party_item = _make_party_item(name="Bên Ký Kết", role_label="Bên A")
    result = _make_mock_result(parties=[party_item])
    parties = _run_mock_extraction(test_tenant, tmp_path, result)

    assert len(parties) == 1
    assert not parties[0]["is_self"]


def test_extraction_is_self_partial_match(tenant_with_legal_name, tmp_path):
    """Partial substring match still sets is_self (normalized diacritics)."""
    tenant_id = tenant_with_legal_name  # legal_name = "Công ty TNHH Test ABC"
    # "Test ABC" is substring of the normalized legal_name
    party_item = _make_party_item(name="Test ABC", role_label="Bên bán")
    result = _make_mock_result(parties=[party_item])
    parties = _run_mock_extraction(tenant_id, tmp_path, result)

    assert len(parties) == 1
    assert parties[0]["is_self"]


# ── PATCH /documents/{doc_id}/parties/{party_id} ─────────────────────────────


def test_patch_party_updates_field(auth_client, test_tenant, db):
    """PATCH party field → 200, updated value returned."""
    doc = _make_doc(db, test_tenant, status="extracted")
    party = _make_party(db, test_tenant, doc.id, name="Công ty ABC")

    r = auth_client.patch(
        f"/documents/{doc.id}/parties/{party.id}",
        json={"address": "456 Lê Lợi, Q.1"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["address"] == "456 Lê Lợi, Q.1"
    assert data["name"] == "Công ty ABC"


def test_patch_party_logs_event(auth_client, test_tenant, db):
    """PATCH party field → party_field_edited Event is written."""
    doc = _make_doc(db, test_tenant, status="extracted")
    party = _make_party(db, test_tenant, doc.id, name="Công ty XYZ")

    r = auth_client.patch(
        f"/documents/{doc.id}/parties/{party.id}",
        json={"tax_code": "9876543210"},
    )
    assert r.status_code == 200

    ev = (
        db.query(Event)
        .filter(
            Event.tenant_id == test_tenant,
            Event.entity_id == party.id,
            Event.event_type == "party_field_edited",
        )
        .first()
    )
    assert ev is not None
    payload = json.loads(ev.payload)
    assert payload["field"] == "tax_code"
    assert payload["new_value"] == "9876543210"


def test_patch_party_multiple_fields_logs_multiple_events(auth_client, test_tenant, db):
    """PATCH with 2 fields writes 2 events."""
    doc = _make_doc(db, test_tenant, status="extracted")
    party = _make_party(db, test_tenant, doc.id)

    r = auth_client.patch(
        f"/documents/{doc.id}/parties/{party.id}",
        json={"address": "123 Đường ABC", "contact": "090-1234567"},
    )
    assert r.status_code == 200

    events = (
        db.query(Event)
        .filter(
            Event.tenant_id == test_tenant,
            Event.entity_id == party.id,
            Event.event_type == "party_field_edited",
        )
        .all()
    )
    assert len(events) == 2
    fields = {json.loads(e.payload)["field"] for e in events}
    assert fields == {"address", "contact"}


def test_patch_party_404_unknown_doc(auth_client):
    """PATCH on unknown doc → 404."""
    r = auth_client.patch("/documents/99999/parties/1", json={"address": "x"})
    assert r.status_code == 404


def test_patch_party_404_unknown_party(auth_client, test_tenant, db):
    """PATCH on known doc but unknown party → 404."""
    doc = _make_doc(db, test_tenant, status="extracted")
    r = auth_client.patch(f"/documents/{doc.id}/parties/99999", json={"address": "x"})
    assert r.status_code == 404


def test_patch_party_is_self_toggle(auth_client, test_tenant, db):
    """PATCH is_self=True on a party → field updated."""
    doc = _make_doc(db, test_tenant, status="extracted")
    party = _make_party(db, test_tenant, doc.id, is_self=False)

    r = auth_client.patch(
        f"/documents/{doc.id}/parties/{party.id}",
        json={"is_self": True},
    )
    assert r.status_code == 200
    assert r.json()["is_self"] is True


# ── GET detail returns extended party fields ──────────────────────────────────


def test_document_detail_includes_party_extended_fields(auth_client, test_tenant, db):
    """GET /documents/{id} returns full party detail including new fields."""
    doc = _make_doc(db, test_tenant, status="extracted")
    party = Party(
        tenant_id=test_tenant,
        document_id=doc.id,
        name="Bên Bán ABC",
        role_label="Bên Bán",
        address="789 Trần Hưng Đạo",
        contact="024-9999999",
        representative="Trần Thị B - CEO",
        tax_code="1234567890",
        is_self=True,
        aliases=json.dumps(["ABC", "Bên Bán"]),
    )
    db.add(party)
    db.commit()

    r = auth_client.get(f"/documents/{doc.id}")
    assert r.status_code == 200
    parties_data = r.json()["parties"]
    assert len(parties_data) == 1
    p = parties_data[0]
    assert p["name"] == "Bên Bán ABC"
    assert p["address"] == "789 Trần Hưng Đạo"
    assert p["contact"] == "024-9999999"
    assert p["representative"] == "Trần Thị B - CEO"
    assert p["tax_code"] == "1234567890"
    assert p["is_self"] is True
    assert "ABC" in p["aliases"]


def test_document_detail_party_null_new_fields_for_legacy(auth_client, test_tenant, db):
    """Legacy parties without new fields return null values in response."""
    doc = _make_doc(db, test_tenant, status="extracted")
    party = Party(
        tenant_id=test_tenant,
        document_id=doc.id,
        name="Công ty Cũ",
        role_label="Bên A",
    )
    db.add(party)
    db.commit()

    r = auth_client.get(f"/documents/{doc.id}")
    assert r.status_code == 200
    p = r.json()["parties"][0]
    assert p["address"] is None
    assert p["contact"] is None
    assert p["representative"] is None
    assert p["tax_code"] is None
    assert p["aliases"] is None
