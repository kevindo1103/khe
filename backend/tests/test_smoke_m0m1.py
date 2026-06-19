"""M0+M1 smoke (#76) — Tier 1 runnable + Tier 2 skip-marked.

Skip markers cite the backend PR each Tier-2 test depends on. Re-run after
each PR lands; remove marker, verify green.

NOTE — scaffolded by QC lead per PM directive (2026-06-19). Test bodies are
Windsurf_QC scope. Stubs include the assertion shape and dep label only.
"""
import pytest


# ═══════════════════════════════════════════════════════════════════════════
# TIER 1 — Should pass NOW on staging (auth + tenant isolation + health)
# ═══════════════════════════════════════════════════════════════════════════

class TestTier1Health:
    def test_health_endpoint_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


class TestTier1Auth:
    """§A from #75 — 6 auth cases. Cookie-based per DEC-#43 / #46."""

    def test_login_success_sets_cookie_no_token_in_body(self, client, seeded_tenants):
        r = client.post("/auth/login", json={
            "tenant_id": "tenant-a", "username": "alice", "password": "alice-pass"
        })
        assert r.status_code == 200
        body = r.json()
        assert "access_token" not in body, "DEC-#43: cookie-only auth, no token in body"
        assert body["tenant_id"] == "tenant-a"
        assert body["user"]["username"] == "alice"
        assert "khe_session" in r.cookies

    def test_login_wrong_password_returns_401_no_cookie(self, client):
        r = client.post("/auth/login", json={
            "tenant_id": "tenant-a", "username": "alice", "password": "wrong"
        })
        assert r.status_code == 401
        assert "khe_session" not in r.cookies

    def test_login_unknown_tenant_returns_401(self, client):
        r = client.post("/auth/login", json={
            "tenant_id": "ghost-tenant", "username": "alice", "password": "alice-pass"
        })
        assert r.status_code == 401  # tenant filter returns no user → 401, not 422

    def test_me_with_cookie_returns_user(self, client, auth_cookie):
        cookie = auth_cookie("tenant-a", "alice", "alice-pass")
        r = client.get("/auth/me", cookies={"khe_session": cookie})
        assert r.status_code == 200
        assert r.json()["username"] == "alice"
        assert r.json()["tenant_id"] == "tenant-a"

    def test_me_without_cookie_returns_401(self, client):
        r = client.get("/auth/me")
        assert r.status_code == 401

    def test_logout_clears_cookie(self, client, auth_cookie):
        cookie = auth_cookie("tenant-a", "alice", "alice-pass")
        r = client.post("/auth/logout", cookies={"khe_session": cookie})
        assert r.status_code == 200
        # Follow-up /me must fail
        r2 = client.get("/auth/me")
        assert r2.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════
# TIER 2 — Write now, run after dep PRs merge
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.skip(reason="dep:#22 — consent gate endpoint not yet merged")
class TestTier2Consent:
    def test_upload_without_consent_returns_403(self, client, auth_cookie):
        # TODO(Windsurf_QC): login as tenant-noconsent, POST /ingest/upload → 403
        raise NotImplementedError

    def test_upload_after_consent_returns_201(self, client, auth_cookie):
        # TODO(Windsurf_QC): POST /consent, then upload → 201
        raise NotImplementedError


@pytest.mark.skip(reason="dep:#54 — ingest endpoint pending; #79 hotfix in flight via #80")
class TestTier2Ingest:
    def test_upload_pdf_returns_doc_id_processing(self, client, auth_cookie):
        # TODO(Windsurf_QC): POST /ingest/upload with %PDF bytes → 201 + status=processing
        raise NotImplementedError

    def test_upload_non_pdf_returns_422(self, client, auth_cookie):
        # TODO(Windsurf_QC): upload .txt → 422 "Only PDF files are accepted."
        raise NotImplementedError

    def test_bulk_upload_3_returns_3_doc_rows(self, client, auth_cookie):
        # TODO(Windsurf_QC): bulk 3 PDFs → 201 count=3
        raise NotImplementedError

    def test_bulk_upload_21_returns_422_max_20(self, client, auth_cookie):
        # TODO(Windsurf_QC): 21 PDFs → 422 "Maximum 20 files per bulk upload."
        raise NotImplementedError


@pytest.mark.skip(reason="dep:#60 — extraction worker pending; mock provider needed")
class TestTier2Extraction:
    def test_extraction_mock_persists_terms_with_confidence(
        self, client, auth_cookie, monkeypatch
    ):
        # TODO(Windsurf_QC): monkeypatch get_extraction_provider → FakeProvider
        # returning canned ExtractionResult. Upload → poll → assert terms saved
        # with confidence + needs_review.
        # CRITICAL: do NOT call real Gemini/Claude in tests (rate limit + cost).
        raise NotImplementedError


@pytest.mark.skip(reason="dep:#26 — obligation engine merged but consent+ingest gating chain")
class TestTier2ObligationDerive:
    def test_derive_from_hieu_luc_plus_thoi_han(self, client):
        # TODO(Windsurf_QC): seed Terms (ngay_hieu_luc=2026-01-01, thoi_han_hd="36 tháng")
        # → derived ngay_het_han=2029-01-01. FR-OB-01 from BRD.
        raise NotImplementedError

    def test_no_dates_returns_zero_obligations(self, client):
        # TODO(Windsurf_QC): D-08 — no extractable date fields → 0 obligations,
        # NOT a fabricated due_date.
        raise NotImplementedError

    def test_open_ended_review_no_due_date(self, client):
        # TODO(Windsurf_QC): DEC-020 — "vô thời hạn" → obligation_type=open_ended_review,
        # due_date=null.
        raise NotImplementedError


@pytest.mark.skip(reason="dep:#62 — reminder scheduler + Event ledger idempotency check")
class TestTier2ReminderIdempotent:
    def test_same_obligation_not_sent_twice(self, client):
        # TODO(Windsurf_QC): fire scheduler twice on same obligation → reminder_sent
        # Event written once; second call observes Event and skips.
        raise NotImplementedError


@pytest.mark.skip(reason="dep:#59 — document relationships")
class TestTier2DocumentRelationships:
    def test_amendment_creates_amends_edge(self, client):
        # TODO(Windsurf_QC): upload main → amendment → edge type=amends created.
        raise NotImplementedError

    def test_orphan_amendment_flagged_pending_not_blocked(self, client):
        # TODO(Windsurf_QC): DEC-021 — orphan amendment → status pending, accepted.
        raise NotImplementedError


@pytest.mark.skip(reason="dep:#27 — chat router not yet merged")
class TestTier2ChatD08:
    def test_no_match_returns_exact_d08_string(self, client, auth_cookie):
        # TODO(Windsurf_QC): question with no data → response body must contain
        # EXACT byte-for-byte:
        EXPECTED = "Không tìm thấy thông tin này trong hồ sơ của bạn."
        # found=False + answer == EXPECTED + sources==[].
        raise NotImplementedError


@pytest.mark.skip(reason="dep:#63 — quota guard not yet started")
class TestTier2QuotaGuard:
    def test_over_quota_returns_429(self, client):
        # TODO(Windsurf_QC): docs_used_month >= doc_quota → upload returns 429.
        raise NotImplementedError


@pytest.mark.skip(reason="dep:DEC-025 — consent channel_target_ref routing")
class TestTier2ChannelRouting:
    def test_telegram_uses_consent_channel_target_ref_not_global_env(self, client):
        # TODO(Windsurf_QC): PM decision 2026-06-19 — prod NEVER falls back to
        # global TELEGRAM_CHAT_ID env. Reminder send must read channel_target_ref
        # from the active reminder_send consent row.
        raise NotImplementedError
