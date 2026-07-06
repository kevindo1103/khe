# KHE_QC — Session State
_Last updated: 2026-07-06 · Branch: `claude/claude-md-qc-review-swuqrg`_

---

## Current Sprint Focus

### Open Issues (for:qc)

| # | Title | Status | Priority |
|---|---|---|---|
| #500 | Review lo-fi wireframe Flow 2 + Flow 3 | `status:planned` | HIGH (blocking Designer hi-fi) |
| #297 | Obligation Fulfillment & Dependency Chain — QC pressure-test | `decision-review` | HIGH (DEC-048 ratify gate) |
| #187 | Playwright scaffold + 3 critical e2e journeys | `status:in-progress` | HIGH (pre-pilot blocker) |
| #118 | Chat query pattern catalog — QC test cases | `relay` | MEDIUM |
| #75 | UAT smoke test — backend M0/M1 on staging | `blocker:waiting-dependency` | HIGH (blocked on uat-demo-b seed) |

---

## Test Coverage Snapshot (2026-07-06)

### Backend (`backend/tests/`)
- **Files:** 55 test files (see list below)
- **Run status:** pending dependency install (cryptography conflict on this env)
- **Coverage areas:** ingest, extraction, obligations, chat, consent, tenant isolation, quota, reminders, D-rules regression, fulfillment, relationships, clauses, parties, cost tracking

### Frontend (`frontend/tests/`)
- **Status:** DIRECTORY DOES NOT EXIST — no e2e scaffold yet
- **PWA (`frontend/pwa/`):** no tests

### E2E Playwright
- **Status:** NOT SCAFFOLDED — tracked in #187
- Pre-requisite for pilot launch

---

## Backend Test Files
```
test_cascade_past, test_chat, test_chat_aggregate, test_chat_composition,
test_chat_session, test_clause_hierarchy, test_clause_patch, test_clause_provenance,
test_clauses_api, test_consent, test_contract_title, test_cost_tracking,
test_cross_ref, test_date_taxonomy, test_db_cache, test_definitions,
test_document_confirm, test_document_events, test_document_provider,
test_document_remap, test_documents_list, test_drules_regression,
test_extraction_dec029, test_extraction_diagnostic, test_extraction_metrics,
test_extraction_progress, test_extraction_runner, test_failure_reason,
test_fulfillment, test_ingest, test_ingest_hardening, test_lifecycle,
test_obligation_date_resolve, test_obligation_direction, test_obligation_model,
test_obligation_snooze, test_obligation_summary, test_obligations,
test_parties_extended, test_quota, test_re_extract, test_relationships,
test_remap_preservation, test_reminders, test_reread, test_scheduler_benchmark,
test_self_party, test_signature_fields, test_smoke, test_smoke_m0,
test_tenant_isolation, test_tenant_journey, test_term_anchor
```

---

## Known Gaps

| Gap | Severity | Issue |
|---|---|---|
| Playwright e2e scaffold missing | CRITICAL | #187 |
| `frontend/tests/` directory missing | CRITICAL | #187 |
| UAT smoke run on staging pending | HIGH | #75 |
| Wireframe Flow 2/3 not yet reviewed | HIGH | #500 |
| DEC-048 open questions not pressure-tested | HIGH | #297 |

---

## Decisions / Notes

- **D-08:** Backend `test_drules_regression.py` covers API layer. E2E needed for UI layer byte-for-byte string check.
- **D-10:** `test_tenant_isolation.py` covers API layer. E2E cross-tenant case needed.
- **Pilot window:** if < 2 weeks → #187 is HIGH/blocker per PM guidance.
- **UAT env:** `uat-demo` seeded (PR #73). `uat-demo-b` (G cases) + `uat-demo-noconsent` (H cases) need Backend seed before #75 can proceed.

---

## Next Actions This Session

1. **#500** — Review wireframe lo-fi artifact (Flow 2 + Flow 3), post findings on issue
2. **#187** — Scaffold Playwright (`playwright/` dir, config, CI hook, fixtures)
3. **#297** — Post pressure-test answers for Open Questions Q1–Q10
