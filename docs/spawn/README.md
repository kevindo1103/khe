# Khế — Cairn Spawn Templates

> v0.2 — STEP 0 BRANCH + SCOPE-LOCK + ROLE-LOCK + Claim verification applied to all templates (Bingxue Cairn N=1 pattern)

Paste relevant file into a fresh Claude Code session to spawn that role.

| Session | Spawn file | Branch pattern | Type |
|---|---|---|---|
| KHE_PM_Assistant | `SPAWN_KHE_PM_ASSISTANT.md` | `claude/pm-assistant` (long-lived) | Single-owner |
| KHE_Docs | `SPAWN_KHE_DOCS.md` | `claude/edit-git-docs-Khe01` (long-lived) | Single-owner |
| KHE_Backend | `SPAWN_KHE_BACKEND.md` | `claude/feat-backend-<desc>` | Lead + Windsurf pair |
| KHE_Frontend_Admin | `SPAWN_KHE_FRONTEND_ADMIN.md` | `claude/feat-admin-<desc>` | Lead + Windsurf pair |
| KHE_PWA_Chat | `SPAWN_KHE_PWA_CHAT.md` | `claude/feat-chat-<desc>` | Lead + Windsurf pair |
| KHE_QC | `SPAWN_KHE_QC.md` | `claude/test-<scope>-<desc>` | Lead + Windsurf pair |
| KHE_AI | `SPAWN_KHE_AI.md` | `claude/feat-ai-<scope>-<desc>` | Single-owner |
| KHE_Infra | `SPAWN_KHE_INFRA.md` | `claude/infra-<scope>-<desc>` | Single-owner |
| KHE_Designer | `SPAWN_KHE_DESIGNER.md` | `claude/design-<scope>-<desc>` | Single-owner |
| KHE_Compliance | `SPAWN_KHE_COMPLIANCE.md` | `claude/compliance-<scope>-<desc>` | Single-owner |

## Enforcement pattern (all templates v0.2)
- **STEP 0 BRANCH** — rename trước ANY read/edit (feature branches) OR STOP (long-lived branches)
- **SCOPE-LOCK** — ĐƯỢC/KHÔNG sửa file list explicit
- **ROLE-LOCK** — lead sessions: plan→assign→review, no self-implement
- **Bootstrap order** — numbered, specific files
- **Claim verification** — `git log --oneline -1` required với mọi merge/push claim

## Active decisions (2026-06-10)
- **DEC-002:** `VisionExtractionProvider` — Gemini Flash + Claude Haiku fallback
- **DEC-006:** Telegram bot (no Zalo) — re-confirmed 2026-06-10
- **DEC-007:** Sprint 0 parallel with M0
- **DEC-009:** Session prefix KHE_ (not ERP_)
- **DEC-010:** NĐ 13/2023 Phase 1 — US-hosted OK with consent + audit log
- **DEC-011:** B2B2B — firm trả per-client, SME free Phase 1
- **DEC-012:** Concierge onboarding 20 SME đầu (không bắt tự upload)
- **DEC-013:** 2-firm pilot (đại lý thuế + law firm), 10 SME mỗi firm, 90 ngày
- **DEC-014:** Positioning "ngôi nhà cho hợp đồng sau khi ký" (hậu sóng NĐ 337)
- **DEC-015:** Kill/pivot signals trong BRD v0.2
- **DEC-016:** OPEN — freemium paywall lever (Telegram giữ, ZNS bỏ)

*Strategy v2 chi tiết: `docs/teams/pm_assistant_STATE.md` §Strategy v2*

## Issues
- [#1](https://github.com/kevindo1103/khe/issues/1) DOCS_INBOX (3 pending)
- [#2](https://github.com/kevindo1103/khe/issues/2) KHE_Backend Sprint 0 scaffold
- [#3](https://github.com/kevindo1103/khe/issues/3) KHE_AI vision benchmark
