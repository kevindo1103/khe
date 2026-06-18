# Khế — Claude Code Context

*Last updated: 2026-06-18 (v0.3 — fold DOCS_INBOX 13/14: DEC-018 + PRODUCT_STRATEGY adoption) — Upstream PRODUCT_STRATEGY v0.2 + MVP BRD v0.3 reference*

> **Tên mã tạm:** Khế *(placeholder per R-7 — sẽ rename khi launch)*
> Vibe Document OS cho SME Vietnam — chat-first, distributed via law firm / tax agent kênh.

---

## Project context

**References:** `docs/PRODUCT_STRATEGY_Khe_v0.2.md` (upstream — Why/Personas/JTBD/Positioning) · `docs/MVP_BRD_Khe_v0.1.md` (v0.3) · `docs/SRS_v0.1.md` · `docs/GLOSSARY_v0.1.md` (v0.2) · `docs/PROJECT_PLAN_v0.1.md` (v0.2)

**Doc cascade:** PRODUCT_STRATEGY → BRD → SRS → Glossary → PROJECT_PLAN → CLAUDE.md → Mockup. PRODUCT_STRATEGY thắng về *tại sao / cho ai / job gì*; BRD thắng về *hệ thống phải làm gì*.

**MVP scope (M0 → M3):** Ingest + retrieve + deadline. KHÔNG soạn HĐ tự động (drafting), KHÔNG review rủi ro, KHÔNG ký số (integrate sau), KHÔNG đa thị trường (VN-first), KHÔNG marketplace template.

**Vertical wedge (DEC-018 — OPEN):** KHÔNG khóa F&B/bán lẻ trước. Lõi general (multi-tenant, đa loại doc, obligation graph không phụ thuộc ngành). Chọn wedge theo **tín hiệu pilot** — tiêu chí (a) lượng HĐ tạo đau, (b) firm sẵn phục vụ, (c) HĐ có nghĩa vụ ngày-tháng để bóc. F&B/bán lẻ vẫn là ứng viên mạnh (network Mùa Vàng/Bingxue) nhưng không độc quyền. Xem `PRODUCT_STRATEGY_Khe_v0.2.md` §9.

**Distribution + Revenue (DEC-011 B2B2B):** Law firm + đại lý thuế là **khách hàng trả tiền** (Phase 1, ~50-100k VND/client/năm) **VÀ** kênh phân phối — không chỉ channel. SME end-user **FREE** Phase 1. Tầng deadline reminder ĐẺ việc cho firm thay vì cướp việc; firm bundle Khế vào gói dịch vụ tháng cho SME. Pivot ở GĐ2 (lawyer-in-loop drafting/review): SME-pays + firm rev share. **2-firm pilot (DEC-013):** 1 đại lý thuế + 1 law firm song song, 90-day evaluation. **Concierge onboarding (DEC-012):** 20 SME đầu được số hóa tận nơi — bỏ ma sát upload.

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
  **comment vào DOCS_INBOX issue** (pinned, label `docs-inbox`) theo template:
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
- **Post-merge:** comment **DOCS_INBOX** issue trong 24h

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
| **`pkg[extra]` removal drops transitive import** | `import main` fails on clean env / CI dù pass local; vd gỡ `passlib[bcrypt]` làm mất `bcrypt` mà code dùng `import bcrypt` (PR #12 case) | Declare TRỰC TIẾP mọi package mà code import — không dựa vào `[extra]` của package khác để pull transitive. |
| **`pull_request` workflow reads HEAD branch YAML, không phải base** | Fix workflow trên `main` không apply ngay cho PR `staging → main`; gate cũ vẫn chạy từ `staging` HEAD | Forward-merge fix workflow vào tất cả long-lived branches (vd `main → staging`) TRƯỚC khi mở promote PR. Tránh hotfix workflow chỉ trên main. |
| **rsync exit code 11 = target dir chưa tồn tại trên VPS** | Deploy workflow fail với `rsync error: errno 11` | Bootstrap `mkdir -p /opt/khe/backend{,-staging}` trên VPS qua SSH step TRƯỚC rsync. Đã wired in `deploy-*.yml` Sprint 0. |

---

## Stack (ratified Sprint 0)

- **Backend:** FastAPI + SQLAlchemy + APScheduler, Python 3.11+, SQLite multi-tenant (`master.db` + `tenants/<slug>.db`)
- **Auth:** `bcrypt` **direct** (KHÔNG `passlib[bcrypt]` — xem bug pattern) + `python-jose` cho JWT
- **Frontend Admin:** React + Vite + Tailwind CSS, React Router v6 *(Sprint 1+ provision)*
- **PWA Chat:** Same React + Vite stack, mobile-first PWA *(Sprint 1+ provision)*
- **Vision extraction (DEC-002):** `VisionExtractionProvider` Protocol, 1-call vision (no separate OCR). Providers: Gemini 2.5 Flash (primary, ~59đ/doc) + Claude Haiku 4.5 (fallback, ~560đ/doc) + Claude Sonnet 4.6 (complex, ~1693đ/doc)
- **Reminders (DEC-006):** Telegram bot via `python-telegram-bot` (env vars `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`) — fallback email. *(Zalo ZNS deprecated for MVP — blocker OA registration.)*
- **Infra:** VPS Ubuntu, systemd + nginx, GitHub Actions CI/CD

---

## Deploy (ratified Sprint 0)

**All deploy via GitHub Actions CI/CD — KHÔNG SSH/paramiko/SFTP trực tiếp VPS** (bypass quality gate). Exception duy nhất: documented hotpatch playbook khi prod down + Backend lead approve.

### Branch flow

`feature` → `staging` → `main`. Mỗi push đến `staging`/`main` trigger auto-deploy workflow tương ứng.

### Workflows (`.github/workflows/`)

| File | Trigger | Hành động |
|---|---|---|
| `pr-quality-gate.yml` | mọi PR | Branch name pattern check (long-lived branches exempt) + backend `python -c "import main"` + alembic single-head + frontend build |
| `deploy-staging.yml` | push `staging` | Bootstrap VPS dirs → rsync `backend/` → ghi `.env` secrets via SSH stdin (masked) → `systemctl restart khe-backend-staging` |
| `deploy-main.yml` | push `main` | Same as staging với target `khe-backend` + Telegram notify ✅/❌ |

### VPS layout

1 VPS dùng chung:
- Staging: `/opt/khe/backend-staging`, port **8001**, service `khe-backend-staging`
- Production: `/opt/khe/backend`, port **8000**, service `khe-backend`
- Systemd `EnvironmentFile=` load `.env` (secrets injected at deploy)

### Secrets (GitHub repository secrets)

`JWT_SECRET`, `GEMINI_API_KEY`, `CLAUDE_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`. Two environments: `staging` + `production`.

### Alembic

Master.db migrations via deploy workflow only (not direct VPS). Per-tenant migration loop is Sprint 1 carry-over (currently `create_all` for skeleton).

---

## Local development

**TBD — Sprint 1 sẽ ratify khi frontend session spawn.**

Pattern (mirror Bingxue):
- `npm run dev` from project root → backend (uvicorn 8000) + frontend (Vite 5173) hot-reload
- Seed script `scripts/seed_local.py` — idempotent wipe + alembic upgrade + fixtures
- Login default: admin/admin123 or staff/staff123 (local only)
- Env files: `backend/.env.local` + `frontend/.env.local`, both gitignored
- Scope: ~70-80% fix UI/logic/CRUD. Staging needed for: scheduler / vision provider / Telegram / multi-tenant integration.

---

## Security Rules

- JWT `Depends(get_current_user)` BẮT BUỘC trên mọi endpoint sửa data
- Endpoints SME-side phải verify `tenant_id` match JWT
- Firm portal endpoints phải verify consent (FR-FP-03)
- KHÔNG log: passwords, JWT secrets, Telegram bot tokens, vision provider API keys (Gemini / Claude)
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

**D-05 (P-5 — DEC-018 revised):** Đa loại document trong KIẾN TRÚC, **wedge OPEN trong SEED**. Lõi general; wedge chọn theo tín hiệu pilot, **không khóa ngành trước** (không khóa F&B/bán lẻ, không khóa lao động — xem R-1 BRD). Tiêu chí wedge: lượng HĐ + sẵn firm + nghĩa vụ ngày-tháng.

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
| DOCS_INBOX | Pinned GitHub issue for canonical docs relay | This file Docs Ownership |

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

*v0.3 — folded DOCS_INBOX 13/14 (DEC-018 Vertical OPEN + PRODUCT_STRATEGY canonical adoption). Cascade: PRODUCT_STRATEGY v0.2 → BRD v0.3 → SRS v0.1 → Glossary v0.2 → PROJECT_PLAN v0.2 → CLAUDE.md v0.3.*

*v0.2 — folded Sprint 0 DOCS_INBOX entries 1-11 (Strategy v2 / DEC-006 Telegram / Backend scaffold / Infra CI/CD / AI extraction insight). Cascade: BRD v0.2 → SRS v0.1 → Glossary v0.1 → PROJECT_PLAN v0.1 → CLAUDE.md v0.2.*
