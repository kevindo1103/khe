# Khế — Claude Code Context

*Last updated: 2026-06-09 (v0.1 — draft, awaiting docs-editor session fold) — MVP BRD v0.1 reference*

> **Tên mã tạm:** Khế *(placeholder per R-7 — sẽ rename khi launch)*
> Vibe Document OS cho SME Vietnam — chat-first, distributed via law firm / tax agent kênh.

---

## Project context

**Reference:** `docs/MVP_BRD_Khe_v0.1.md` *(current file: `MVP_BRD_Khe.md` at root — ERP_Docs to move + version on first fold)*

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
  **BRD → SRS → Glossary → PROJECT_PLAN → CLAUDE.md → Mockup**.
- Cập nhật version number + changelog entry ở mỗi file bị ảnh hưởng.
- Reply DOCS_INBOX comment với: `✅ Folded — <docs/version kết quả>`.
- Weekly Review (Monday): check `## Weekly Review Log` trong DOCS_INBOX. Run 8-item checklist.

---

## Session Topology (10 sessions: 6 lead + 4 dev pairs — Khế Day 1)

### Pair table

| # | Lead (Claude Code) | Middle Dev (Windsurf) | Scope |
|---|---|---|---|
| 1 | **ERP_Docs** | — *(single-owner)* | `docs/**` + root `*.md`. Canonical owner, fold DOCS_INBOX. Cascade BRD → SRS → Glossary → CLAUDE.md → PROJECT_PLAN. |
| 2 | **ERP_PM_Assistant** | — *(single-owner, long-lived)* | Branch `claude/pm-assistant`. Read-only mọi nơi. WRITE: GitHub issue comments + `docs/teams/pm_assistant_STATE.md` only. Cross-team triage, draft PM decisions, coordinate sessions. KHÔNG phải PM thật — draft + user ratify. |
| 3 | **ERP_Backend** | **Windsurf_Backend** | TOÀN BỘ `backend/**` — FastAPI, modules (ingest, extraction, obligation, reminders, firm_portal, auth, audit), alembic, scheduler. Multi-tenant: master.db + per-tenant pattern (reuse SpurX A-1). |
| 4 | **ERP_Frontend_Admin** | **Windsurf_Frontend** | `frontend/src/pages/{admin,firm,public}/**` — SME admin web UI + firm partner portal. |
| 5 | **ERP_PWA_Chat** | **Windsurf_PWA** | `frontend/src/pwa/**` — Chat-first SME UI (primary user experience), mobile-first PWA. |
| 6 | **ERP_QC** | **Windsurf_QC** | `backend/tests/**`, `frontend/tests/**`, Playwright e2e, fixtures, smoke automation. |
| 7 | **ERP_Designer** | — *(single-owner)* | `docs/mockup_*.jsx`. Read-only on BRD/SRS. KHÔNG sửa canonical docs — report DOCS_INBOX nếu design ảnh hưởng spec. |
| 8 | **ERP_Infra** | — *(low-touch)* | `.github/workflows/**`, deploy scripts, VPS, CI/CD, Zalo ZNS OA integration, env secrets, OCR/LLM API key rotation, monitoring. |
| 9 | **ERP_AI** (Khế-specific) | — *(single-owner Phase 1)* | OCR + LLM extraction tuning, prompt engineering, model selection per Term/Field, accuracy monitoring (M-3 ≥90%). |
| 10 | **ERP_Compliance** (Khế-specific) | — *(low-touch)* | NĐ 13/2023 / NĐ 337/2025 / NĐ 70/2025 tracking, consent flows, data residency, retention policies, audit log requirements. |

### Lead/Dev workflow (BẮT BUỘC)

| Vai trò | Trách nhiệm |
|---|---|
| **Claude Code (lead)** | (1) Đọc spec + plan task → assign cho Windsurf (qua user). (2) Review Windsurf PR trước merge. (3) **Viết DOCS_INBOX report** sau merge nếu task chạm business rule / schema / API / UI / deploy / known bug. (4) Bug pattern + refactor lớn. (5) Coordinate session khác qua PM. **KHÔNG tự implement code** — exception duy nhất: hotfix khẩn cấp khi không có Windsurf available + PM đồng ý. |
| **Windsurf (dev)** | (1) Code feature/fix theo task assignment từ lead. (2) Tuân thủ scope file. (3) Đẩy branch `windsurf/...`. (4) Mở PR với lead listed reviewer. (5) **KHÔNG tự merge** — chờ lead approve. (6) **KHÔNG viết DOCS_INBOX trực tiếp** — báo lead. (7) **Local-first** dev (~70-80% fix): `npm run dev` verify local TRƯỚC khi push PR. |

### Cross-session rules

- **Trùng file giữa 2 session** → coordinate qua PM, KHÔNG tự merge.
- **Infra-only files** — `.github/workflows/**`, deploy scripts: CHỈ ERP_Infra được sửa.
- **Backend schema change** → ERP_Backend lead MUST comment DOCS_INBOX để frontend sessions biết.
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
- **scope:** module/area — `ingest` · `extraction` · `obligation` · `reminders` · `chat` · `firm` · `auth` · `tenant` · `ai` · `legal` · `zalo` · `infra`

**Long-lived branches:**
- `main` — production canonical
- `staging` — pre-prod test environment
- `claude/edit-git-docs-Khe01` — docs canonical lane
- `claude/pm-assistant` — PM_Assistant role

**Ví dụ đúng:**
- `claude/feat-extraction-pdf-pipeline-A1b2c`
- `claude/fix-reminders-zalo-template-X9y8z`
- `windsurf/feat-backend-obligation-engine`
- `claude/compliance-nd13-consent-audit`

**Quy tắc enforcement:** Tên không match pattern → rename trước khi push lần đầu.

---

## Bug Fix Protocol

**Thứ tự bắt buộc — không bỏ bước:**

### 1. Reproduce first
- Xác nhận bug reproduce trên staging trước khi code
- Ghi rõ: endpoint nào, input nào, response thực tế vs expected

### 2. Locate root cause
- Backend bug → đọc `service.py` → `schemas.py` → `models.py` theo thứ tự
- Frontend bug → API field name? Hook placement? Missing `key` prop?
- **Không fix symptom — fix root cause**

### 3. Check impact scope
- Schema change Pydantic → kiểm tra tất cả endpoint dùng schema đó
- DB query change → kiểm tra data integrity (FK, unique constraint)
- Frontend component change → kiểm tra tất cả routes dùng component đó

### 4. Fix & verify locally
- `npm run dev` (frontend) hoặc local pytest (backend) verify
- Với seed/migration: chạy 2 lần verify idempotent

### 5. Deploy
- Merge fix vào `main` → GitHub Actions auto deploy
- **KHÔNG** SSH/paramiko/SFTP trực tiếp — bypass CI quality gate
- Exception: documented hotpatch playbook khi prod down + Backend lead approve

### 6. Confirm on staging
- Verify API response với `curl`
- Confirm không regression trên screen liên quan

---

## Common Bug Patterns (sẽ grow theo Sprint)

*Bingxue Cairn N=1 retrospective seeded 5 entries below. Khế N=2 may add more.*

| Pattern | Triệu chứng | Fix |
|---------|-------------|-----|
| **Pydantic nested config inheritance** | 500 ValidationError on response serialization for nested ORM objects | Each nested schema needs own `model_config = ConfigDict(from_attributes=True)` — không cascade từ parent |
| **Schema-vs-body shape drift** | 422 "Field required" on auth/post endpoints | Verify frontend body matches backend Pydantic schema (e.g., `tenant_slug` field required) |
| **React Hooks useCallback TDZ** | Page load ReferenceError "Cannot access X before initialization" | Define dependent callbacks BEFORE dependent ones in source order |
| **SQLite same-thread deadlock** | `database is locked` 10s sau busy_timeout | Outer session holds write lock + inner session tries to write same thread → blocked. Commit outer BEFORE inner opens session. |
| **Cross-env data alignment** | UI shows different identifier than source system (e.g., POS receipt #232, system #1) | Single source of truth — use canonical ID across all layers. Verify pre-prod smoke. |

---

## Stack

**TBD — to be ratified Sprint 0.**

Proposed (mirror SpurX reuse per BRD A-1):
- **Backend:** FastAPI + SQLAlchemy + APScheduler, Python 3.11+, SQLite multi-tenant (master.db + per-tenant)
- **Frontend Admin:** React + Vite + Tailwind CSS, React Router v6
- **PWA Chat:** Same React + Vite stack, mobile-first PWA
- **OCR + LLM:** TBD — FPT.AI / Google Document AI / GPT-4 Vision / Claude API (Sprint 0 decision)
- **Reminders:** Zalo ZNS via OA + email fallback
- **Infra:** VPS Ubuntu, systemd + nginx, GitHub Actions CI/CD

---

## Deploy

**TBD — to be defined Sprint 0.**

Pattern (mirror Bingxue):
- All deploy via GitHub Actions CI/CD — KHÔNG SSH/paramiko trực tiếp
- Branch flow: feature → staging → main (auto-deploy each)
- PR quality gate: build + import check + schema diff
- Manual via `workflow_dispatch`
- Alembic via deploy workflow only, not direct VPS

---

## Local development

**TBD — to be defined Sprint 0.**

Pattern (mirror Bingxue):
- `npm run dev` from project root → backend (uvicorn 8000) + frontend (Vite 5173) hot-reload
- Seed script `scripts/seed_local.py` — idempotent wipe + alembic upgrade + fixtures
- Login default: admin/admin123 or staff/staff123 (local only)
- Env files: `backend/.env.local` + `frontend/.env.local`, both gitignored
- Scope: ~70-80% fix UI/logic/CRUD. Staging needed for: scheduler / OCR / Zalo / multi-tenant integration.

---

## Security Rules

- JWT `Depends(get_current_user)` BẮT BUỘC trên mọi endpoint sửa data
- Endpoints SME-side phải verify `tenant_id` match JWT
- Firm portal endpoints phải verify consent (FR-FP-03)
- KHÔNG log: passwords, JWT secrets, Zalo OA tokens, OCR/LLM API keys
- SQL: chỉ ORM, không raw SQL với f-string
- **NĐ 13/2023 DLCN compliance hooks:** mọi PII processing phải log purpose + consent reference
- **Tenant isolation:** mọi query MUST filter by tenant_id, NEVER `SessionLocal()` directly

---

## Business Rules — D-rules (sẽ lock per BRD §4 + §7)

*To be expanded as features lock. Initial D-rules from BRD guardrails P-1 to P-5:*

**D-01 (P-1):** AI không bao giờ là system of record. AI chỉ đọc/bóc tách (vào) và điền template đã duyệt (ra, giai đoạn sau).

**D-02 (P-2):** Mọi ghi xuống lõi mang tính pháp lý phải qua xác nhận của người. Authoring mode bắt readback → preview → user confirm.

**D-03 (P-3):** "Ngựa thành Troy" — dẫn bằng ingest + retrieve + deadline. Drafting/review là upsell sau.

**D-04 (P-4):** Tích hợp, đừng tự build. Ký số, hóa đơn ĐT, kênh nhắc Zalo → bên thứ ba.

**D-05 (P-5):** Đa loại document trong KIẾN TRÚC, sắc trong SEED. Lõi general; seed F&B/bán lẻ.

**D-06 (FR-EX-03):** AI extraction CHỈ ĐỌC — không sinh/sửa nội dung pháp lý.

**D-07 (FR-EX-04):** Mọi field bóc ra phải cho người sửa; sửa → ghi Event.

**D-08 (FR-CQ-03):** Chat không trả lời được → nói thẳng "không tìm thấy", không phỏng đoán.

**D-09 (FR-FP-03):** Firm KHÔNG sửa dữ liệu SME ở MVP (chỉ xem + nhận tín hiệu).

**D-10 (FR-AC-03):** Quyền partner xuyên-tenant chỉ mở khi SME consent rõ ràng, thu hồi được.

*(Sẽ grow theo Sprint 1+ implementation.)*

---

## Multi-Tenant DB Architecture (CRITICAL)

**Pattern reuse từ SpurX (BRD A-1).** 2-database structure:

- **`master.db`** — global tenant registry
  - `tenants` table: tenant_id, name, plan, status, created_at
  - `tenant_users` table: tenant_id FK, username, hashed_password, role, is_active
  - `firm_partners` table: firm_id, name, contact (Khế-new vs SpurX)
  - `firm_tenant_access` table: firm_id, tenant_id, consent_status, granted_at, revoked_at (Khế-new)

- **`<tenant_slug>.db`** — per-tenant data (vd `tenants/sme-abc-restaurant.db`)
  - `documents` table — file metadata + classification
  - `terms` table — extracted fields per document
  - `obligations` table — derived deadlines + recurrence
  - `parties` table — normalized partner entities
  - `events` table — append-only ledger (reuse SpurX pattern)
  - `branches` table — physical locations (if multi-branch SME)
  - `employees` table — staff (if SME has multiple users)

**`get_tenant_session(tid)`** dependency MUST be used; NEVER `SessionLocal()` directly.

**Migration rule:** Migration scripts dùng `SessionLocal()` chỉ chạy trên master.db. Per-tenant migrations qua loop over all tenants.

---

## Anti-Patterns

- N+1 queries → dùng `joinedload` hoặc `selectinload`
- Magic numbers → đặt tên constant
- God files >500 lines → split
- `console.log` trong production code
- Direct SQL với f-string (use parameterized queries)
- `SessionLocal()` direct (use `get_tenant_session(tid)`)
- AI generating legal content (P-1 violation)
- Skipping `## Plan` 1-5 lines confirm trước khi code

---

## Domain Glossary (refs BRD §6)

| Term | Definition (1-line) | Full def |
|---|---|---|
| Document | Văn bản: file gốc bất biến + Term + relationships | BRD §6 |
| Term/Field | Giá trị có cấu trúc bóc từ Document | BRD §6 |
| **Obligation** | **MVP heart.** Cam kết rời rạc, có ngày, có trạng thái. | BRD §6 |
| Party | Đối tác trong tài liệu, chuẩn hóa | BRD §6 |
| Event (Ledger) | Append-only ghi mọi thay đổi trạng thái | BRD §6 |
| Tenant | Một SME (cô lập dữ liệu) | BRD §6 |
| Partner | Một firm; role xuyên tenant | BRD §6 |
| FM-XX | Failure Mode (recurring process bug) | This file Common Bug Patterns |
| INC-XX | Incident (specific bad event with root cause) | This file Common Bug Patterns |
| DOCS_INBOX | Pinned GitHub issue for canonical docs relay — [#1](https://github.com/kevindo1103/khe/issues/1) | This file Docs Ownership |

---

## Commit Format

```
feat(ingest): add PDF upload + OCR queue
fix(reminders): retry on Zalo ZNS 5xx
chore(infra): rotate OCR API key
docs(brd): clarify Obligation lifecycle states
compliance(nd13): add purpose-of-processing log
```

---

*v0.1 — initial draft for docs-editor session to fold. PM_Assistant proposes; ERP_Docs ratifies after first DOCS_INBOX cycle.*
