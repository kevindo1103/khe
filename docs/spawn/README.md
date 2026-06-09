# Khế — Cairn Spawn Templates

Spawn prompts for all 10 KHE_ sessions. Paste the relevant file into a fresh Claude Code session.

| Session | Spawn file | Branch pattern |
|---|---|---|
| KHE_PM_Assistant | `SPAWN_KHE_PM_ASSISTANT.md` | `claude/pm-assistant` (long-lived) |
| KHE_Docs | `SPAWN_KHE_DOCS.md` | `claude/edit-git-docs-Khe01` (long-lived) |
| KHE_Backend | `SPAWN_KHE_BACKEND.md` | `claude/feat-backend-*` |
| KHE_Frontend_Admin | `SPAWN_KHE_FRONTEND_ADMIN.md` | `claude/feat-admin-*` |
| KHE_PWA_Chat | `SPAWN_KHE_PWA_CHAT.md` | `claude/feat-chat-*` |
| KHE_QC | `SPAWN_KHE_QC.md` | `claude/test-*` |
| KHE_Designer | `SPAWN_KHE_DESIGNER.md` | `claude/design-*` |
| KHE_Infra | `SPAWN_KHE_INFRA.md` | `claude/infra-*` |
| KHE_AI | `SPAWN_KHE_AI.md` | `claude/feat-ai-*` |
| KHE_Compliance | `SPAWN_KHE_COMPLIANCE.md` | `claude/compliance-*` |

## How to use

1. Open a new Claude Code session (web or CLI)
2. Set working directory to this repo
3. Paste the full contents of the relevant spawn file as your first message
4. Session outputs kickoff checklist and awaits direction

## Key decisions in effect (as of 2026-06-09)

- **DEC-002:** `VisionExtractionProvider` — Gemini 2.0 Flash + Claude Haiku fallback
- **DEC-006:** Telegram bot (no Zalo ZNS)
- **DEC-010:** NĐ 13/2023 Phase 1 — US-hosted OK with explicit consent + audit log

## DOCS_INBOX

[#1](https://github.com/kevindo1103/khe/issues/1) — all post-merge doc updates queue here.

## Active task issues

- [#2](https://github.com/kevindo1103/khe/issues/2) — KHE_Backend Sprint 0 scaffold
- [#3](https://github.com/kevindo1103/khe/issues/3) — KHE_AI vision benchmark
