# KHE_QC — Session STATE

> Owner: **KHE_QC** (lead) + **Windsurf_QC** (dev). Scope: `backend/tests/**`,
> `frontend/tests/**`, Playwright e2e, fixtures, smoke automation,
> `docs/teams/qc_STATE.md`.
> Branch: `claude/test-m0m1-smoke`.

_Last updated: 2026-06-19 (session spawn)._

## Decisions in force
- **D-01 / D-06** — AI is read-only; tests must assert no fabrication
  (None over guessing) for extraction outputs.
- **D-08** — chat "không tìm thấy" path must be covered by retrieval tests
  (no hallucinated answers).
- **D-09** — firm portal endpoints must be read-only at MVP; regression
  guard required.
- **D-10** — partner cross-tenant access only when SME consent granted;
  authz negative tests mandatory.
- **Multi-Tenant DB** — every test that touches tenant data must go through
  `get_tenant_session(tid)`; NEVER instantiate `SessionLocal()` directly.

## Scope (per CLAUDE.md §Session Topology row 6)
- Backend unit + integration tests (`backend/tests/**`).
- Frontend component + page tests (`frontend/tests/**`).
- Playwright e2e (admin + firm + PWA chat flows).
- Fixtures (PII-scrubbed; mirror AI fixture rules — `data/`, `manifest.json`
  gitignored if real docs).
- Smoke automation for staging post-deploy.

## Inventory snapshot (2026-06-19)
- `backend/tests/test_smoke.py` exists — import-level smoke only (per
  `pr-quality-gate.yml` shape).
- `frontend/tests/` — **not yet present**; Vite + RTL/Playwright wiring
  pending Sprint 1 frontend session spawn.
- No fixtures directory under `backend/tests/fixtures/` yet.

## M0 / M1 smoke targets (awaiting task instruction)
Placeholders to be confirmed when next task lands:
- M0 = backend skeleton import + alembic single-head + master.db boot.
- M1 = ingest endpoint round-trip (upload → document row → event row),
  multi-tenant isolation negative test (cross-tenant 404).

## Done
- [x] Branch renamed `claude/compassionate-dijkstra-hy46yh` →
  `claude/test-m0m1-smoke`.
- [x] Read CLAUDE.md §D-rules, §Multi-Tenant DB, §Common Bug Patterns.

## Blocked / pending
- **SPAWN_KHE_QC.md not found** in `docs/spawn/` (directory doesn't exist).
  Awaiting either the spawn doc or direct task instruction from PM. Flagged
  to user at session kickoff.
- Frontend test harness not yet scaffolded — depends on KHE_Frontend_Admin
  / KHE_PWA_Chat spawn.

## Inbox
- (none yet — Step 0 `list for:qc open issues` to run on first real task.)

## Next
- Wait for task instruction (per kickoff prompt step "đợi task instruction
  tiếp theo").
- On task land: run Decision Review Gate cascade (Strategy → BRD → SRS →
  CLAUDE.md §D-rules + §Multi-Tenant DB → system_architecture_khe.html)
  before writing tests.
</content>
</invoke>