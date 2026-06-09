# KHE_PM_Assistant STATE — Khế MVP

*Branch: `claude/pm-assistant` | Last updated: 2026-06-09 | v0.5*

---

## Active Sprint Context

**Current phase:** Sprint 0 bootstrap (kicking off)
**Sprint 0 goal:** FastAPI + multi-tenant DB scaffold, CI/CD skeleton, Telegram bot wired, Vision extraction benchmark, 1 firm LOI. Runs **in parallel** with M0 vertical slice (Sprint 1).

---

## Ratified Decisions

| ID | Decision | Status | Date |
|---|---|---|---|
| DEC-001 | Stack: FastAPI + SQLite multi-tenant per BRD A-1 | Draft | 2026-06-09 |
| DEC-002 | OCR+LLM: `VisionExtractionProvider` — Gemini 2.0 Flash primary (~150đ/doc) + Claude Haiku fallback (~300đ/doc if accuracy <90%). Sprint 0 benchmark on 15 PII-scrubbed Bingxue HĐ samples. | **Ratified** | 2026-06-09 |
| DEC-003 | Hosting provider + data residency | Draft | 2026-06-09 |
| DEC-004 | Naming "Khế" finalization (R-7) | Draft | 2026-06-09 |
| DEC-005 | Sprint cadence | Draft | 2026-06-09 |
| DEC-006 | Reminder channel: Telegram bot replaces Zalo ZNS | **Ratified** | 2026-06-09 |
| DEC-007 | Sprint 0 infra runs in parallel with M0 vertical slice | **Ratified** | 2026-06-09 |
| DEC-008 | KHE_Backend is first feature session to spawn | **Ratified** | 2026-06-09 |
| DEC-009 | Session prefix renamed ERP_ → KHE_ across all sessions | **Ratified** | 2026-06-09 |
| DEC-010 | NĐ 13/2023 Phase 1: US-hosted LLM API acceptable with explicit consent + audit log. Phase 2+ re-evaluate self-host when volume justifies. | **Ratified** | 2026-06-09 |

---

## Day-1 Blockers

| Blocker | Risk | Action needed | Owner |
|---|---|---|---|
| Firm design-partner LOI | Need 1 signed firm before Sprint 1 ships | Identify + contact target firm | User (Kevin) |
| Hosting + data residency | NĐ 13/2023 VN data center if required | Confirm VPS provider + region | Sprint 0 |
| Naming finalization | R-7 trademark risk before launch | Trademark check | Pre-launch |

*(DEC-002 ratified: OCR/LLM unblocked. DEC-010 ratified: hosting unblocked for Phase 1.)*

---

## Session Topology Status

| # | Session | Branch | Status |
|---|---|---|---|
| 1 | KHE_Docs | `claude/edit-git-docs-Khe01` | Branch created ✅ — not yet spawned |
| 2 | KHE_PM_Assistant | `claude/pm-assistant` | Active ✅ |
| 3 | KHE_Backend | `claude/feat-*` | Task issued ✅ — ready to spawn |
| 4 | KHE_Frontend_Admin | `claude/feat-*` | Not spawned |
| 5 | KHE_PWA_Chat | `claude/feat-*` | Not spawned |
| 6 | KHE_QC | `claude/test-*` | Not spawned |
| 7 | KHE_Designer | `claude/design-*` | Not spawned |
| 8 | KHE_Infra | `claude/infra-*` | Not spawned |
| 9 | KHE_AI | `claude/feat-ai-*` | Task issued ✅ — ready to spawn |
| 10 | KHE_Compliance | `claude/compliance-*` | Not spawned |

---

## INC Log (Incidents)

*No incidents yet.*

---

## FM Log (Failure Modes)

*No recurring failure modes yet. Bingxue learnings pre-loaded in CLAUDE.md Common Bug Patterns.*

---

## Bootstrap Checklist (2026-06-09)

- [x] `CLAUDE.md` exists at root
- [x] `MVP_BRD_Khe.md` at root (pending move to `docs/MVP_BRD_Khe_v0.1.md` by KHE_Docs)
- [x] DOCS_INBOX issue [#1](https://github.com/kevindo1103/khe/issues/1) created
- [x] `claude/edit-git-docs-Khe01` branch created
- [x] `docs/teams/pm_assistant_STATE.md` created
- [x] Cairn spawn templates in `docs/spawn/` (all 10 KHE_ sessions)
- [x] DEC-002 ratified: VisionExtractionProvider (Gemini Flash + Claude Haiku)
- [x] DEC-006 ratified: Telegram replaces Zalo
- [x] DEC-007 ratified: Sprint 0 parallel with M0
- [x] DEC-008 ratified: KHE_Backend first
- [x] DEC-009 ratified: KHE_ prefix
- [x] DEC-010 ratified: NĐ 13 Phase 1 US-hosted OK
- [x] KHE_Backend task issue [#2](https://github.com/kevindo1103/khe/issues/2)
- [x] KHE_AI benchmark task issue [#3](https://github.com/kevindo1103/khe/issues/3)
- [x] PROJECT_PLAN v0.1 draft in DOCS_INBOX
- [ ] KHE_Backend session spawned
- [ ] KHE_AI session spawned
- [ ] GitHub topology labels created (manual — Settings → Labels)
- [ ] KHE_Docs session spawned
- [ ] Sprint 0 kickoff

**Labels to create manually (Settings → Labels):**
- `from:pm/backend/frontend/qc/designer/infra/ai/compliance/docs`
- `for:pm/backend/frontend/qc/designer/infra/ai/compliance/docs`
- `task-assignment` · `relay` · `spec-conflict` · `docs-inbox`
- `status:planned` · `status:in-progress` · `status:review` · `status:done-staging`
- `blocker:human-needed` · `blocker:waiting-dependency`

---

## Sprint Retrospective Notes

*None yet.*

---

## Weekly Review Log

*No reviews yet.*
