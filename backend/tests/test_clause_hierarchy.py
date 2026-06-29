"""Tests for clause hierarchy — parent/child cascade (#365 R3)."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.database import get_tenant_session
from app.models.tenant import Clause, Document
from app.services.clause_hierarchy import build_clause_hierarchy, _parse_path, _level_from_path


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


def _make_clause(db, tenant_id, doc_id, clause_num, content="nội dung"):
    c = Clause(
        tenant_id=tenant_id,
        document_id=doc_id,
        clause_num=clause_num,
        content=content,
    )
    db.add(c)
    return c


def _make_mock_result(clauses_data=None):
    """Build ExtractionResult mock with clause list."""
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
    result.fields = {}
    result.obligation_schedule = []
    result.parties = []
    result.defined_terms = []
    result.cross_references = []
    result.has_signature = False
    result.signature_pages = []

    clause_items = []
    for item in (clauses_data or []):
        ci = MagicMock()
        if len(item) == 3:
            num, title, content = item
            ci.level = None
            ci.clause_path = None
        else:
            num, title, content, level, clause_path = item
            ci.level = level
            ci.clause_path = clause_path
        ci.num = num
        ci.title = title
        ci.content = content
        clause_items.append(ci)
    result.clauses = clause_items
    return result


def _run_mock_extraction(tenant_id, tmp_path, mock_result):
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
        clauses = (
            db2.query(Clause)
            .filter(Clause.document_id == doc_id, Clause.tenant_id == tenant_id)
            .order_by(Clause.clause_path.asc().nulls_last(), Clause.id.asc())
            .all()
        )
        return [
            {
                "id": c.id,
                "clause_num": c.clause_num,
                "clause_path": c.clause_path,
                "level": c.level,
                "parent_id": c.parent_id,
                "content": c.content,
            }
            for c in clauses
        ], doc_id
    finally:
        db2.close()


# ── Pure path parsing tests ───────────────────────────────────────────────────


def test_parse_path_dieu():
    """Điều X → path "X"."""
    assert _parse_path("Điều 2") == "2"
    assert _parse_path("Điều 10") == "10"


def test_parse_path_khoan():
    """Khoản X.Y → path "X.Y"."""
    assert _parse_path("Khoản 2.1") == "2.1"
    assert _parse_path("Khoản 3.2.1") == "3.2.1"


def test_parse_path_muc():
    """Mục X.Y → path "X.Y"."""
    assert _parse_path("Mục 2.3") == "2.3"


def test_parse_path_bare_dotted():
    """Bare "2.1" or "2.1.1" → extracted as dotted path."""
    assert _parse_path("2.1") == "2.1"
    assert _parse_path("2.1.1") == "2.1.1"
    assert _parse_path("2.1 Some content title") == "2.1"


def test_parse_path_bare_top():
    """Bare "2" or "2." → top-level path "2"."""
    assert _parse_path("2.") == "2"
    assert _parse_path("3 Thanh toán") == "3"


def test_parse_path_unrecognised():
    """Non-numeric / letter / roman numbering → None."""
    assert _parse_path("a.") is None
    assert _parse_path("I. Giới thiệu") is None
    assert _parse_path("Tổng quan") is None
    assert _parse_path(None) is None
    assert _parse_path("") is None


def test_level_from_path():
    """Level derived from dot count + 1 (1-indexed, matching prompt schema)."""
    assert _level_from_path("2") == 1
    assert _level_from_path("2.1") == 2
    assert _level_from_path("2.1.1") == 3
    assert _level_from_path("2.1.1.1") == 4


# ── build_clause_hierarchy unit tests ────────────────────────────────────────


def test_build_hierarchy_links_parent(test_tenant, db):
    """Clause "2.1" gets parent_id pointing to clause "2"."""
    doc = _make_doc(db, test_tenant, status="extracted")
    c_parent = _make_clause(db, test_tenant, doc.id, "Điều 2", "Nội dung điều 2")
    c_child = _make_clause(db, test_tenant, doc.id, "Khoản 2.1", "Nội dung khoản 2.1")
    db.flush()

    build_clause_hierarchy([c_parent, c_child], db)
    db.commit()
    db.refresh(c_parent)
    db.refresh(c_child)

    assert c_parent.clause_path == "2"
    assert c_parent.level == 1
    assert c_parent.parent_id is None

    assert c_child.clause_path == "2.1"
    assert c_child.level == 2
    assert c_child.parent_id == c_parent.id


def test_build_hierarchy_three_levels(test_tenant, db):
    """Three-level chain: 2 → 2.1 → 2.1.1."""
    doc = _make_doc(db, test_tenant, status="extracted")
    c1 = _make_clause(db, test_tenant, doc.id, "Điều 2")
    c2 = _make_clause(db, test_tenant, doc.id, "Khoản 2.1")
    c3 = _make_clause(db, test_tenant, doc.id, "2.1.1")
    db.flush()

    build_clause_hierarchy([c1, c2, c3], db)
    db.commit()
    db.refresh(c1); db.refresh(c2); db.refresh(c3)

    assert c1.parent_id is None
    assert c2.parent_id == c1.id
    assert c3.parent_id == c2.id
    assert c3.level == 3


def test_build_hierarchy_synthesizes_missing_parent(test_tenant, db):
    """Child "2.1" with no parent "2" → stub parent synthesized."""
    doc = _make_doc(db, test_tenant, status="extracted")
    c_child = _make_clause(db, test_tenant, doc.id, "Khoản 2.1")
    db.flush()

    build_clause_hierarchy([c_child], db)
    db.commit()
    db.refresh(c_child)

    # stub parent must exist in DB
    stub = db.query(Clause).filter(
        Clause.document_id == doc.id,
        Clause.clause_path == "2",
        Clause.tenant_id == test_tenant,
    ).first()
    assert stub is not None
    assert stub.content == "(tổng hợp từ mục con)"
    assert stub.level == 1
    assert c_child.parent_id == stub.id


def test_build_hierarchy_flat_clauses(test_tenant, db):
    """Clauses with no numeric numbering stay parent_id=None, level=None."""
    doc = _make_doc(db, test_tenant, status="extracted")
    c1 = _make_clause(db, test_tenant, doc.id, "Giới thiệu")
    c2 = _make_clause(db, test_tenant, doc.id, None)
    db.flush()

    build_clause_hierarchy([c1, c2], db)
    db.commit()
    db.refresh(c1); db.refresh(c2)

    assert c1.clause_path is None
    assert c1.parent_id is None
    assert c1.level is None
    assert c2.clause_path is None


def test_build_hierarchy_empty_list(test_tenant, db):
    """Empty clause list is a no-op."""
    build_clause_hierarchy([], db)  # should not raise


# ── Model column tests ────────────────────────────────────────────────────────


def test_clause_has_hierarchy_columns(test_tenant, db):
    """Clause model has parent_id, level, clause_path columns (nullable)."""
    doc = _make_doc(db, test_tenant, status="extracted")
    c = _make_clause(db, test_tenant, doc.id, "Điều 1")
    db.commit()
    db.refresh(c)
    assert hasattr(c, "parent_id")
    assert hasattr(c, "level")
    assert hasattr(c, "clause_path")
    assert c.parent_id is None
    assert c.level is None
    assert c.clause_path is None


# ── extraction_runner integration ─────────────────────────────────────────────


def test_extraction_builds_hierarchy(test_tenant, tmp_path):
    """Extraction populates clause hierarchy from AI result."""
    clauses_data = [
        ("Điều 2", "Cấp phép", "Nội dung điều 2"),
        ("Khoản 2.1", "Phạm vi", "Nội dung 2.1"),
        ("2.1.1", None, "Chi tiết 2.1.1"),
    ]
    result = _make_mock_result(clauses_data)
    clauses, _ = _run_mock_extraction(test_tenant, tmp_path, result)

    by_path = {c["clause_path"]: c for c in clauses if c["clause_path"]}
    assert "2" in by_path
    assert "2.1" in by_path
    assert "2.1.1" in by_path

    assert by_path["2"]["level"] == 1
    assert by_path["2"]["parent_id"] is None
    assert by_path["2.1"]["level"] == 2
    assert by_path["2.1"]["parent_id"] == by_path["2"]["id"]
    assert by_path["2.1.1"]["level"] == 3
    assert by_path["2.1.1"]["parent_id"] == by_path["2.1"]["id"]


def test_extraction_synthesizes_missing_parent(test_tenant, tmp_path):
    """Extraction creates stub parent when AI omits intermediate level."""
    clauses_data = [
        ("Khoản 3.2", None, "Nội dung 3.2"),  # parent "3" missing from AI output
    ]
    result = _make_mock_result(clauses_data)
    clauses, _ = _run_mock_extraction(test_tenant, tmp_path, result)

    by_path = {c["clause_path"]: c for c in clauses if c["clause_path"]}
    assert "3" in by_path, "Stub parent '3' should be synthesized"
    assert by_path["3"]["content"] == "(tổng hợp từ mục con)"
    assert by_path["3.2"]["parent_id"] == by_path["3"]["id"]


def test_extraction_prefers_llm_hierarchy(test_tenant, tmp_path):
    """LLM-provided level/clause_path are preserved, not overwritten by regex."""
    clauses_data = [
        ("Điều 5", "Thanh toán", "Nội dung điều 5", 1, "5"),
        ("Khoản 5.1", "Chi tiết", "Nội dung 5.1", 2, "5.1"),
    ]
    result = _make_mock_result(clauses_data)
    clauses, _ = _run_mock_extraction(test_tenant, tmp_path, result)

    by_path = {c["clause_path"]: c for c in clauses if c["clause_path"]}
    assert by_path["5"]["level"] == 1
    assert by_path["5.1"]["level"] == 2
    assert by_path["5.1"]["parent_id"] == by_path["5"]["id"]


def test_extraction_flat_clauses_null_hierarchy(test_tenant, tmp_path):
    """Clauses with non-numeric numbering stay NULL hierarchy."""
    clauses_data = [
        ("Mở đầu", None, "Phần giới thiệu"),
        (None, None, "Điều khoản chung"),
    ]
    result = _make_mock_result(clauses_data)
    clauses, _ = _run_mock_extraction(test_tenant, tmp_path, result)

    for c in clauses:
        assert c["clause_path"] is None
        assert c["parent_id"] is None
        assert c["level"] is None


# ── GET /documents/{id}/clauses returns new fields ────────────────────────────


def test_get_clauses_includes_hierarchy_fields(auth_client, test_tenant, db):
    """GET /documents/{id}/clauses returns parent_id, level, clause_path."""
    doc = _make_doc(db, test_tenant, status="extracted")
    c_parent = Clause(
        tenant_id=test_tenant,
        document_id=doc.id,
        clause_num="Điều 1",
        content="Nội dung điều 1",
        clause_path="1",
        level=1,
    )
    db.add(c_parent)
    db.flush()

    c_child = Clause(
        tenant_id=test_tenant,
        document_id=doc.id,
        clause_num="Khoản 1.1",
        content="Nội dung 1.1",
        clause_path="1.1",
        level=2,
        parent_id=c_parent.id,
    )
    db.add(c_child)
    db.commit()

    r = auth_client.get(f"/documents/{doc.id}/clauses")
    assert r.status_code == 200
    data = r.json()
    clauses = {c["clause_num"]: c for c in data["clauses"]}

    assert clauses["Điều 1"]["clause_path"] == "1"
    assert clauses["Điều 1"]["level"] == 1
    assert clauses["Điều 1"]["parent_id"] is None

    assert clauses["Khoản 1.1"]["clause_path"] == "1.1"
    assert clauses["Khoản 1.1"]["level"] == 2
    assert clauses["Khoản 1.1"]["parent_id"] == c_parent.id


def test_get_clauses_null_hierarchy_for_legacy(auth_client, test_tenant, db):
    """Legacy clauses without hierarchy columns return null in response."""
    doc = _make_doc(db, test_tenant, status="extracted")
    c = Clause(
        tenant_id=test_tenant,
        document_id=doc.id,
        clause_num="Điều 5",
        content="Nội dung cũ",
    )
    db.add(c)
    db.commit()

    r = auth_client.get(f"/documents/{doc.id}/clauses")
    assert r.status_code == 200
    item = r.json()["clauses"][0]
    assert item["parent_id"] is None
    assert item["level"] is None
    assert item["clause_path"] is None
