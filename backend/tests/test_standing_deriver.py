"""StandingObligationDeriver unit tests — covers 6 QC-found bugs (#274 PR #498).

Bugs fixed:
  1. D-15: DELETE lacked fulfilled_at IS NULL guard
  2. _norm(): đ/Đ silently dropped (no NFD decomp) → fix pre-replace đ→d
  3. _first_sentence(): returned "1" for "1. Bên A..." numbered clauses
  4. Typo: "khong tiep lo" → "khong tiet lo"
  5. recurrence="once" wrong → "open_ended_review"
  6. _STANDING_PATTERNS had diacritic/CJK literals that can't match after _norm()
"""
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest

from modules.obligation.derivers import (
    _first_sentence,
    _norm,
    _match_clause_type,
    derive_standing_obligations,
)
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Clause, Document, Obligation
from app.core.security import get_password_hash

TENANT = "standing-deriver-tenant"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_master_db()
    init_tenant_db(TENANT)
    db = MasterSessionLocal()
    if not db.query(Tenant).filter(Tenant.id == TENANT).first():
        db.add(Tenant(id=TENANT, name="Standing Deriver Tenant", db_path=f"tenants/{TENANT}.db"))
        db.commit()
    if not db.query(Tenant).filter(Tenant.id == TENANT).first():
        db.add(Tenant(id=TENANT, name="Standing Deriver Tenant", db_path=f"tenants/{TENANT}.db"))
        db.commit()
    db.close()


@pytest.fixture
def db():
    d = get_tenant_session(TENANT)
    try:
        yield d
    finally:
        d.close()


# ── _norm() ──────────────────────────────────────────────────────────────────

def test_norm_strips_diacritics():
    assert _norm("Bảo Mật") == "bao mat"


def test_norm_d_with_stroke_bug2():
    """Bug 2: đ (U+0111) has no NFD decomp — must pre-replace đ→d."""
    assert _norm("độc quyền") == "doc quyen"
    assert _norm("đáp ứng") == "dap ung"
    assert _norm("định kỳ") == "dinh ky"
    assert _norm("Đơn vị") == "don vi"


def test_norm_uppercase_D_with_stroke():
    assert _norm("ĐỊNH KỲ") == "dinh ky"


def test_norm_mixed():
    assert _norm("Báo cáo định kỳ") == "bao cao dinh ky"


# ── _first_sentence() ────────────────────────────────────────────────────────

def test_first_sentence_normal():
    assert _first_sentence("Bên A cam kết bảo mật. Điều khoản tiếp theo.") == "Bên A cam kết bảo mật"


def test_first_sentence_numbered_clause_bug3():
    """Bug 3: '1. Bên A...' split on '.' yields '1' — must skip pure-digit segments."""
    result = _first_sentence("1. Bên A cam kết không tiết lộ thông tin.")
    assert result == "Bên A cam kết không tiết lộ thông tin"
    assert result != "1"  # should NOT return just the list marker


def test_first_sentence_empty():
    assert _first_sentence("") == ""


def test_first_sentence_no_terminator():
    assert _first_sentence("Không có dấu chấm câu") == "Không có dấu chấm câu"


def test_first_sentence_skip_digit_then_content():
    result = _first_sentence("2. Hợp đồng có hiệu lực. Sau đó.")
    assert "2" != result
    assert "Hợp đồng có hiệu lực" in result


# ── _match_clause_type() ──────────────────────────────────────────────────────

def test_match_nda_ascii():
    assert _match_clause_type("NDA Agreement", "") == "standing"


def test_match_confidentiality_vn():
    assert _match_clause_type("Điều khoản bảo mật", "") == "standing"


def test_match_non_compete():
    assert _match_clause_type("Không cạnh tranh", "") == "standing"


def test_match_exclusivity_with_d_stroke_bug6():
    """Bug 6 + Bug 2: 'độc quyền' requires đ→d fix to match 'doc quyen' pattern."""
    assert _match_clause_type("Điều khoản độc quyền", "") == "standing"


def test_match_compliance_dap_ung():
    """Bug 2: 'đáp ứng' requires đ→d to match 'dap ung'."""
    assert _match_clause_type("Điều kiện đáp ứng", "") == "standing"


def test_match_reporting():
    assert _match_clause_type("Báo cáo định kỳ", "") == "reporting"


def test_match_reporting_dinh_ky():
    """Bug 2: 'định kỳ' requires đ→d to match 'dinh ky'."""
    assert _match_clause_type("Báo cáo định kỳ hàng quý", "") == "reporting"


def test_match_no_match():
    assert _match_clause_type("Điều khoản thanh toán", "") is None


def test_match_khong_tiet_lo_fix_bug4():
    """Bug 4: typo was 'tiep lo' — correct pattern is 'tiet lo' (tiết lộ = disclose)."""
    assert _match_clause_type("Không tiết lộ thông tin", "") == "standing"


def test_match_no_cjk_match():
    """Bug 6: CJK chars (保密) removed from patterns — should not cause errors."""
    # Chinese title shouldn't throw; may or may not match (not a requirement)
    result = _match_clause_type("保密协议", "")
    assert result in (None, "standing")  # acceptable either way post-cleanup


# ── derive_standing_obligations() ────────────────────────────────────────────

def _make_doc(db) -> int:
    doc = Document(tenant_id=TENANT, file_name="test.pdf", file_path="x/test.pdf", status="extracted")
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc.id


def test_derive_creates_obligations(db):
    doc_id = _make_doc(db)
    db.add(Clause(tenant_id=TENANT, document_id=doc_id, clause_num="1",
                   title="Điều khoản bảo mật", content="Bên A cam kết bảo mật thông tin."))
    db.commit()

    result = derive_standing_obligations(db, TENANT, doc_id)
    assert result["created"] == 1
    assert result["skipped"] is False

    obs = db.query(Obligation).filter(Obligation.document_id == doc_id).all()
    assert len(obs) == 1
    ob = obs[0]
    assert ob.obligation_type == "standing"
    assert ob.status == "in_progress"
    assert ob.due_date is None


def test_derive_recurrence_open_ended_review_bug5(db):
    """Bug 5: recurrence must be 'open_ended_review', not 'once'."""
    doc_id = _make_doc(db)
    db.add(Clause(tenant_id=TENANT, document_id=doc_id, clause_num="2",
                   title="Non-disclosure agreement", content="Party A shall not disclose."))
    db.commit()

    derive_standing_obligations(db, TENANT, doc_id)
    ob = db.query(Obligation).filter(Obligation.document_id == doc_id).first()
    assert ob is not None
    assert ob.recurrence == "open_ended_review"


def test_derive_d15_done_not_deleted_bug1(db):
    """D-15 guard — 'done' standing obligations must survive re-derive."""
    doc_id = _make_doc(db)
    db.add(Clause(tenant_id=TENANT, document_id=doc_id, clause_num="3",
                   title="Bảo mật thông tin", content="Các bên giữ bí mật tuyệt đối."))
    db.commit()

    derive_standing_obligations(db, TENANT, doc_id)
    ob = db.query(Obligation).filter(Obligation.document_id == doc_id).first()
    assert ob is not None

    from datetime import datetime
    ob.status = "done"
    ob.fulfilled_at = datetime(2025, 1, 1)
    ob.fulfilled_by = "testuser"
    db.commit()

    derive_standing_obligations(db, TENANT, doc_id)
    surviving = db.query(Obligation).filter(
        Obligation.document_id == doc_id,
        Obligation.status == "done",
    ).all()
    assert len(surviving) == 1, "Done standing obligation was wiped by re-derive (D-15 violation)"


def test_derive_d15_cancelled_not_deleted(db):
    """D-15 guard — 'cancelled' rows have fulfilled_at=NULL (cancel clears it),
    so the old fulfilled_at IS NULL guard silently resurrected them on re-derive.
    Must use status.notin_(['done','cancelled']) instead."""
    doc_id = _make_doc(db)
    db.add(Clause(tenant_id=TENANT, document_id=doc_id, clause_num="c3",
                   title="Non-compete clause", content="Party shall not compete."))
    db.commit()

    derive_standing_obligations(db, TENANT, doc_id)
    ob = db.query(Obligation).filter(Obligation.document_id == doc_id).first()
    assert ob is not None

    # Cancel the obligation — cancel path sets fulfilled_at = None explicitly
    ob.status = "cancelled"
    ob.fulfilled_at = None
    db.commit()

    derive_standing_obligations(db, TENANT, doc_id)
    cancelled = db.query(Obligation).filter(
        Obligation.document_id == doc_id,
        Obligation.status == "cancelled",
    ).all()
    assert len(cancelled) == 1, "Cancelled standing obligation was resurrected by re-derive (D-15 violation)"


def test_derive_skips_no_clauses(db):
    doc_id = _make_doc(db)
    result = derive_standing_obligations(db, TENANT, doc_id)
    assert result["skipped"] is True
    assert result["created"] == 0


def test_derive_idempotent(db):
    doc_id = _make_doc(db)
    db.add(Clause(tenant_id=TENANT, document_id=doc_id, clause_num="4",
                   title="Tuân thủ pháp luật", content="Các bên cam kết tuân thủ."))
    db.commit()

    r1 = derive_standing_obligations(db, TENANT, doc_id)
    r2 = derive_standing_obligations(db, TENANT, doc_id)
    assert r1["created"] == 1
    assert r2["created"] == 1  # idempotent: old unfulfilled row cleared, new row created
    obs = db.query(Obligation).filter(Obligation.document_id == doc_id,
                                       Obligation.status == "in_progress").all()
    assert len(obs) == 1  # no duplicates
