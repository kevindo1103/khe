"""D-rules regression (#76) — D-06 / D-07 / D-08 / D-10.

Per CLAUDE.md §D-rules — these are business invariants that MUST hold across
every release. Any failure = `severity:critical`, STOP smoke immediately
(per #75 bug-reporting rule), file as bug, ping Backend lead.

NOTE — scaffolded by QC lead per PM directive (2026-06-19). Bodies are
Windsurf_QC scope; this file pins the contract.
"""
import pytest


# ═══════════════════════════════════════════════════════════════════════════
# D-06 — Extraction is READ-ONLY (AI never authors/edits legal content)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(reason="dep:#60 — extraction worker; needs mock provider")
class TestD06ExtractionReadOnly:
    def test_extraction_result_values_appear_verbatim_in_source(self, client):
        # TODO(Windsurf_QC): mock provider returns ExtractionResult; assert
        # every field_value either appears in source text (for known fixture)
        # or is None. NO synthesized strings.
        raise NotImplementedError


# ═══════════════════════════════════════════════════════════════════════════
# D-07 — Edit field → Event ledger row with correct tenant_id
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(reason="dep:#54+#60 — term edit endpoint depends on ingest+extraction")
class TestD07EventLedgerOnEdit:
    def test_term_edit_writes_event_field_edited(self, client, auth_cookie):
        # TODO(Windsurf_QC): PATCH /documents/{id}/terms/{term_id} → verify
        # events row appended: event_type='updated' (or 'field_edited'),
        # entity_type='term', actor=<user>, payload={old, new}.
        raise NotImplementedError

    def test_event_tenant_id_matches_logged_in_tenant(self, client, auth_cookie):
        # TODO(Windsurf_QC): event.tenant_id MUST equal JWT/cookie tenant_id.
        raise NotImplementedError


# ═══════════════════════════════════════════════════════════════════════════
# D-08 — Chat "không tìm thấy" — no fabrication
# ═══════════════════════════════════════════════════════════════════════════

D08_EXACT = "Không tìm thấy thông tin này trong hồ sơ của bạn."


@pytest.mark.skip(reason="dep:#27 — chat router not yet merged")
class TestD08NoFabrication:
    def test_no_data_returns_exact_d08_string(self, client, auth_cookie):
        # TODO(Windsurf_QC): tenant with 0 docs, ask any question → exact string.
        raise NotImplementedError

    def test_question_about_nonexistent_doc_returns_d08(self, client, auth_cookie):
        # TODO(Windsurf_QC): doc named X exists, question names doc Y → D-08.
        raise NotImplementedError

    def test_multi_doc_ambiguous_question_returns_d08(self, client, auth_cookie):
        # TODO(Windsurf_QC): 2+ docs, no doc named in question → D-08
        # (single-doc fallback OK; multi-doc must not pick arbitrarily).
        raise NotImplementedError

    def test_interpretation_question_returns_d08(self, client, auth_cookie):
        # TODO(Windsurf_QC): "tôi có thể hủy hợp đồng không?" → D-08
        # (D-06 — backend does not interpret).
        raise NotImplementedError


# ═══════════════════════════════════════════════════════════════════════════
# D-10 — Cross-tenant isolation (404, NEVER 200, NEVER 403)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(reason="dep:#54 — needs ingest endpoint to seed a tenant-a doc")
class TestD10TenantIsolation:
    def test_tenant_b_cannot_read_tenant_a_document(self, client, auth_cookie):
        # TODO(Windsurf_QC): upload as alice → note doc_id. Login as bob.
        # GET /documents/{doc_id} → 404 (NOT 200, NOT 403).
        raise NotImplementedError

    def test_tenant_b_cannot_download_tenant_a_file(self, client, auth_cookie):
        # TODO(Windsurf_QC): GET /documents/{doc_id}/file as bob → 404.
        raise NotImplementedError

    def test_tenant_b_cannot_patch_tenant_a_term(self, client, auth_cookie):
        # TODO(Windsurf_QC): PATCH .../terms/{tid} as bob → 404.
        raise NotImplementedError

    def test_tenant_b_obligations_does_not_leak_tenant_a(self, client, auth_cookie):
        # TODO(Windsurf_QC): GET /obligations as bob → no rows from tenant-a.
        raise NotImplementedError

    def test_tenant_b_chat_query_returns_d08_for_tenant_a_data(
        self, client, auth_cookie
    ):
        # TODO(Windsurf_QC): chat as bob about tenant-a's contract → D-08 string.
        raise NotImplementedError
