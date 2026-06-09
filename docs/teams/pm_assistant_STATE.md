# PM_Assistant STATE — Khế MVP

*Branch: `claude/pm-assistant` | Last updated: 2026-06-09 | v0.3*

---

## Active Sprint Context

**Current phase:** Sprint 0 bootstrap (kicking off)  
**Sprint 0 goal:** FastAPI + multi-tenant DB scaffold, CI/CD skeleton, Telegram bot wired, OCR/LLM provider selected, 1 firm LOI. Runs **in parallel** with M0 vertical slice (Sprint 1).

---

## Ratified Decisions

| ID | Decision | Status | Date |
|---|---|---|---|
| DEC-001 | Stack: FastAPI + SQLite multi-tenant per BRD A-1 | Draft | 2026-06-09 |
| DEC-002 | OCR + LLM provider selection | Draft | 2026-06-09 |
| DEC-003 | Hosting provider + data residency (NFR-3, NĐ 13/2023) | Draft | 2026-06-09 |
| DEC-004 | Naming "Khế" finalization (R-7, trademark check) | Draft | 2026-06-09 |
| DEC-005 | Sprint cadence | Draft | 2026-06-09 |
| DEC-006 | Reminder channel: Telegram bot replaces Zalo ZNS | **Ratified** | 2026-06-09 |
| DEC-007 | Sprint 0 infra runs **in parallel** with M0 vertical slice (Sprint 1) | **Ratified** | 2026-06-09 |
| DEC-008 | ERP_Backend is first feature session to spawn (FastAPI + multi-tenant scaffold) | **Ratified** | 2026-06-09 |

---

## Day-1 Blockers

| Blocker | Risk | Action needed | Owner |
|---|---|---|---|
| Firm design-partner LOI | Need 1 signed firm before Sprint 1 ships | Identify + contact target firm | User (Kevin) |
| OCR + LLM provider | Budget + accuracy benchmark decision | Select provider, get API keys | Sprint 0 |
| Hosting + data residency | NĐ 13/2023 VN data center requirement | Confirm VPS provider + region | Sprint 0 |
| Naming finalization | R-7 trademark risk before launch | Trademark check | Pre-launch |

---

## Session Topology Status

| # | Session | Branch | Status |
|---|---|---|---|
| 1 | ERP_Docs | `claude/edit-git-docs-Khe01` | Branch created ✅ — not yet spawned |
| 2 | ERP_PM_Assistant | `claude/pm-assistant` | Active ✅ |
| 3 | ERP_Backend | `claude/feat-*` | Task issued ✅ — ready to spawn |
| 4 | ERP_Frontend_Admin | `claude/feat-*` | Not spawned |
| 5 | ERP_PWA_Chat | `claude/feat-*` | Not spawned |
| 6 | ERP_QC | `claude/test-*` | Not spawned |
| 7 | ERP_Designer | `claude/design-*` | Not spawned |
| 8 | ERP_Infra | `claude/infra-*` | Not spawned |
| 9 | ERP_AI | `claude/feat-ai-*` | Not spawned |
| 10 | ERP_Compliance | `claude/compliance-*` | Not spawned |

---

## INC Log (Incidents)

*No incidents yet.*

---

## FM Log (Failure Modes)

*No recurring failure modes logged yet. Bingxue learnings pre-loaded in CLAUDE.md Common Bug Patterns.*

---

## Bootstrap Checklist (2026-06-09)

- [x] `CLAUDE.md` exists at root
- [x] `MVP_BRD_Khe.md` exists at root (pending move to `docs/MVP_BRD_Khe_v0.1.md` by ERP_Docs)
- [x] DOCS_INBOX issue created ([#1](https://github.com/kevindo1103/khe/issues/1), pinned)
- [x] `claude/edit-git-docs-Khe01` branch created
- [x] `claude/pm-assistant` branch exists
- [x] `docs/teams/pm_assistant_STATE.md` created
- [x] DEC-006: Telegram replaces Zalo ZNS
- [x] DEC-007: Sprint 0 infra parallel with M0
- [x] DEC-008: ERP_Backend first session
- [x] PROJECT_PLAN v0.1 draft posted to DOCS_INBOX
- [x] ERP_Backend task assignment issue created
- [ ] ERP_Backend session spawned by user
- [ ] GitHub topology labels created (manual — Settings → Labels)
- [ ] ERP_Docs session spawned
- [ ] Sprint 0 kickoff

**Labels note:** Must be created manually in GitHub repo Settings → Labels. Required:
- `from:pm`, `from:backend`, `from:frontend`, `from:qc`, `from:designer`, `from:infra`, `from:ai`, `from:compliance`, `from:docs`
- `for:pm`, `for:backend`, `for:frontend`, `for:qc`, `for:designer`, `for:infra`, `for:ai`, `for:compliance`, `for:docs`
- `task-assignment`, `relay`, `spec-conflict`, `docs-inbox`
- `status:planned`, `status:in-progress`, `status:review`, `status:done-staging`
- `blocker:human-needed`, `blocker:waiting-dependency`

---

## Sprint Retrospective Notes

*None yet.*

---

## Weekly Review Log

*No reviews yet.*
