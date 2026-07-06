# CAIRN Framework Alignment — Servanda (Khế)

*Skeleton created cycle 8 (2026-07-06). Detailed content TBD from CAIRN v0.7 spec by KHE_Docs task-owner per Sprint 7 backlog.*

---

## What is CAIRN?

**CAIRN** = framework tham chiếu external ([multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) fork) cho LLM-driven multi-role dev workflows. Cung cấp:
- Failure mode (FM-*) catalog
- Session spawn templates
- Anti-pattern catalog
- Post-claim verification discipline

## Adoption stance — Cherry-pick (NOT blind upgrade)

Kevin ratified cherry-pick approach 2026-07-06. Servanda selective adopt 5 items từ CAIRN v0.7, NOT wholesale.

### ✅ Adopted (folded cycle 8)

| Item | Where folded |
|---|---|
| **FM-16 role drift** | CLAUDE.md §Common Bug Patterns |
| **FM-17 hallucinated artifact** | CLAUDE.md §Common Bug Patterns |
| **P-10 post-claim verification** | CLAUDE.md §Lead/Dev workflow (post-role table) |
| **Trust-done anti-pattern** | CLAUDE.md §Anti-Patterns |
| **Scope-drift anti-pattern** | CLAUDE.md §Anti-Patterns |
| **Partial-read discipline** | CLAUDE.md NEW §Partial-Read Discipline (before Docs Ownership) |
| **Spawn templates skeleton** | `docs/spawn/SPAWN_LEAD.md` + `SPAWN_DEV.md` + `SPAWN_DOCS_EDITOR.md` (skeletons cycle 8, content Sprint 7) |

### ❌ Intentionally NOT adopted (rationale TBD Sprint 7)

*(To be filled by KHE_Docs task-owner after reading full CAIRN v0.7 spec — decisions on which CAIRN items conflict with existing Servanda D-rules / DEC-047 / Docs Ownership Protocol.)*

Examples of items likely NOT adopted (subject to Sprint 7 review):
- Any CAIRN principle numbered P-1..P-9 that would collide with Servanda BRD §4 P-1..P-6 (Servanda P-6 = obligation-source-agnostic, DEC-056)
- CAIRN failure modes FM-1..FM-15 if they duplicate existing Servanda bug patterns
- CAIRN spawn templates if they don't match Servanda's session topology (KHE_* lead / Windsurf_* + Claude_*_Dev dev pairs)

## Numbering conventions

- **CAIRN P-10** ≠ **BRD §4 P-*** — different domain. CAIRN P-N = internal workflow discipline framework; BRD P-N = product principles (Servanda-specific).
- **FM-16, FM-17** are **first** FM-numbered entries in Servanda CLAUDE.md (§Glossary defines FM-XX pattern but §Common Bug Patterns previously used unnumbered rows).

## Version tracking

- `.cairn-version` file at repo root = version currently adopted (initial: `v0.7`).
- Future CAIRN upgrade = **explicit decision** in DOCS_INBOX + Kevin ratify. Bump `.cairn-version`.

## Related decisions

- **DEC-047** (PR Scope-Lock Enforcement) — companion to FM-16 role drift + Scope-drift anti-pattern
- **D-14/D-15/D-16/D-17** (Servanda D-rules) — companion to P-10 post-claim verification (verify claims in D-02 confirm flow, D-07 audit, etc.)

---

*docs/CAIRN.md — skeleton cycle 8. Full content per Sprint 7 backlog (KHE_Docs task-owner + CAIRN v0.7 spec read).*
