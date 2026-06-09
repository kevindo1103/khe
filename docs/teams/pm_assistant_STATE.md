# PM_Assistant STATE — Khế MVP

*Branch: `claude/pm-assistant` | Last updated: 2026-06-09 | v0.2*

---

## Active Sprint Context

**Current phase:** Sprint 0 bootstrap (pre-sprint)  
**Sprint 0 goal:** Repo + CI/CD skeleton, multi-tenant pattern, Telegram bot wired, OCR/LLM provider selected, 1 firm LOI.

---

## Open Decisions (Draft — awaiting user ratify)

| ID | Decision | Status | Date |
|---|---|---|---|
| DEC-001 | Stack ratification (FastAPI + SQLite multi-tenant per BRD A-1) | Draft | 2026-06-09 |
| DEC-002 | OCR + LLM provider selection | Draft | 2026-06-09 |
| DEC-003 | Hosting provider + data residency (NFR-3, NĐ 13/2023) | Draft | 2026-06-09 |
| DEC-004 | Naming "Khế" finalization (R-7, trademark check) | Draft | 2026-06-09 |
| DEC-005 | Sprint cadence — weekly (mirror Bingxue) or slower | Draft | 2026-06-09 |
| DEC-006 | Reminder channel: **Telegram bot** (telebot / python-telegram-bot) replaces Zalo ZNS | **Ratified** by user 2026-06-09 |

---

## Day-1 Blockers (Surface to user EARLY)

| Blocker | Risk | Action needed | Owner |
|---|---|---|---|
| Firm design-partner LOI | Need 1 signed firm before Sprint 1 | Identify + contact target firm | User (Kevin) |
| OCR + LLM provider | Budget + accuracy benchmark decision | Select provider, get API keys | Sprint 0 |
| Hosting + data residency | NĐ 13/2023 VN data center requirement | Confirm VPS provider + region | Sprint 0 |
| Naming finalization | R-7 trademark risk before launch | Trademark check | Pre-launch |

*(Zalo OA registration removed — no longer needed. Telegram bot requires only a bot token from @BotFather, no approval process.)*

---

## Session Topology Status

| # | Session | Branch | Status |
|---|---|---|---|
| 1 | ERP_Docs | `claude/edit-git-docs-Khe01` | Branch created ✅ — not yet spawned |
| 2 | ERP_PM_Assistant | `claude/pm-assistant` | Active ✅ |
| 3 | ERP_Backend | `claude/feat-*` | Not spawned |
| 4 | ERP_Frontend_Admin | `claude/feat-*` | Not spawned |
| 5 | ERP_PWA_Chat | `claude/feat-*` | Not spawned |
| 6 | ERP_QC | `claude/test-*` | Not spawned |
| 7 | ERP_Designer | `claude/design-*` | Not spawned |
| 8 | ERP_Infra | `claude/infra-*` | Not spawned |
| 9 | ERP_AI | `claude/feat-ai-*` | Not spawned |
| 10 | ERP_Compliance | `claude/compliance-*` | Not spawned |

---

## INC Log (Incidents)

*No incidents yet. First incident will be INC-01.*

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
- [x] `docs/teams/pm_assistant_STATE.md` created (this file)
- [x] DEC-006 ratified: Telegram replaces Zalo ZNS
- [ ] ERP_Docs session spawned on `claude/edit-git-docs-Khe01`
- [ ] GitHub topology labels created (manual — see note below)
- [ ] PROJECT_PLAN v0.1 drafted
- [ ] Sprint 0 kickoff

**Labels note:** GitHub MCP tools do not expose a `create_label` endpoint. Labels must be created manually in GitHub repo Settings → Labels, or via `gh` CLI. Required labels:
- `from:pm`, `from:backend`, `from:frontend`, `from:qc`, `from:designer`, `from:infra`, `from:ai`, `from:compliance`, `from:docs`
- `for:pm`, `for:backend`, `for:frontend`, `for:qc`, `for:designer`, `for:infra`, `for:ai`, `for:compliance`, `for:docs`
- `task-assignment`, `relay`, `spec-conflict`
- `status:planned`, `status:in-progress`, `status:review`, `status:done-staging`
- `blocker:human-needed`, `blocker:waiting-dependency`
- `docs-inbox`

---

## Sprint Retrospective Notes

*None yet.*

---

## Weekly Review Log

*No reviews yet.*
