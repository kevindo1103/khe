# Khế — Cairn Spawn Templates

Spawn prompts for all 10 sessions in the Khế Cairn topology.
Paste the relevant file into a fresh Claude Code session to spawn that role.

| Session | File | Branch pattern |
|---|---|---|
| ERP_PM_Assistant | `SPAWN_PM_ASSISTANT.md` (see repo root uploads) | `claude/pm-assistant` (long-lived) |
| ERP_Docs | `SPAWN_ERP_DOCS.md` | `claude/edit-git-docs-Khe01` (long-lived) |
| ERP_Backend | `SPAWN_ERP_BACKEND.md` | `claude/feat-backend-*` |
| ERP_Frontend_Admin | `SPAWN_ERP_FRONTEND_ADMIN.md` | `claude/feat-admin-*` |
| ERP_PWA_Chat | `SPAWN_ERP_PWA_CHAT.md` | `claude/feat-chat-*` |
| ERP_QC | `SPAWN_ERP_QC.md` | `claude/test-*` |
| ERP_Designer | `SPAWN_ERP_DESIGNER.md` | `claude/design-*` |
| ERP_Infra | `SPAWN_ERP_INFRA.md` | `claude/infra-*` |
| ERP_AI | `SPAWN_ERP_AI.md` | `claude/feat-ai-*` |
| ERP_Compliance | `SPAWN_ERP_COMPLIANCE.md` | `claude/compliance-*` |

## How to use

1. Open a new Claude Code session (web or CLI)
2. Set the working directory to this repo
3. Paste the full contents of the relevant spawn file as your first message
4. Session will output its kickoff checklist and await your direction

## Cross-session communication

All sessions communicate via GitHub Issues with labels.
See `CLAUDE.md §Cross-session communication` for the full protocol.

**DOCS_INBOX:** [#1](https://github.com/kevindo1103/khe/issues/1) — all post-merge doc updates go here.
