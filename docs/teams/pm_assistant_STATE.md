# KHE_PM_Assistant STATE — Khế MVP

*Branch: `claude/pm-assistant` | Last updated: 2026-06-09 | v0.5*

---

## Active Sprint Context

**Current phase:** Sprint 0 bootstrap (kicking off)
**Sprint 0 goal:** FastAPI + multi-tenant DB scaffold, CI/CD, Telegram bot, Vision extraction benchmark, 1 firm LOI. Runs **in parallel** with M0 vertical slice (Sprint 1).

---

## Ratified Decisions

| ID | Decision | Status | Date |
|---|---|---|---|
| DEC-001 | Stack: FastAPI + SQLite multi-tenant per BRD A-1 | Draft | 2026-06-09 |
| DEC-002 | `VisionExtractionProvider` — Gemini 2.0 Flash primary (~150đ/doc) + Claude Haiku fallback (~300đ/doc if accuracy <90%). Sprint 0 benchmark on 15 PII-scrubbed Bingxue HĐ samples. | **Ratified** | 2026-06-09 |
| DEC-003 | Hosting provider + data residency | Draft | 2026-06-09 |
| DEC-004 | Naming "Khế" finalization (R-7) | Draft | 2026-06-09 |
| DEC-005 | Sprint cadence | Draft | 2026-06-09 |
| DEC-006 | Telegram bot replaces Zalo ZNS | **Ratified** | 2026-06-09 |
| DEC-007 | Sprint 0 infra parallel with M0 | **Ratified** | 2026-06-09 |
| DEC-008 | KHE_Backend first session to spawn | **Ratified** | 2026-06-09 |
| DEC-009 | Session prefix ERP_ → KHE_ | **Ratified** | 2026-06-09 |
| DEC-010 | NĐ 13/2023 Phase 1: US-hosted LLM OK with explicit consent + audit log | **Ratified** | 2026-06-09 |

---

## Day-1 Blockers

| Blocker | Risk | Action | Owner |
|---|---|---|---|
| Firm design-partner LOI | Need 1 signed firm before Sprint 1 ships | Identify + contact | User (Kevin) |
| Hosting + data residency | VPS provider decision | Confirm provider + region | Sprint 0 |
| Naming finalization | R-7 trademark risk | Trademark check | Pre-launch |

---

## Session Topology Status

| # | Session | Status |
|---|---|---|
| 1 | KHE_Docs | Branch created ✅ — not yet spawned |
| 2 | KHE_PM_Assistant | Active ✅ |
| 3 | KHE_Backend | Task [#2](https://github.com/kevindo1103/khe/issues/2) issued ✅ — ready to spawn |
| 4-7 | KHE_Frontend_Admin/PWA/QC/Designer | Not spawned |
| 8 | KHE_Infra | Not spawned |
| 9 | KHE_AI | Task [#3](https://github.com/kevindo1103/khe/issues/3) issued ✅ — ready to spawn |
| 10 | KHE_Compliance | Not spawned |

---

## Bootstrap Checklist (2026-06-09)

- [x] CLAUDE.md at root
- [x] MVP_BRD_Khe.md at root (KHE_Docs to move to docs/)
- [x] DOCS_INBOX [#1](https://github.com/kevindo1103/khe/issues/1)
- [x] `claude/edit-git-docs-Khe01` branch
- [x] `docs/spawn/SPAWN_KHE_*.md` (all 10 sessions)
- [x] DEC-002, DEC-006, DEC-007, DEC-008, DEC-009, DEC-010 ratified
- [x] KHE_Backend [#2](https://github.com/kevindo1103/khe/issues/2) + KHE_AI [#3](https://github.com/kevindo1103/khe/issues/3)
- [x] PROJECT_PLAN v0.1 draft in DOCS_INBOX
- [ ] KHE_Backend + KHE_AI sessions spawned by user
- [ ] GitHub labels created (Settings → Labels)
- [ ] KHE_Docs spawned
- [ ] Sprint 0 kickoff

---

## INC Log / FM Log

*No incidents or failure modes yet.*

---

## Weekly Review Log

*No reviews yet.*
