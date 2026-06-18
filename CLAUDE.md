# Khế — Claude Code Context

*Last updated: 2026-06-09 (v0.1 — draft, awaiting docs-editor session fold) — MVP BRD v0.1 reference*

> **Tên mã tạm:** Khế *(placeholder per R-7 — sẽ rename khi launch)*
> Vibe Document OS cho SME Vietnam — chat-first, distributed via law firm / tax agent kênh.

---

## Project context

**Reference:** `docs/MVP_BRD_Khe_v0.1.md` *(current file: `MVP_BRD_Khe.md` at root — KHE_Docs to move + version on first fold)*

**MVP scope (M0 → M3):** Ingest + retrieve + deadline. KHÔNG soạn HĐ tự động (drafting), KHÔNG review rủi ro, KHÔNG ký số (integrate sau), KHÔNG đa thị trường (VN-first), KHÔNG marketplace template.

**Vertical seed:** F&B / bán lẻ (HĐ thuê mặt bằng + HĐ nhà cung cấp + HĐ lao động). Architecture phải general nhưng seed sắc theo vertical.

**Distribution:** Law firm + tax agent (đại lý thuế) làm channel — họ vốn là "phòng pháp lý thuê ngoài" SME đã có. Tầng deadline reminder ĐẺ việc cho firm thay vì cướp việc.

**Catalysts:**
- NĐ 337/2025 (hợp đồng lao động điện tử) hiệu lực 01/01/2026
- NĐ 70/2025 (hóa đơn điện tử, kết nối thuế)
- NĐ 13/2023 (bảo vệ dữ liệu cá nhân) — compliance baseline

---

## Docs Ownership Protocol (BẮT BUỘC)

**Toàn bộ tài liệu (`docs/` + root `*.md`) do MỘT session docs-editor duy nhất quản lý** —
branch `claude/edit-git-docs-Khe01`. Mục đích: giữ docs nhất quán, không để stale cross-reference.

### Mọi session KHÁC (không phải docs-editor)
- **KHÔNG sửa trực tiếp** file trong `docs/` hoặc root `*.md`.
  - Ngoại lệ: được phép thêm ghi chú vận hành vào `CLAUDE.md` (bug pattern, fix mới).
- Sau bất kỳ thay đổi nào ảnh hưởng tới **business rule, schema, API, UI, deploy info, hoặc known bug**,
  **comment vào DOCS_INBOX issue [#1](https://github.com/kevindo1103/khe/issues/1)** (pinned, label `docs-inbox`) theo template:
  ```
  ### <YYYY-MM-DD> — <session / branch>
  - **PR / trigger:** #<số PR> → `<base branch>`
  - **Đã đụng:** <file / module / area>
  - **Thay đổi:** <tóm tắt cái gì thay đổi và tại sao>
  - **Docs cần cập nhật:** <BRD §x / SRS §y / Glossary / PROJECT_PLAN / CLAUDE.md / "chưa rõ">
  - **Ambiguity / cần PM xác nhận:** <nếu có, hoặc "none">
  ```
- **Post-merge rule (BẮT BUỘC):** Khi PR merge vào `main` (hoặc `staging` cho spec-impact cần frontend sync sớm),
  session author MUST comment vào DOCS_INBOX trong vòng 24h. Bỏ qua = rule violation.
- Không tự ý resolve ambiguity — nêu trong comment để docs-editor xử lý.

### Session docs-editor (branch `claude/edit-git-docs-Khe01`)
- Đọc DOCS_INBOX comments mới → fold canonical docs theo cascade order:
  **Strategy → BRD → SRS → Glossary → PROJECT_PLAN → CLAUDE.md → Mockup**.
- Cập nhật version number + changelog entry ở mỗi file bị ảnh hưởng.
- Reply DOCS_INBOX comment với: `✅ Folded — <docs/version kết quả>`.
- Weekly Review (Monday): check `## Weekly Review Log` trong DOCS_INBOX. Run 8-item checklist.

---

## Decision Review Gate (BẮT BUỘC trước mọi module/feature decision)

**Trước khi đề xuất hoặc implement bất kỳ module, feature, schema, hoặc API mới:**

### Cascade đọc bắt buộc (theo thứ tự)

| # | Tài liệu | Đọc khi nào |
|---|---|---|
| 1 | `docs/PRODUCT_STRATEGY_Khe.md` | LUÔN LUÔN — JTBD, personas, positioning, D-rules rationale |
| 2 | `MVP_BRD_Khe.md` | LUÔN LUÔN — FR/NFR, AC, scope boundary |
| 3 | `CLAUDE.md` §D-rules | LUÔN LUÔN — 10 business invariants |
| 4 | `CLAUDE.md` §Multi-Tenant DB | Khi chạm schema hoặc query |
| 5 | `docs/system_architecture_khe.html` | Khi chạm module boundary, API shape, hoặc external service |
| 6 | `docs/teams/<myteam>_STATE.md` | Mỗi session kickoff |

### Checklist trước khi propose decision

- [ ] Feature này phục vụ JTBD nào? (J1–J5 trong Strategy §3)
- [ ] Feature này có vi phạm D-rules không? (đặc biệt D-01, D-06, D-08, D-09, D-10)
- [ ] Feature này có thay đổi schema / API không? → PHẢI comment DOCS_INBOX
- [ ] Feature này có chạm multi-tenant isolation không? → Review §Multi-Tenant DB
- [ ] Feature này có trong MVP scope (M0–M3) không? Nếu không → flag lên PM trước
- [ ] Feature này có conflict với ratified DEC-001–018 không? → PHẢI escalate PM, không tự override

### Escalation rule

- **Conflict với DEC-*** → comment issue `for:pm` + `spec-conflict`, KHÔNG tự resolve.
- **Tính năng ngoài MVP scope** → label `blocker:human-needed`, STOP, báo user.
- **Ambiguity về business rule** → comment DOCS_INBOX, KHÔNG assumption.

---

## Session Topology (10 sessions — Khế Day 1)

### Pair table

| # | Lead (Claude Code) | Middle Dev (Windsurf) | Scope |
|---|---|---|---|
| 1 | **KHE_Docs** | — *(single-owner)* | `docs/**` + root `*.md`. Canonical owner, fold DOCS_INBOX. Cascade BRD → SRS → Glossary → CLAUDE.md → PROJECT_PLAN. |
| 2 | **KHE_PM_Assistant** | — *(single-owner, long-lived)* | Branch `claude/pm-assistant`. Read-only mọi nơi. WRITE: GitHub issue comments + `docs/teams/pm_assistant_STATE.md` only. Cross-team triage, draft PM decisions, coordinate sessions. KHÔNG phải PM thật — draft + user ratify. |
| 3 | **KHE_Backend** | **Windsurf_Backend** | TOÀN BỘ `backend/**` — FastAPI, modules (ingest, extraction, obligation, reminders, firm_portal, auth, audit), alembic, scheduler. Multi-tenant: master.db + per-tenant pattern (reuse SpurX A-1). |
| 4 | **KHE_Frontend_Admin** | **Windsurf_Frontend** | `frontend/src/pages/{admin,firm,public}/**` — SME admin web UI + firm partner portal. |
| 5 | **KHE_PWA_Chat** | **Windsurf_PWA** | `frontend/src/pwa/**` — Chat-first SME UI (primary user experience), mobile-first PWA. |
| 6 | **KHE_QC** | **Windsurf_QC** | `backend/tests/**`, `frontend/tests/**`, Playwright e2e, fixtures, smoke automation. |
| 7 | **KHE_Designer** | — *(single-owner)* | `docs/mockup_*.jsx`. Read-only on BRD/SRS. KHÔNG sửa canonical docs — report DOCS_INBOX nếu design ảnh hưởng spec. |
| 8 | **KHE_Infra** | — *(low-touch)* | `.github/workflows/**`, deploy scripts, VPS, CI/CD, Telegram bot integration, env secrets, OCR/LLM API key rotation, monitoring. |
| 9 | **KHE_AI** (Khế-specific) | — *(single-owner Phase 1)* | `VisionExtractionProvider` interface — Gemini 2.0 Flash + Claude Haiku/Sonnet Vision. No separate OCR step. Sprint 0 benchmark on 15 PII-scrubbed samples. Accuracy target M-3 ≥90%. US-hosted Phase 1 per DEC-010. |
| 10 | **KHE_Compliance** (Khế-specific) | — *(low-touch)* | NĐ 13/2023 / NĐ 337/2025 / NĐ 70/2025 tracking, consent flows, data residency, retention policies, audit log requirements. |

### Lead/Dev workflow (BẮT BUỘC)

| Vai trò | Trách nhiệm |
|---|---|
| **Claude Code (lead)** | (1) Đọc spec + plan task → assign cho Windsurf (qua user). (2) Review Windsurf PR trước merge. (3) **Viết DOCS_INBOX report** sau merge nếu task chạm business rule / schema / API / UI / deploy / known bug. (4) Bug pattern + refactor lớn. (5) Coordinate session khác qua PM. **KHÔNG tự implement code** — exception duy nhất: hotfix khẩn cấp khi không có Windsurf available + PM đồng ý. |
| **Windsurf (dev)** | (1) Code feature/fix theo task assignment từ lead. (2) Tuân thủ scope file. (3) Đẩy branch `windsurf/...`. (4) Mở PR với lead listed reviewer. (5) **KHÔNG tự merge** — chờ lead approve. (6) **KHÔNG viết DOCS_INBOX trực tiếp** — báo lead. (7) **Local-first** dev (~70-80% fix): `npm run dev` verify local TRƯỚC khi push PR. |

### Cross-session rules

- **Trùng file giữa 2 session** → coordinate qua PM, KHÔNG tự merge.
- **Infra-only files** — `.github/workflows/**`, deploy scripts: CHỈ KHE_Infra được sửa.
- **Backend schema change** → KHE_Backend lead MUST comment DOCS_INBOX để frontend sessions biết.
- **Deploy** chỉ qua GitHub Actions CI/CD. KHÔNG SSH/SFTP trực tiếp VPS bypass quality gate. Exception: documented hotpatch playbook.
- **PR phải qua quality gate** (`pr-quality-gate.yml`): `npm run build` (frontend), `python -c "import main"` (backend), schema diff check.

### Cross-session communication

**Protocol:** GitHub Issues với labels — sessions tự đọc inbox khi spawn, không user relay thủ công.

**Quick reference:**
- Lead giao task: issue `from:<lead-team>` + `for:<dev-team>` + `task-assignment` + `status:planned`. Body PHẢI có `## Plan` (1-5 dòng).
- Lead → Lead relay: `from:X` + `for:Y` + `relay`
- Spec conflict → PM: `from:X` + `for:pm` + `spec-conflict`
- **Blocker labels:** `blocker:human-needed` (high priority) vs `blocker:waiting-dependency` (track only)
- **Status labels:** `status:planned` → `status:in-progress` → `status:review` → `status:done-staging` → close
- **Bước 0 mỗi session kickoff:** list `for:<my-team>` open issues
- **Bước 1 mỗi session:** đọc `docs/teams/<myteam>_STATE.md`
- **Post-merge:** comment **[DOCS_INBOX #1](https://github.com/kevindo1103/khe/issues/1)** issue trong 24h

### Branch Naming (BẮT BUỘC)

**Pattern (feature/fix branch):** `claude/<type>-<scope>-<short-desc>[-<random>]`

- **type:** `feat` · `fix` · `chore` · `docs` · `infra` · `hotfix` · `test` · `design` · `compliance`
- **scope:** `ingest` · `extraction` · `obligation` · `reminders` · `chat` · `firm` · `auth` · `tenant` · `ai` · `legal` · `telegram` · `infra`

**Long-lived branches:**
- `main` — production canonical
- `staging` — pre-prod test environment
- `claude/edit-git-docs-Khe01` — docs canonical lane
- `claude/pm-assistant` — KHE_PM_Assistant role

---

## Bug Fix Protocol

**Thứ tự bắt buộc — không bỏ bước:**

1. Reproduce first — xác nhận bug trên staging
2. Locate root cause — service.py → schemas.py → models.py
3. Check impact scope
4. Fix & verify locally (`npm run dev` / pytest)
5. Deploy via GitHub Actions (KHÔNG SSH trực tiếp)
6. Confirm on staging

---

## Common Bug Patterns (sẽ grow theo Sprint)

*Bingxue Cairn N=1 seeded 5 entries. Khế N=2 may add more.*

| Pattern | Triệu chứng | Fix |
|---------|-------------|-----|
| **Pydantic nested config inheritance** | 500 ValidationError on nested ORM response | Each nested schema needs own `model_config = ConfigDict(from_attributes=True)` |
| **Schema-vs-body shape drift** | 422 "Field required" on auth/post | Verify frontend body matches backend Pydantic schema |
| **React Hooks useCallback TDZ** | Page load ReferenceError | Define callbacks in dependency order |
| **SQLite same-thread deadlock** | `database is locked` 10s | Commit outer session BEFORE inner opens |
| **Cross-env data alignment** | UI shows different ID than source system | Single source of truth canonical ID across all layers |

---

## Stack

- **Backend:** FastAPI + SQLAlchemy + APScheduler, Python 3.11+, SQLite multi-tenant
- **Frontend Admin:** React + Vite + Tailwind CSS, React Router v6
- **PWA Chat:** React + Vite, mobile-first PWA
- **OCR + LLM:** Single `VisionExtractionProvider` interface — Gemini 2.0 Flash primary (~150đ/doc) + Claude Haiku fallback (~300đ/doc if accuracy <90%). Sprint 0 benchmark on 15 PII-scrubbed samples. (DEC-002)
- **Reminders:** Telegram bot (telebot / python-telegram-bot) + email fallback (DEC-006)
- **Infra:** VPS Ubuntu, systemd + nginx, GitHub Actions CI/CD

---

## Deploy

- All deploy via GitHub Actions CI/CD — KHÔNG SSH/paramiko trực tiếp
- Branch flow: feature → staging → main
- PR quality gate: build + import check + schema diff
- Alembic via deploy workflow only

---

## Local development

- `npm run dev` → backend (uvicorn 8000) + frontend (Vite 5173)
- Seed: `scripts/seed_local.py` — idempotent
- Env: `backend/.env.local` + `frontend/.env.local` (gitignored)

---

## Security Rules

- JWT `Depends(get_current_user)` BẮT BUỘC trên mọi endpoint sửa data
- Endpoints SME-side phải verify `tenant_id` match JWT
- Firm portal: verify consent (FR-FP-03)
- KHÔNG log: passwords, JWT secrets, Telegram bot tokens, OCR/LLM API keys
- SQL: chỉ ORM, không raw SQL với f-string
- **NĐ 13/2023 DLCN:** mọi PII processing phải log purpose + consent reference
- **NĐ 13/2023 Phase 1 hosting:** US-hosted LLM API acceptable với explicit consent + audit log. Phase 2+ re-evaluate self-host. (DEC-010)
- **Tenant isolation:** MUST filter by tenant_id, NEVER `SessionLocal()` directly

---

## Business Rules — D-rules

**D-01:** AI không bao giờ là system of record.
**D-02:** Mọi ghi xuống pháp lý phải qua xác nhận người.
**D-03:** Dẫn bằng ingest + retrieve + deadline. Drafting là upsell sau.
**D-04:** Tích hợp, đừng tự build. Kênh nhắc Telegram → bên thứ ba.
**D-05:** Đa loại document trong kiến trúc, sắc trong seed. Lõi general; seed F&B/bán lẻ.
**D-06:** AI extraction CHỈ ĐỌC — không sinh/sửa nội dung pháp lý.
**D-07:** Mọi field bóc ra phải cho người sửa; sửa → ghi Event.
**D-08:** Chat không trả lời được → nói "không tìm thấy", không phỏng đoán.
**D-09:** Firm KHÔNG sửa dữ liệu SME ở MVP.
**D-10:** Quyền partner xuyên-tenant chỉ mở khi SME consent rõ ràng, thu hồi được.

---

## Multi-Tenant DB Architecture (CRITICAL)

- **`master.db`:** tenants, tenant_users, firm_partners, firm_tenant_access
- **`tenants/<slug>.db`:** documents, terms, obligations, parties, events, branches, employees

**`get_tenant_session(tid)`** MUST be used. NEVER `SessionLocal()` directly.

---

## Vision Extraction Architecture (KHE_AI scope)

**Single `VisionExtractionProvider` — no separate OCR.**

```python
class VisionExtractionProvider(Protocol):
    async def extract(self, image_bytes: bytes, doc_type: str) -> ExtractionResult: ...
```

Providers: `GeminiFlashProvider` (primary) · `ClaudeHaikuProvider` (fallback) · `ClaudeSonnetProvider` (complex docs)

**NĐ 13/2023 Phase 1:** Explicit SME consent logged in `events` table before first extraction.

---

## Vision Extraction Architecture (KHE_AI scope)

**Single `VisionExtractionProvider` interface — no separate OCR step.**

```python
class VisionExtractionProvider(Protocol):
    async def extract(self, image_bytes: bytes, doc_type: str) -> ExtractionResult: ...
```

**Providers (Sprint 0 benchmark):**
- `GeminiFlashProvider` — primary, ~150đ/doc
- `ClaudeHaikuProvider` — fallback if accuracy <90%, ~300đ/doc
- `ClaudeSonnetProvider` — fallback for complex/handwritten docs

**Selection logic:** Run benchmark Sprint 0. Lock primary/fallback config before Sprint 1.

**NĐ 13/2023 Phase 1:** Documents sent to US-hosted API must have explicit SME consent logged before first extraction. Consent reference stored in `events` table.

---

## Anti-Patterns

- N+1 queries, magic numbers, god files >500 lines, `console.log` in prod
- Direct SQL f-string, `SessionLocal()` direct
- AI generating legal content (D-01/D-06 violation)
- Skipping `## Plan` before coding
- Separate OCR + LLM pipeline (use `VisionExtractionProvider` single call)

---

## Domain Glossary

| Term | Definition |
|---|---|
| Document | File gốc bất biến + Term + relationships |
| Obligation | **MVP heart.** Cam kết rời rạc, có ngày, có trạng thái. |
| VisionExtractionProvider | Single-call OCR+classify+extract (no separate OCR) |
| DOCS_INBOX | Pinned issue for docs relay — [#1](https://github.com/kevindo1103/khe/issues/1) |
| FM-XX | Failure Mode (recurring process bug) |
| INC-XX | Incident (specific bad event) |

---

## Commit Format

```
feat(ingest): add PDF upload + vision extraction queue
fix(reminders): retry on Telegram delivery 5xx
chore(infra): rotate Gemini API key
compliance(nd13): add purpose-of-processing log
```

---

*v0.1 — KHE_PM_Assistant bootstrap. KHE_Docs to fold on first DOCS_INBOX cycle.*
