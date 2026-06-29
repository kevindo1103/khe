"""Document relationship + chain resolution tests (#50 PR-B)."""
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.database import MasterSessionLocal, get_tenant_session, init_master_db, init_tenant_db
from app.models.master import Tenant, TenantUser
from app.models.tenant import Document, DocumentRelationship, Obligation, Term
from app.services.relationships import (
    confirm_relationship,
    get_relationships_for_document,
    late_link_orphans,
    resolve_chain,
    suggest_relationships,
)
from main import app


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Seed a test tenant + user for relationship tests."""
    init_master_db()
    init_tenant_db("rel-tenant")

    db = MasterSessionLocal()
    tenant = db.query(Tenant).filter(Tenant.id == "rel-tenant").first()
    if not tenant:
        db.add(Tenant(id="rel-tenant", name="Relationship Tenant", db_path="tenants/rel-tenant.db"))
        db.commit()

    user = db.query(TenantUser).filter(TenantUser.tenant_id == "rel-tenant", TenantUser.username == "reluser").first()
    if not user:
        db.add(
            TenantUser(
                tenant_id="rel-tenant",
                username="reluser",
                hashed_password=get_password_hash("relpass"),
                role="staff",
            )
        )
        db.commit()
    db.close()


@pytest.fixture
def auth_client():
    c = TestClient(app)
    r = c.post(
        "/auth/login",
        json={"tenant_id": "rel-tenant", "username": "reluser", "password": "relpass"},
    )
    assert r.status_code == 200
    return c


@pytest.fixture
def tenant_db():
    db = get_tenant_session("rel-tenant")
    yield db
    db.close()


def _seed_doc(db, file_name: str) -> Document:
    doc = Document(
        tenant_id="rel-tenant",
        file_name=file_name,
        file_path=f"rel-tenant/{file_name}",
        doc_type="lease",
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _seed_term(db, document_id: int, field_name: str, field_value: str, needs_review: bool = False) -> Term:
    term = Term(
        tenant_id="rel-tenant",
        document_id=document_id,
        field_name=field_name,
        field_value=field_value,
        confidence=0.8,
        needs_review=needs_review,
    )
    db.add(term)
    db.commit()
    db.refresh(term)
    return term


# ── Service tests ──

class TestSuggestRelationships:
    def test_match_existing_document(self, tenant_db):
        parent = _seed_doc(tenant_db, "HD-001.pdf")
        child = _seed_doc(tenant_db, "HD-002.pdf")
        _seed_term(tenant_db, child.id, "dieu_khoan_gia_han", "Phụ lục HĐ số HD-001")

        rels = suggest_relationships(tenant_db, "rel-tenant", child.id)
        assert len(rels) >= 1
        matched = [r for r in rels if r.to_doc_id == parent.id]
        assert len(matched) == 1
        assert matched[0].relationship_type == "amends"
        assert matched[0].status == "pending"
        assert matched[0].confirmed_by_sme is False

    def test_theo_reference_is_framework_not_amends(self, tenant_db):
        """"theo/căn cứ HĐ" is a framework/basis reference, not an amendment —
        so resolve_chain (amends-only) won't supersede its terms."""
        framework = _seed_doc(tenant_db, "HD-FW1.pdf")
        order = _seed_doc(tenant_db, "DH-100.pdf")
        _seed_term(tenant_db, order.id, "ghi_chu", "Căn cứ HĐ số HD-FW1")

        rels = suggest_relationships(tenant_db, "rel-tenant", order.id)
        fw = [r for r in rels if r.to_doc_id == framework.id]
        assert len(fw) == 1
        assert fw[0].relationship_type == "references_framework"

    def test_orphan_when_no_match(self, tenant_db):
        doc = _seed_doc(tenant_db, "HD-003.pdf")
        _seed_term(tenant_db, doc.id, "ghi_chu", "Tham chiếu HĐ số MISSING-REF")

        rels = suggest_relationships(tenant_db, "rel-tenant", doc.id)
        orphan = [r for r in rels if r.to_doc_id is None and r.unresolved_ref == "missing-ref"]
        assert len(orphan) == 1

    def test_no_self_reference(self, tenant_db):
        doc = _seed_doc(tenant_db, "HD-004.pdf")
        _seed_term(tenant_db, doc.id, "ghi_chu", "HĐ số HD-004")

        rels = suggest_relationships(tenant_db, "rel-tenant", doc.id)
        assert not any(r.to_doc_id == doc.id for r in rels)


class TestLateLinkOrphans:
    def test_late_link_parent(self, tenant_db):
        child = _seed_doc(tenant_db, "HD-005.pdf")
        rel = DocumentRelationship(
            tenant_id="rel-tenant",
            from_doc_id=child.id,
            to_doc_id=None,
            unresolved_ref="hd-006",
            relationship_type="amends",
            status="pending",
            confidence=0.7,
        )
        tenant_db.add(rel)
        tenant_db.commit()

        parent = _seed_doc(tenant_db, "HD-006.pdf")
        updated = late_link_orphans(tenant_db, "rel-tenant", parent)
        assert len(updated) == 1
        assert updated[0].to_doc_id == parent.id
        assert updated[0].status == "pending"  # still needs SME confirm


class TestResolveChain:
    def test_confirmed_edge_supersedes_older_term(self, tenant_db):
        parent = _seed_doc(tenant_db, "HD-007.pdf")
        child = _seed_doc(tenant_db, "HD-008.pdf")
        old_term = _seed_term(tenant_db, parent.id, "gia_tri_hd", "1000")
        new_term = _seed_term(tenant_db, child.id, "gia_tri_hd", "2000")

        rel = DocumentRelationship(
            tenant_id="rel-tenant",
            from_doc_id=child.id,
            to_doc_id=parent.id,
            relationship_type="amends",
            status="confirmed",
            confirmed_by_sme=True,
            confidence=0.9,
        )
        tenant_db.add(rel)
        tenant_db.commit()

        result = resolve_chain(tenant_db, "rel-tenant", child.id)
        assert result["doc_ids"] == [parent.id, child.id]
        assert result["terms_resolved"] == 1

        tenant_db.refresh(old_term)
        tenant_db.refresh(new_term)
        assert old_term.is_superseded is True
        assert new_term.overrides_term_id == old_term.id
        assert new_term.inherited_from_doc_id == parent.id

    def test_resolve_orders_by_amends_not_upload_time(self, tenant_db):
        """DEC-021 orphan: amendment uploaded BEFORE its parent. The amendment must
        still win, since order follows the amends edge, not created_at."""
        # Child (the amendment) is seeded FIRST → lower id / earlier created_at.
        child = _seed_doc(tenant_db, "AMD-100.pdf")
        parent = _seed_doc(tenant_db, "ORIG-100.pdf")
        parent_term = _seed_term(tenant_db, parent.id, "gia_tri_hd", "1000")
        child_term = _seed_term(tenant_db, child.id, "gia_tri_hd", "2000")

        rel = DocumentRelationship(
            tenant_id="rel-tenant",
            from_doc_id=child.id,         # child amends parent
            to_doc_id=parent.id,
            relationship_type="amends",
            status="confirmed",
            confirmed_by_sme=True,
            confidence=0.9,
        )
        tenant_db.add(rel)
        tenant_db.commit()

        result = resolve_chain(tenant_db, "rel-tenant", child.id)
        # Topology order = base (parent) first, even though parent was uploaded later.
        assert result["doc_ids"] == [parent.id, child.id]

        tenant_db.refresh(parent_term)
        tenant_db.refresh(child_term)
        # The amendment (child) wins regardless of upload order.
        assert parent_term.is_superseded is True
        assert child_term.is_superseded is False
        assert child_term.overrides_term_id == parent_term.id

    def test_resolve_multi_parent_keeps_all_branches(self, tenant_db):
        """A document amending two parents (X→Y and X→Z) must keep both in the
        chain — the edge map is one-to-many."""
        y = _seed_doc(tenant_db, "MP-Y.pdf")
        z = _seed_doc(tenant_db, "MP-Z.pdf")
        x = _seed_doc(tenant_db, "MP-X.pdf")
        for parent in (y, z):
            tenant_db.add(
                DocumentRelationship(
                    tenant_id="rel-tenant",
                    from_doc_id=x.id,
                    to_doc_id=parent.id,
                    relationship_type="amends",
                    status="confirmed",
                    confirmed_by_sme=True,
                    confidence=0.9,
                )
            )
        tenant_db.commit()

        result = resolve_chain(tenant_db, "rel-tenant", x.id)
        assert y.id in result["doc_ids"]
        assert z.id in result["doc_ids"]
        assert x.id in result["doc_ids"]

    def test_unconfirmed_edge_does_not_resolve(self, tenant_db):
        parent = _seed_doc(tenant_db, "HD-009.pdf")
        child = _seed_doc(tenant_db, "HD-010.pdf")
        old_term = _seed_term(tenant_db, parent.id, "gia_tri_hd", "1000")
        new_term = _seed_term(tenant_db, child.id, "gia_tri_hd", "2000")

        rel = DocumentRelationship(
            tenant_id="rel-tenant",
            from_doc_id=child.id,
            to_doc_id=parent.id,
            relationship_type="amends",
            status="pending",
            confirmed_by_sme=False,
            confidence=0.9,
        )
        tenant_db.add(rel)
        tenant_db.commit()

        result = resolve_chain(tenant_db, "rel-tenant", child.id)
        assert result["terms_resolved"] == 0

        tenant_db.refresh(old_term)
        tenant_db.refresh(new_term)
        assert old_term.is_superseded is False
        assert new_term.overrides_term_id is None

    def test_updates_existing_obligation_source_chain(self, tenant_db):
        parent = _seed_doc(tenant_db, "HD-011.pdf")
        child = _seed_doc(tenant_db, "HD-012.pdf")
        _seed_term(tenant_db, parent.id, "gia_tri_hd", "1000")
        _seed_term(tenant_db, child.id, "gia_tri_hd", "2000")

        rel = DocumentRelationship(
            tenant_id="rel-tenant",
            from_doc_id=child.id,
            to_doc_id=parent.id,
            relationship_type="amends",
            status="confirmed",
            confirmed_by_sme=True,
            confidence=0.9,
        )
        tenant_db.add(rel)

        ob = Obligation(
            tenant_id="rel-tenant",
            document_id=child.id,
            description="Pay rent",
            recurrence="monthly",
            due_date="2026-07-01",
        )
        tenant_db.add(ob)
        tenant_db.commit()

        result = resolve_chain(tenant_db, "rel-tenant", child.id)
        assert result["obligations_updated"] == 1

        tenant_db.refresh(ob)
        assert ob.source_doc_chain is not None
        assert ob.resolution_method == "last_writer_wins"


# ── Endpoint tests ──

class TestRelationshipEndpoints:
    def test_list_relationships(self, auth_client, tenant_db):
        parent = _seed_doc(tenant_db, "EP-001.pdf")
        child = _seed_doc(tenant_db, "EP-002.pdf")
        rel = DocumentRelationship(
            tenant_id="rel-tenant",
            from_doc_id=child.id,
            to_doc_id=parent.id,
            relationship_type="amends",
            status="pending",
            confidence=0.8,
        )
        tenant_db.add(rel)
        tenant_db.commit()

        r = auth_client.get(f"/documents/{child.id}/relationships")
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["to_doc_id"] == parent.id

    def test_confirm_relationship_triggers_resolution(self, auth_client, tenant_db):
        parent = _seed_doc(tenant_db, "EP-003.pdf")
        child = _seed_doc(tenant_db, "EP-004.pdf")
        old_term = _seed_term(tenant_db, parent.id, "gia_tri_hd", "1000")
        new_term = _seed_term(tenant_db, child.id, "gia_tri_hd", "2000")
        rel = DocumentRelationship(
            tenant_id="rel-tenant",
            from_doc_id=child.id,
            to_doc_id=parent.id,
            relationship_type="amends",
            status="pending",
            confidence=0.9,
        )
        tenant_db.add(rel)
        tenant_db.commit()
        tenant_db.refresh(rel)

        r = auth_client.patch(
            f"/documents/{child.id}/relationships/{rel.id}",
            json={"confirmed_by_sme": True},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert data["relationship"]["status"] == "confirmed"
        assert data["relationship"]["confirmed_by_sme"] is True

        tenant_db.refresh(old_term)
        tenant_db.refresh(new_term)
        assert old_term.is_superseded is True
        assert new_term.overrides_term_id == old_term.id

    def test_cross_tenant_document_404(self, auth_client, tenant_db):
        r = auth_client.get("/documents/99999/relationships")
        assert r.status_code == 404


# ── R4a (#366): annex type extension ─────────────────────────────────────────


class TestAnnexType:
    """Tests for annex relationship type — R4a (#366)."""

    def test_annex_in_valid_relationship_types(self):
        """annex is accepted in VALID_RELATIONSHIP_TYPES."""
        from app.services.relationships import VALID_RELATIONSHIP_TYPES
        assert "annex" in VALID_RELATIONSHIP_TYPES

    def test_annex_in_schema_literal(self):
        """Schema Literal accepts annex without validation error."""
        from app.schemas.relationships import RelationshipOut
        from datetime import datetime
        obj = RelationshipOut(
            id=1,
            from_doc_id=1,
            to_doc_id=2,
            relationship_type="annex",
            status="pending",
            confirmed_by_sme=False,
        )
        assert obj.relationship_type == "annex"

    def test_extract_reference_hints_standalone_phu_luc_is_annex(self):
        """'phụ lục số 1' → annex (not amends)."""
        from app.services.relationships import _extract_reference_hints
        hints = _extract_reference_hints("Tài liệu đính kèm: phụ lục số 1")
        types = {rel_type for _, rel_type in hints}
        assert "annex" in types
        assert "amends" not in types

    def test_extract_reference_hints_phu_luc_so_number_is_annex(self):
        """'Phụ lục số 2' standalone → annex."""
        from app.services.relationships import _extract_reference_hints
        hints = _extract_reference_hints("Phụ lục số 2 của hợp đồng")
        types = {rel_type for _, rel_type in hints}
        assert "annex" in types

    def test_extract_reference_hints_lettered_phu_luc_is_annex(self):
        """'phụ lục A' / 'phụ lục B' → annex (lettered appendix)."""
        from app.services.relationships import _extract_reference_hints
        for text in ["phụ lục A", "Phụ lục B của hợp đồng", "phụ lục HĐ ABC-001"]:
            hints = _extract_reference_hints(text)
            types = {rel_type for _, rel_type in hints}
            assert "annex" in types, f"Expected annex for '{text}', got {hints}"

    def test_extract_reference_hints_amendment_phu_luc_is_amends(self):
        """'phụ lục sửa đổi HĐ số X' → amends, NOT annex."""
        from app.services.relationships import _extract_reference_hints
        hints = _extract_reference_hints("phụ lục sửa đổi HĐ số ABC-001")
        types = {rel_type for _, rel_type in hints}
        assert "amends" in types
        assert "annex" not in types

    def test_extract_reference_hints_phu_luc_bo_sung_is_amends(self):
        """'phụ lục bổ sung' → amends, NOT annex."""
        from app.services.relationships import _extract_reference_hints
        hints = _extract_reference_hints("phụ lục bổ sung số X99")
        types = {rel_type for _, rel_type in hints}
        assert "amends" in types

    def test_amendment_pattern_does_not_match_across_clauses(self):
        """Amendment pattern capped at 80 chars — won't grab distant reference."""
        from app.services.relationships import _extract_reference_hints
        filler = "a" * 100
        text = f"phụ lục bổ sung quy trình nội bộ {filler} tham chiếu ABC-999"
        hints = _extract_reference_hints(text)
        tokens = {tok for tok, _ in hints}
        assert "abc-999" not in tokens, "Should not match reference 100+ chars away"

    def test_resolve_chain_skips_annex_edges(self, tenant_db, test_tenant):
        """resolve_chain does NOT override terms via annex edges."""
        from app.models.tenant import Document, DocumentRelationship, Term
        from app.services.relationships import resolve_chain

        parent = Document(
            tenant_id=test_tenant,
            file_name="main.pdf",
            file_path=f"{test_tenant}/main.pdf",
            status="extracted",
        )
        annex_doc = Document(
            tenant_id=test_tenant,
            file_name="phu-luc-1.pdf",
            file_path=f"{test_tenant}/phu-luc-1.pdf",
            status="extracted",
        )
        tenant_db.add(parent)
        tenant_db.add(annex_doc)
        tenant_db.flush()

        # Term in parent doc
        t_parent = Term(
            tenant_id=test_tenant,
            document_id=parent.id,
            field_name="contract_value",
            field_value="100,000,000 VND",
            confidence=0.9,
        )
        # Term in annex doc — same field_name, different value
        t_annex = Term(
            tenant_id=test_tenant,
            document_id=annex_doc.id,
            field_name="contract_value",
            field_value="999,999,999 VND",
            confidence=0.9,
        )
        tenant_db.add(t_parent)
        tenant_db.add(t_annex)

        # Annex edge (confirmed)
        rel = DocumentRelationship(
            tenant_id=test_tenant,
            from_doc_id=annex_doc.id,
            to_doc_id=parent.id,
            relationship_type="annex",
            status="confirmed",
            confirmed_by_sme=True,
        )
        tenant_db.add(rel)
        tenant_db.commit()

        result = resolve_chain(tenant_db, test_tenant, annex_doc.id)

        # annex edge must not trigger term override
        tenant_db.refresh(t_parent)
        tenant_db.refresh(t_annex)
        assert t_parent.is_superseded is False, "annex must NOT supersede parent terms"
        assert t_annex.overrides_term_id is None
        assert result["terms_resolved"] == 0

    def test_suggest_relationships_creates_annex_edge(self, tenant_db, test_tenant):
        """suggest_relationships classifies 'phụ lục số 1' as annex."""
        from app.models.tenant import Document, Term
        from app.services.relationships import suggest_relationships

        doc = Document(
            tenant_id=test_tenant,
            file_name="contract-main.pdf",
            file_path=f"{test_tenant}/contract-main.pdf",
            status="extracted",
        )
        tenant_db.add(doc)
        tenant_db.flush()

        term = Term(
            tenant_id=test_tenant,
            document_id=doc.id,
            field_name="reference",
            field_value="Đính kèm phụ lục số 1",
        )
        tenant_db.add(term)
        tenant_db.commit()

        rels = suggest_relationships(tenant_db, test_tenant, doc.id)
        rel_types = {r.relationship_type for r in rels}
        assert "annex" in rel_types, f"Expected annex in {rel_types}"
