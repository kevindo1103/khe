# Servanda (Khế) — Claude Code Context

*Last updated: 2026-07-06 (v0.12 — fold cycle 8: DEC-056 BA #493 + DEC-057/058/059 + CAIRN cherry-pick) — Upstream PRODUCT_STRATEGY v0.4 + MVP BRD v0.11 reference*

> **Tên thương mại:** Servanda *(DEC-055 ratified 2026-07-02, R-7 resolved — từ pacta sunt servanda)*. **Khế** giữ làm codename nội bộ.
> **Obligation OS** cho SME Vietnam (DEC-056 North Star) — nền tảng hợp nhất mọi nghĩa vụ có ngày: HĐ (nguồn 1) + tuân thủ pháp luật (nguồn 2 — rule pack curated). Chat-first, distributed via law firm / tax agent kênh (B2B2B DEC-011).

---

## Project context

**References:** `docs/PRODUCT_STRATEGY_Khe_v0.2.md` (v0.4) · `docs/MVP_BRD_Khe_v0.1.md` (v0.11) · `docs/SRS_v0.1.md` (v0.8) · `docs/GLOSSARY_v0.1.md` (v0.9) · `docs/PROJECT_PLAN_v0.1.md` (v0.8 pending) · `docs/USER_MANUAL_PILOT_v0.1.md` · `docs/mockup_design_system_v1.1.jsx` (Design System canonical) · `docs/CAIRN.md` (framework alignment) · `.cairn-version`

**Doc cascade:** PRODUCT_STRATEGY → BRD → SRS → Glossary → PROJECT_PLAN → CLAUDE.md → Mockup. PRODUCT_STRATEGY thắng về *tại sao / cho ai / job gì*; BRD thắng về *hệ thống phải làm gì*.

**MVP scope (M0 → M3):** Ingest + retrieve + deadline. KHÔNG soạn HĐ tự động (drafting), KHÔNG review rủi ro, KHÔNG ký số (integrate sau), KHÔNG đa thị trường (VN-first), KHÔNG marketplace template.

**Vertical wedge (DEC-018 — OPEN):** KHÔNG khóa F&B/bán lẻ trước. Lõi general (multi-tenant, đa loại doc, obligation graph không phụ thuộc ngành). Chọn wedge theo **tín hiệu pilot** — tiêu chí (a) lượng HĐ tạo đau, (b) firm sẵn phục vụ, (c) HĐ có nghĩa vụ ngày-tháng để bóc. F&B/bán lẻ vẫn là ứng viên mạnh (network Mùa Vàng/Bingxue) nhưng không độc quyền. Xem `PRODUCT_STRATEGY_Khe_v0.2.md` §9.

**Distribution + Revenue (DEC-011 B2B2B):** Law firm + đại lý thuế là **khách hàng trả tiền** (Phase 1, ~50-100k VND/client/năm) **VÀ** kênh phân phối — không chỉ channel. SME end-user **FREE** Phase 1. Tầng deadline reminder ĐẺ việc cho firm thay vì cướp việc; firm bundle Khế vào gói dịch vụ tháng cho SME. Pivot ở GĐ2 (lawyer-in-loop drafting/review): SME-pays + firm rev share. **2-firm pilot (DEC-013):** 1 đại lý thuế + 1 law firm song song, 90-day evaluation. **Concierge onboarding (DEC-012):** 20 SME đầu được số hóa tận nơi — bỏ ma sát upload.

**Catalysts:**
- NĐ 337/2025 (hợp đồng lao động điện tử) hiệu lực 01/01/2026
- NĐ 70/2025 (hóa đơn điện tử, kết nối thuế)
- NĐ 13/2023 (bảo vệ dữ liệu cá nhân) — compliance baseline

---

## Partial-read discipline (BẮT BUỘC)

Canonical docs lớn — đọc theo section anchor (`§4.2`, `§3.1`), KHÔNG đọc full file.
Không chắc section → đọc changelog/mục lục đầu file để locate.
Full-file read chỉ khi file < 200 dòng.

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

| # | Lead (Claude Code) | Middle Dev (Windsurf / Claude_*_Dev) | Scope |
|---|---|---|---|
| 1 | **KHE_Docs** | — *(single-owner)* | `docs/**` + root `*.md`. Canonical owner, fold DOCS_INBOX. Cascade BRD → SRS → Glossary → CLAUDE.md → PROJECT_PLAN. |
| 2 | **KHE_PM_Assistant** | — *(single-owner, long-lived)* | Branch `claude/pm-assistant`. Read-only mọi nơi. WRITE: GitHub issue comments + `docs/teams/pm_assistant_STATE.md` only. Cross-team triage, draft PM decisions, coordinate sessions. KHÔNG phải PM thật — draft + user ratify. |
| 3 | **KHE_Backend** | **Windsurf_Backend** + **Claude_Backend_Dev** | TOÀN BỘ `backend/**` — FastAPI, modules (ingest, extraction, obligation, reminders, firm_portal, auth, audit), alembic, scheduler. Multi-tenant: master.db + per-tenant pattern (reuse SpurX A-1). |
| 4 | **KHE_Frontend_Admin** | **Windsurf_Frontend** + **Claude_Frontend_Dev** | `frontend/src/pages/{admin,firm,public}/**` — SME admin web UI + firm partner portal. |
| 5 | **KHE_PWA_Chat** | **Windsurf_PWA** + **Claude_Frontend_Dev** | **`frontend/pwa/**`** — Standalone Vite project (own `package.json` + `vite.config` + service worker) — DEC-025 LOCKED. KHÔNG shared với Admin. Chat-first SME UI, mobile-first PWA. Nginx: Admin `/` + PWA `/pwa/` (Option A — FE PR #95). |
| 6 | **KHE_QC** | **Windsurf_QC** | `backend/tests/**`, `frontend/tests/**`, Playwright e2e, fixtures, smoke automation. |
| 7 | **KHE_Designer** | — *(single-owner)* | `docs/mockup_*.jsx`. Read-only on BRD/SRS. KHÔNG sửa canonical docs — report DOCS_INBOX nếu design ảnh hưởng spec. |
| 8 | **KHE_Infra** | — *(low-touch)* | `.github/workflows/**`, deploy scripts, VPS, CI/CD, Telegram bot integration (DEC-006), env secrets, OCR/LLM API key rotation, monitoring. |
| 9 | **KHE_AI** (Khế-specific) | — *(single-owner Phase 1)* | OCR + LLM extraction tuning, prompt engineering, model selection per Term/Field, accuracy monitoring (M-3 ≥90%). |
| 10 | **KHE_Compliance** (Khế-specific) | — *(low-touch)* | NĐ 13/2023 / NĐ 337/2025 / NĐ 70/2025 tracking, consent flows, data residency, retention policies, audit log requirements. |

### Lead/Dev workflow (BẮT BUỘC)

| Vai trò | Trách nhiệm |
|---|---|
| **Claude Code (lead)** | (1) Đọc spec + plan task → assign cho **dev** (Windsurf hoặc Claude_*_Dev) qua user. (2) Review dev PR trước merge. (3) **Viết DOCS_INBOX report** sau merge nếu task chạm business rule / schema / API / UI / deploy / known bug. (4) Bug pattern + refactor lớn. (5) Coordinate session khác qua PM. **KHÔNG tự implement code** — exception duy nhất: hotfix khẩn cấp khi không có dev available + PM đồng ý. |
| **Dev** (Windsurf_* / Claude_Backend_Dev / Claude_Frontend_Dev) | (1) Code feature/fix theo task assignment từ lead. (2) Tuân thủ scope file (xem §PR Scope-Lock Enforcement DEC-047). (3) Đẩy branch theo prefix: `windsurf/...` (Windsurf) hoặc `claude/<dev-role>-...` (Claude_*_Dev). (4) Mở PR với lead listed reviewer. (5) **KHÔNG tự merge** — chờ lead approve. (6) **KHÔNG viết DOCS_INBOX trực tiếp** — báo lead. (7) **Local-first** dev (~70-80% fix): `npm run dev` verify local TRƯỚC khi push PR. |

**P-10 Post-claim verification (CAIRN — cycle 8):** Trước khi claim task done ("PR merged", "file created", "test passing", "obligation persisted"): **verify claim via concrete evidence**. Not just say-so.
- Git claims → `git log --oneline` / `git show <sha>`
- File claims → `ls path/` / `cat path/file`
- PR claims → `gh pr view #N` hoặc GitHub API
- Test claims → paste actual test output, KHÔNG "test passed"
- Endpoint claims → curl output + response body

Prevents **FM-17 hallucinated artifact**. Apply mọi role — lead review dev claims, docs-editor review PM relay claims, dev review own work before marking task done.

### Cross-session rules

- **Trùng file giữa 2 session** → coordinate qua PM, KHÔNG tự merge.
- **Infra-only files** — `.github/workflows/**`, deploy scripts: CHỈ KHE_Infra được sửa.
- **Backend schema change** → KHE_Backend lead MUST comment DOCS_INBOX để frontend sessions biết.
- **Deploy** chỉ qua GitHub Actions CI/CD. KHÔNG SSH/SFTP trực tiếp VPS bypass quality gate. Exception: documented hotpatch playbook.
- **PR phải qua quality gate** (`pr-quality-gate.yml`): `npm run build` (frontend), `python -c "import main"` (backend), schema diff check.

### PR Scope-Lock Enforcement (DEC-047, post PR #288 incident)

**Hard rule:** PR CHỈ được chứa files trong scope của session mở PR. Cross-lane changes = **file issue, NEVER bundle**.

| Lane | Owner | Allowed paths | Strictly forbidden in PR |
|---|---|---|---|
| **docs** | KHE_Docs (branch `claude/edit-git-docs-Khe01`) | `docs/**` + root `*.md` | Bất kỳ code/test/workflow files |
| **infra/workflows** | KHE_Infra | `.github/workflows/**`, deploy scripts, VPS configs | Backend code, frontend code, docs |
| **mockup exception** | KHE_Designer | `docs/mockup_*.jsx` ONLY | Other docs/, code, workflows |
| **backend** | KHE_Backend | `backend/**` | Frontend, docs, workflows |
| **frontend admin** | KHE_Frontend_Admin | `frontend/src/pages/{admin,firm,public}/**` + shared `frontend/src/{types,lib,hooks,components}/**` | PWA `frontend/pwa/**`, backend, docs |
| **PWA** | KHE_PWA_Chat | `frontend/pwa/**` standalone | Admin `frontend/src/**`, backend, docs |
| **QC** | KHE_QC | `backend/tests/**`, `frontend/tests/**`, e2e | App code (`backend/app/**`, `frontend/src/**` non-test), docs |

**Trigger pattern (PR #288):** dev cherry-picks fix từ stale branch → carries co-committed files khác lane → PR scope sprawl → human review burden + revert risk. **Fix:** branch off `origin/staging` (or appropriate base) fresh; cherry-pick ONLY in-scope files; `git diff --name-only origin/staging..HEAD` verify trước push.

**CI enforcement (TODO Infra):** `pr-quality-gate.yml` add scope-lock check — block PR if changed paths violate session's allowed lanes (read from PR author / branch prefix mapping).

**Cross-lane work needed?** File issue `from:<my-team>` + `for:<other-team>` + `relay`, **không bundle**. Người khác PR riêng.

### Cross-session communication

**Protocol:** GitHub Issues với labels — sessions tự đọc inbox khi spawn, không user relay thủ công.

**Quick reference:**
- Lead giao task: issue `from:<lead-team>` + `for:<dev-team>` + `task-assignment` + `status:planned`. Body PHẢI có `## Plan` (1-5 dòng).
- Lead → Lead relay: `from:X` + `for:Y` + `relay`
- Spec conflict → PM: `from:X` + `for:pm` + `spec-conflict`
- **Blocker labels:** `blocker:human-needed` (high priority) vs `blocker:waiting-dependency` (track only)
- **Status labels:** `status:planned` → `status:in-progress` → `status:review` → `status:done-staging` → close
- **Bước 0 mỗi session kickoff (BẮT BUỘC, theo thứ tự):**
  1. **Đọc `CLAUDE.md` trước tiên** — đặc biệt §PR Scope-Lock Enforcement (DEC-047), §D-rules, §Multi-Tenant DB, §Common Bug Patterns. KHÔNG skip dù session quen.
  2. Đọc `docs/teams/<myteam>_STATE.md` — context session trước.
  3. List `for:<my-team>` open issues — inbox.
  4. **Verify branch name** — đúng `claude/<type>-<scope>-...` pattern + đúng lane (xem §Branch Naming + §PR Scope-Lock).
- **Post-merge:** comment **DOCS_INBOX** issue trong 24h nếu PR ảnh hưởng business rule / schema / API / UI / deploy / known bug.

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

### 0. Turn task into verifiable criterion (Karpathy — cycle 7)
Trước khi sửa: **biến task thành tiêu chí verify được**.
- "Fix bug" → viết test tái hiện bug trước, rồi sửa tới khi test pass.
- "Thêm validation" → viết test input không hợp lệ trước, rồi làm nó pass.
- "Refactor" → capture behavior current qua test, rồi refactor mà không đổi test.

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
| **Phantom deploy failures (0 jobs run) từ feature branch push** | GitHub Actions UI hiển thị workflow run "failed" với 0 job chạy khi push branch không match `paths`/`branches` filter | Không phải real failure — GitHub evaluates workflow YAML **từ branch HEAD** đang push, không phải workflow đang tồn tại trên `main`. Nếu branch không có YAML hoặc YAML filter loại trừ → 0 jobs. Ignore hoặc filter UI by branch. Infra PR #48. |
| **`pydantic-settings env_file` populates Settings ONLY, NOT `os.environ`** | Provider code dùng `os.environ.get("GEMINI_API_KEY")` returns None dù `.env` có key; backend boot OK, extraction silently fails với `ExtractionUnavailable` | `.env` qua `pydantic-settings` chỉ load vào `Settings` class. Provider reading `os.environ.get()` cần systemd `EnvironmentFile=` directive trên `.service` unit. `/api/health/extraction` (non-prod) diagnostic detect missing vars. Backend PR #80 (#79 root cause). |
| **Claude `messages.parse()` schema-complexity timeout** | Claude trả 400 `Schema is too complex` deterministic khi schema có `list[NestedModel]` hoặc many bounded fields | Claude grammar compiler có hard limit. Fix: tách 2-tier schema — lean flat cho Claude fallback, full nested cho Gemini primary. AI PR #103/#135. |
| **Gemini `response_schema` `too many states for serving`** | Gemini trả lỗi khi schema có nhiều `ge/le` bounded fields + many fields | Gemini grammar state-explosion. Fix: bỏ `ge/le` constraints (server-side `@field_validator` clamp instead) + gộp dict-of-fields thành `list[NamedField]` keyed. AI PR #135. |
| **SQLite `lower()` ASCII-only — `.ilike()` fail trên VN diacritics** | Chat `party_filter` với `"DANH VIỆT"` không match `"danh việt"` dù case-insensitive — SQLite built-in `lower()` không xử lý Unicode (`Ệ`/`Ố`/`Ư`...) | Register Python `str.lower()` as SQLite `lower()` via `_register_unicode_lower` listener trên tenant engines. Backend PR #138 (closes #134). |
| **PR scope sprawl từ stale branch** | PR mở từ branch tích lũy commits qua nhiều cycles → cherry-pick fix mang theo files khác lane (`docs/` trong PR backend, `.github/workflows/` trong PR frontend...). Reviewer phải nhặt từng file vs revert toàn bộ. Incident: PR #288 (4 frontend fix + co-committed docs + workflow). | (1) Branch off `origin/staging` fresh; (2) cherry-pick CHỈ in-scope files; (3) `git diff --name-only origin/staging..HEAD` verify trước push; (4) đọc §PR Scope-Lock Enforcement (DEC-047). CI scope-check sẽ block (TODO Infra). |
| **Derive delete path-2 mất audit của fulfilled obligations** | Re-derive (clause edit / re-read / re-extraction) cleanup phase DELETE obligations dù chúng đã có `fulfilled_at` set → mất audit trail của work hoàn thành. Incident: PR #311 V1 fix. | Cleanup DELETE phải có **path-2 guard** `WHERE source != 'user_manual' AND fulfilled_at IS NULL`. Bảo vệ user_manual obligations + fulfilled state khỏi AI overwrite. Codified D-15 (DEC-048). Test cover: `test_clause_provenance.py` AC-fulfilled-protected. |
| **FallbackProvider discards failed provider warnings** (cycle 7 PR #426) | `_FallbackProvider.extract()` silently discard warnings từ failed providers khi advance sang provider tiếp theo → không diagnose được sao fall through chain. | Accumulate warnings với `[provider_name]` prefix, carry forward tới final result. |
| **pdftotext garbled Vietnamese on scanned PDFs with embedded OCR** (cycle 7 PR #428) | Scanned PDFs có embedded OCR layer → pdftotext output garbled (missing diacritics, `~` artifacts). Extraction downstream broken. | Replace pdftotext với Document AI OCR cho **ALL PDFs** (both scanned and digital). Cost: digital PDFs từ 0đ → ~39đ/page (1000 pages/month free tier). |
| **Claude lean schema silent-success on PDFs** (cycle 7 PR #458) | `claude_haiku` fallback trên PDF returns 0 clauses / 0 parties (Claude `ContractExtractionLLM` không có array fields) → doc status `done` với empty extraction, không error. | Loại `claude_haiku` khỏi `_PDF_CHAIN = (hybrid_ocr, gemini_flash)`. Ảnh giữ haiku fallback OK. |
| **Silent no-op stub in extraction runner** (cycle 7 PR #431) | `extraction_runner.py:275` was empty stub — Gemini extracted `defined_terms[]` nhưng runner never persisted → Điều 1 (ĐỊNH NGHĨA) empty in UI. | Idempotent delete + persist loop from `result.defined_terms` linking `source_clause_num` / `source_clause_id`. Add integration test covers persist path end-to-end. |
| **Party.aliases NULL blocks D-13 alias-match** (cycle 7 PR #475 gap) | `_self_party_strings()` now unpacks aliases nhưng `PartyItem` LLM schema thiếu `aliases` field → aliases luôn NULL trừ khi user PATCH thủ công. Direction=NULL sai. | Fix source: thêm `aliases` vào `PartyItem` + prompt để LLM auto-populate. Interim: user PATCH `Party.aliases` manual. Filed relay cho KHE_AI. |
| **`bg-success`/green-creep for done states** (DS v1.1 cycle 7 PR #488) | 4 components dùng `bg-success`/`text-success` cho "hoàn thành" → vi phạm DS principle "hoàn thành = xám lặng". User feel over-celebrated cho routine complete. | Migrate sang tokens `done #5A6660` / `done-soft #F0F0EB` (v1.1 tokens). ConfidenceMeter ≥80%, SignatureBadge "Đã ký", LifecycleBadge "active", AmountDisplay đều convert. |
| **FM-16 Session tự mở rộng scope ngoài role** (CAIRN cherry-pick cycle 8) | Session nhận scope cụ thể (vd docs-editor `docs/**`) nhưng tự implement code backend/frontend thay vì file task-assignment issue | Hard scope-lock: chỉ sửa file trong scope. Ngoài scope → file issue `task-assignment` cho team đúng, KHÔNG tự làm. |
| **FM-17 Session báo "committed/merged" với artifact không tồn tại** (CAIRN cherry-pick cycle 8) | Claim "committed `<hash>`" hoặc "merged PR #X" nhưng hash/PR không tồn tại trong repo. Che FM-16 (scope violation + fabricated evidence). | P-10: mọi claim done phải kèm `git log <hash> --oneline` hoặc PR URL. Orchestrator verify trước khi trust. |

---

## Stack (ratified Sprint 0)

- **Backend:** FastAPI + SQLAlchemy + APScheduler, Python 3.11+, SQLite multi-tenant (`master.db` + `tenants/<slug>.db`)
- **Auth:** `bcrypt` **direct** (KHÔNG `passlib[bcrypt]` — xem bug pattern) + `python-jose` cho JWT signing. **Session: HttpOnly cookie `khe_session`** (Bearer fully retired Backend PR #46/#91). `GET /auth/me` for session check; `credentials: 'include'` on all FE fetches.
- **Frontend Admin:** React + Vite + Tailwind CSS, React Router v6 *(Sprint 1+ provision)*
- **Design System (DS v1.1 cycle 7):** `docs/mockup_design_system_v1.1.jsx` = source of truth cho tokens. **Palette:** primary `Lục Khế #1E5C49` + paper `#FBFAF7` + ink `#1C2420` + **`border-strong #7E8983`** (WCAG 2.1 3.47:1 cho input/button/checkbox) + `done #5A6660` / `done-soft #F0F0EB`. **Fonts:** Be Vietnam Pro (UI sans) + Source Serif 4 (nguyên văn HĐ serif = D-06 signal), self-host. **13 badges vocabulary** không icon/emoji. **4 components ratified:** `NavItem`, `IconButton` (icon exception), `Dropzone`, `LiveRegion`. **Elevation e0-e3.** **Voice:** "bạn" + "Servanda" không dấu chấm than. WCAG 2.1 AA measured.
- **PWA Chat:** Same React + Vite stack, mobile-first PWA *(Sprint 1+ provision)*
- **Vision extraction (DEC-002 + DEC-026/029/050):** `VisionExtractionProvider` Protocol, 1-call vision (no separate OCR). **2-tier schema** (DEC-026 + DEC-050 v3): `ContractExtractionLLM` (7 BASE fields, Claude grammar-compatible — unchanged) + `ContractExtractionLLMFull` (Gemini-only: **15 universal CANONICAL** + 30 type-specific + clauses[] với level/path + parties[] với address/representative/tax_code + payment_schedule[] + **defined_terms[] R9 + cross_references[] R10 + has_signature/signature_pages R5b**). 4 providers: Gemini 2.5 Flash (primary, ~59đ/doc) + Claude Haiku 4.5 (fallback ~560đ) + Claude Sonnet 4.6 (complex ~1693đ) + **`hybrid_ocr`** (DEC-049 KHE_AI PR #341 — 2-pass scan_detect → Document AI/pdftotext → Gemini text-mode; opt-in only). Backend dùng `get_extraction_provider()` factory (KHE_AI scope). VPS dep: `poppler-utils` cho hybrid path.
- **Chat (DEC-026):** Gemini Flash function-calling, 3 tools (`search_terms`/`search_obligations`/`search_clauses`) per BRD FR-CQ-02. D-08 hard fallback exact string at caller. PII-safe routing log (D-12).
- **Reminders (DEC-006 + DEC-025):** Telegram bot via `python-telegram-bot` (env vars `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` — dev fallback). **Per-tenant routing:** prod đọc `reminder_send` consent's `channel_target_ref` per tenant. APScheduler daily 08:00 ICT sweep (Backend PR #66). Email fallback Sprint 2. *(Zalo ZNS deprecated for MVP — blocker OA registration.)*
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
| `deploy-staging.yml` | push `staging` | Bootstrap VPS dirs → rsync `backend/` → ghi `.env` secrets via SSH stdin (masked, incl. `CORS_ORIGINS`) → `alembic upgrade head` (master.db) → `python migrate_all_tenants.py` (per-tenant loop) → HTTPS check (warn-only) → `systemctl restart khe-backend-staging` |
| `deploy-main.yml` | push `main` | Same as staging với target `khe-backend` + Telegram notify ✅/❌ |

### Domain (Infra PR #48)

- **Production:** `khe.iceflow.cloud` (DNS A → `14.225.212.116`, TLS via certbot)
- **Staging:** `staging.khe.iceflow.cloud` (DNS A → `14.225.212.116`, TLS via certbot)
- ~~`khe.vn`~~ deprecated — never provisioned.

### VPS layout

1 VPS dùng chung:
- Staging: `/opt/khe/backend-staging`, port **8001**, service `khe-backend-staging`
- Production: `/opt/khe/backend`, port **8000**, service `khe-backend`
- Systemd `EnvironmentFile=` load `.env` (secrets injected at deploy)

### Secrets (GitHub repository secrets)

`JWT_SECRET`, `GEMINI_API_KEY`, `CLAUDE_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `CORS_ORIGINS` (staging=`https://staging.khe.iceflow.cloud`, prod=`https://khe.iceflow.cloud` — ngăn browser reject credentialed requests khi `allow_credentials=True`), **`SUPERADMIN_USERS`** (cycle 6 — env-var allowlist cho `require_superadmin` admin extraction metrics endpoints PR #350, PM Option B no DB migration), **`GOOGLE_APPLICATION_CREDENTIALS`** (DEC-049 hybrid_ocr Document AI gate). Two environments: `staging` + `production`.

### Alembic

- **master.db:** `alembic upgrade head` chạy mỗi deploy.
- **Per-tenant:** `python migrate_all_tenants.py` chạy SAU `upgrade head` trên cả 2 deploy workflows (Infra PR #48). Bắt buộc để tenant_002+ schema changes (consent columns, `document_relationships`) apply trên VPS. Replaces Sprint 0 `create_all` skeleton.

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
*(DEC-031 extension: silent wrong-scope = D-08 spirit violation. Carry-over context PHẢI visible + correctable. Auto-widen on miss = không được phép.)*

**D-09 (FR-FP-03):** Firm KHÔNG sửa dữ liệu SME ở MVP (chỉ xem + nhận tín hiệu).

**D-10 (FR-AC-03):** Quyền partner xuyên-tenant chỉ mở khi SME consent rõ ràng, thu hồi được.

**D-11 (FR-TN-01):** Quota check BẮT BUỘC trước mọi `POST /ingest/*` endpoint. `docs_used_month >= doc_quota` → HTTP **429** ngay, KHÔNG proceed extraction (no LLM call). Phòng cost runaway (Gemini/Claude per-doc vision cost). Default firm-configurable per SME (override in `master.db tenants.doc_quota`). Reset calendar-month mùng 1 via APScheduler.

**D-12 (FR-CQ-05 — DEC-028):** Chat learning loop log shape PII-safe: `{tool_name, field_name_canonical, arg_keys_present, found, source_count}`. KHÔNG log raw `question`/`party_filter`/`value_contains`/`doc_hint` value. Cross-tenant few-shot prompts phải synthetic/scrubbed. **🔴 COMPLIANCE DEBT:** assume-consent bypass cho staging/pilot-dev — phải đóng explicit consent gate trước prod (KHE_Compliance tracks #119).

**D-13 (FR-OB-07 — DEC-030):** Mỗi Obligation phải có `direction`. Auto-match `tenant_profile.legal_name` ↔ `obligor`:
- Match → `nghĩa_vụ` (SME phải làm)
- No-match nhưng obligor present → `quyền_lợi` (đối tác cần làm cho SME)
- legal_name NULL hoặc obligor NULL → `direction=NULL` + `needs_review=true` (D-02 user confirm via UI). KHÔNG default sang `nghĩa_vụ`.

**D-14 (FR-OB-09 — DEC-048 Fulfillment capture):** Fulfillment status `done` PHẢI ghi `fulfilled_at` + `fulfilled_by`. KHÔNG cho phép `status=done` mà `fulfilled_at IS NULL`. `evidence_doc_ids` tùy chọn (nếu provide → docs phải `is_evidence=true`). Event `obligation_fulfilled` log với `purpose=obligation_fulfillment` (KHE_Compliance §A.1 closed-set, no consent gate). Revert flow ghi `obligation_fulfillment_reverted`.

**D-15 (FR-OB-10 — DEC-048 Cascade chain anchor):** Khi parent obligation `done` → cascade child obligations PHẢI dùng `parent.fulfilled_at` làm anchor (G1 fix), **KHÔNG** dùng `date.today()`. Backfill case (child_due < today) → child status = **`awaiting_confirmation`** (D-02 SME confirm), KHÔNG auto-flip `overdue` hoặc trigger reminder. P1 source-aware merge: re-derive cleanup phase MUST có guard `WHERE source != 'user_manual' AND fulfilled_at IS NULL` (PR #311).

**D-16 (DEC-055 — No paywall on safety):** Không bao giờ paywall các tool an toàn (reminder, D-02 confirm, D-07 edit, audit, consent). Chỉ monetize **trí tuệ** (extraction, chat) và **tiện lợi** (bulk operations, portfolio view). Servanda phải cứu SME khỏi trượt hạn kể cả khi họ không trả tiền. Ledger tier free vĩnh viễn cho core safety loop; AI tier paid với quota per-document. *Renumbered từ PM-proposed D-11 do conflict với existing D-11 quota check.*

**D-17 (DEC-056 — Firm confirms compliance obligations):** Servanda cung cấp template rule pack + engine nhắc nghĩa vụ tuân thủ (thuế/BHXH/ngành dọc). **Firm (đại lý thuế/law firm) là người kích hoạt và xác nhận** lịch tuân thủ cho SME client (D-02 áp nguyên). Servanda **KHÔNG bao giờ** tự tư vấn nghĩa vụ pháp lý (đụng D-01/D-08). **KHÔNG dùng AI đọc văn bản luật** để sinh nghĩa vụ. Rule pack sai → firm bắt được ở bước xác nhận = lá chắn trách nhiệm. *Renumbered từ PM-proposed D-12 do conflict với existing D-12 chat learning.*

*(Sẽ grow theo Sprint 2+ implementation.)*

---

## Multi-Tenant DB Architecture (CRITICAL)

**Pattern reuse từ SpurX (BRD A-1).** 2-database structure:

- **`master.db`** — global tenant registry
  - `tenants` table: tenant_id, name, plan, status, created_at, **doc_quota** (nullable, firm-configurable per SME — FR-TN-01), **docs_used_month**, **quota_reset_at** (calendar mùng 1 reset)
  - `tenant_users` table: tenant_id FK, username, hashed_password, role, is_active
  - `firm_partners` table: firm_id, name, contact (Khế-new vs SpurX)
  - `firm_tenant_access` table: firm_id, tenant_id, consent_status, granted_at, revoked_at (Khế-new)
  - **`tenant_profile`** table (DEC-030, Kevin cycle 4 q2): 1:1 với `tenants`. Stores `legal_name` (SME entity name — auto-match Obligation `obligor` cho direction derivation) + `legal_name_aliases` + future profile fields. **Separate model** (NOT column embed in `tenants` — keeps registry minimal). **Cycle 8 extension (`master_005` BA #493 §4):** +`legal_form`, +`has_employees` BOOL, +`vat_period` (`month`/`quarter`), +`fiscal_year_start` DATE. Drives rule pack `applies_when` matching (DEC-056 compliance obligations).

- **`<tenant_slug>.db`** — per-tenant data (vd `tenants/sme-abc-restaurant.db`)
  - `documents` table — file metadata + `doc_type` (legacy enum 4) + `doc_type_group` (DEC-029 enum 11)
  - `terms` table — extracted fields (12 universal + ~30 type-specific via NamedExtractedField — DEC-029)
  - `obligations` table — derived deadlines. **Schema rewrite #122 Option B (DEC-027/030):** `obligation_type` = category (enum **9** per cycle 7 PR #475 `tenant_030`: `payment`/`delivery`/`handover`/`expiration`/`renewal`/`review`/`warranty`/**`penalty`**/`other`); `recurrence` = cadence; `direction` + `obligor`; `source_doc_chain` + `resolution_method`. **DEC-048 expansion (cycle 5, `tenant_017`):** +`fulfilled_at` (cascade anchor G1) +`fulfilled_by` +`evidence_doc_ids` JSON +`source_clause_num` (Kevin Option B 0a) +`derived_from` (`original`/`user_edit`/`ai_re_derived`) +`source` (`ai_extracted`/`user_manual`/`ai_re_derived` — P1 merge protected). Status enum extended: `pending` · `done` · `cancelled` · `awaiting_confirmation` (cascade-past D-02) · `waiting_trigger` (FR-OB-13).
  - `clauses` table (DEC-026, migration `tenant_003`) — text nguyên gốc Document; Gemini-only populated. **DEC-048 §13 expansion (`tenant_018`):** +`original_content`/`edited_by_user`/`edited_at`. **DEC-050 R3 hierarchy (`tenant_023`):** +`parent_id` self-FK +`level` +`clause_path` (regex-synthesized post-extraction).
  - `documents` table — +`is_evidence` BOOL DEC-048. **DEC-050 cluster:** +`title`/`contract_number` (`tenant_021`) · +`signing_date`/`commencement_date` (`tenant_025`) · +`contract_duration`/`lifecycle_status` (`tenant_026`) · +`has_signature`/`signature_pages` (`tenant_028`). **Cycle 6 admin/polling:** +`extraction_model`/`extraction_latency_ms`/`extraction_warnings` (`tenant_019`) · +`processing_stage`/`processing_progress` (`tenant_020`). **Cycle 7 (`tenant_029` content_status + `tenant_031`):** `processing_stage` enum extended (+`retry_needed` PR #458, +`two_pass_skeleton`/`two_pass_fill` PR #463) · +`may_have_unextracted_obligations` BOOL NULLABLE (three-state D-03 completeness, PR #492). **Cycle 8 (`tenant_032`):** +`type` enum (`normal`/`manual`/`rule_pack`=Virtual Document DEC-057).
  - **NEW `rule_activations` table (cycle 8, `tenant_032` BA #493 §6):** `id`, `tenant_id`, `rule_pack_id`, `rule_pack_version`, `status` (`active`/`declined`/`paused`), `activated_at`, `activated_by`, `obligation_ids` JSON, `virtual_document_id` FK. Unique `(tenant_id, rule_pack_id)`. Tracks user decline decision → block re-suggest (FR-OB-23).
  - `parties` table (DEC-030) — +`role_label` extracted verbatim. **DEC-050 R2 (`tenant_022`):** +`address`/`representative`/`tax_code`/`is_self` BOOL/`aliases` JSON.
  - `document_relationships` table — `relationship_type` enum **3-value** (DEC-050 R4 `tenant_024`): `amends` / `references_framework` / **`annex`** (excluded from `resolve_chain`).
  - `definitions` table (DEC-050 R9 NEW, `tenant_026`/`tenant_027`) — glossary entries từ "Định nghĩa" section. CRUD endpoints + D-07 `original_term` snapshot.
  - Cross-refs (DEC-050 R10 PR #392) — VN legal ref detection service `cross_ref.py`. Exact storage shape (JSON on clauses or dedicated table) verify per PR diff.
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
- **(Karpathy — cycle 7) Delete-only-what-your-change-makes-dead:** khi sửa code chỉ xóa import/biến/hàm mà **chính thay đổi của mình** làm thừa. Dead code có sẵn từ trước — nêu ra trong PR description, KHÔNG tự xóa trừ khi được yêu cầu explicit.
- **(DS v1.1 — cycle 7) Icon/emoji rời trong JSX:** KHÔNG dùng icon rời ngoài `IconButton` component (ngoại lệ duy nhất). Badge chỉ dùng text + color per 13-badge vocabulary.
- **(DS v1.1 — cycle 7) Màu ngoài token:** KHÔNG dùng hex/rgb hard-code trong component. Chỉ dùng token từ `mockup_design_system_v1.1.jsx`. Viền `n-300`/`n-400` KHÔNG được dùng cho input/button/checkbox (dùng `border-strong` cho WCAG 3:1) — tránh lặp lại contrast gap đã fix v1.1.
- Trust "done" chưa verify artifact (FM-17 risk) — verify hash/PR URL trước
- Session tự mở scope ngoài role (FM-16) — file issue cho team đúng, không tự làm
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

*v0.12 — Cycle 8 fold (DEC-056 BA #493 6 sub-decisions + DEC-057 Virtual Document + DEC-058 Home 3-CTA + DEC-059 compliance wizard + CAIRN cherry-pick 5 items). §Common Bug Patterns +FM-16 role drift + FM-17 hallucinated artifact. §Anti-Patterns +Trust-done + Scope-drift. §Lead/Dev workflow +P-10 post-claim verification. NEW §Partial-Read Discipline. §Multi-Tenant DB `documents.type` enum (`normal`/`manual`/`rule_pack`) + NEW `rule_activations` per-tenant table + `tenant_profile` compliance-profile extension (`legal_form`/`has_employees`/`vat_period`/`fiscal_year_start` — `master_005`). References +docs/CAIRN.md + .cairn-version. Cascade: PRODUCT_STRATEGY v0.4 → BRD v0.11 → SRS v0.8 → Glossary v0.9 → PROJECT_PLAN v0.8 → CLAUDE.md v0.12.*

*v0.11 — Cycle 7 fold (DEC-055 Servanda tier + DEC-056 Obligation OS + Design System v1.1 + ~15 impl entries). Header rename Khế → Servanda (R-7 resolved DEC-055). +D-16 no-paywall-safety (renumbered from PM D-11 collision). +D-17 firm-confirms-compliance (renumbered from PM D-12 collision). §Multi-Tenant DB obligations `obligation_type` +`penalty` (tenant_030). documents +`may_have_unextracted_obligations` (tenant_031) + processing_stage enum +retry_needed/two_pass_skeleton/two_pass_fill (tenant_029). §Stack DS v1.1 tokens (Lục Khế + border-strong + done + Be Vietnam Pro + Source Serif 4 + 13 badges + 4 components + elevation). §Anti-Patterns +3 (icon/emoji rời, màu ngoài token, Karpathy delete-only-your-dead). §Bug Fix Protocol +Step 0 Karpathy verifiable criterion. §Common Bug Patterns +6 (FallbackProvider warnings, pdftotext garbled, Claude lean silent-success, no-op stub, Party.aliases blocks alias-match, green-creep). Cascade: PRODUCT_STRATEGY v0.4 → BRD v0.10 → SRS v0.7 → Glossary v0.8 → PROJECT_PLAN v0.7 → CLAUDE.md v0.11.*

*v0.10 — Cycle 6 fold (DEC-049 hybrid OCR + DEC-050 R1-R10 EPIC #362 production PR #402 sha pending). §Multi-Tenant DB cluster update: documents +10 cols (title/contract_number tenant_021, signing_date/commencement_date tenant_025, contract_duration/lifecycle_status tenant_026, has_signature/signature_pages tenant_028, extraction metrics tenant_019, processing progress tenant_020). parties +5 cols (R2 tenant_022). clauses hierarchy +3 cols (R3 tenant_023). document_relationships enum +annex (R4 tenant_024). NEW definitions table (R9 tenant_027). Cross-refs service (R10 PR #392). §Stack vision extraction: schema v3 (15 canonical + R9 defined_terms + R10 cross_references + R5b signature flags). 4th provider `hybrid_ocr` (DEC-049 opt-in). §Deploy secrets +SUPERADMIN_USERS (admin metrics gate) + GOOGLE_APPLICATION_CREDENTIALS (hybrid_ocr Document AI). Cascade: PRODUCT_STRATEGY v0.3 → BRD v0.9 → SRS v0.6 → Glossary v0.7 → PROJECT_PLAN v0.6 → CLAUDE.md v0.10.*

*v0.9 — Cycle 5 fold (DEC-048 EPIC #300 production promote `ce48bbd`). +D-14 fulfillment capture (fulfilled_at + fulfilled_by mandatory, evidence_doc_ids link to is_evidence docs, purpose=obligation_fulfillment no consent gate). +D-15 cascade chain anchor (fulfilled_at G1 fix NOT date.today(), backfill → awaiting_confirmation D-02, P1 source-aware merge guard). §Multi-Tenant DB obligations expansion (+6 cols incl. fulfilled_at/by/evidence/source_clause_num/derived_from/source; status enum +awaiting_confirmation +waiting_trigger; migration tenant_017). +clauses tenant_018 edit cols (original_content immutable + edited_by_user + edited_at). +documents is_evidence. +Bug pattern "Derive delete path-2 mất audit fulfilled obligations" (PR #311). References block bumped: BRD v0.8, SRS v0.5, Glossary v0.6, PROJECT_PLAN v0.5 (pending), +USER_MANUAL_PILOT_v0.1.md. Cascade: PRODUCT_STRATEGY v0.3 → BRD v0.8 → SRS v0.5 → Glossary v0.6 → PROJECT_PLAN v0.5 → CLAUDE.md v0.9.*

*v0.8 — Topology cleanup + Claude_*_Dev roles. (1) ERP_*→KHE_* rename rows 1-10 + §Cross-session rules (Infra-only files, Backend schema change). (2) Topology header "Middle Dev (Windsurf)" → "Middle Dev (Windsurf / Claude_*_Dev)". (3) Rows 3/4/5 dev column adds Claude_Backend_Dev (#3) + Claude_Frontend_Dev (#4 + #5). Row 6 QC unchanged. (4) §Lead/Dev workflow row "Windsurf" → "Dev" generic, lists all dev types, branch prefix `windsurf/...` or `claude/<dev-role>-...`. (5) Row 8 KHE_Infra: stale "Zalo ZNS OA" → "Telegram bot (DEC-006)". Operational note — không change cascade upstream docs.*

*v0.7 — DEC-047 PR Scope-Lock Enforcement section (full lane table + trigger pattern + CI TODO + cross-lane workflow). §Cross-session communication Bước 0 kickoff checklist BẮT BUỘC (CLAUDE.md trước tiên → STATE.md → inbox → verify branch). §Common Bug Patterns +1: "PR scope sprawl từ stale branch" (PR #288 incident). Operational notes — không change cascade upstream docs.*

*v0.6 — folded DEC-031 v2 (Result-seeded Progressive State chat architecture). D-08 extension note: silent wrong-scope = spirit violation; carry-over context PHẢI visible + correctable; auto-widen on miss cấm. Discard DEC-031 v1 spec (`1f6c5ad`) — v2 (`dc307eb`) canonical. Cascade: PRODUCT_STRATEGY v0.3 → BRD v0.7 → CLAUDE.md v0.6.*

*v0.5 — folded DOCS_INBOX 23-52 (cycle 4 — Sprint 1 staging-complete + DEC-027/028/029/030 mega-batch). +D-12 chat learning compliance debt, +D-13 direction derivation. +3 bug patterns (pydantic-settings env_file, Claude grammar schema-complex, Gemini ge/le too-many-states). Obligations schema rewrite per #122 Option B (`obligation_type` = category 8, `recurrence` renamed, status enum corrected). tenant_profile separate model (Kevin q2 ratify). DEC-025 PWA standalone Vite scope. Cascade: PRODUCT_STRATEGY v0.2 → BRD v0.6 → SRS v0.4 → Glossary v0.5 → PROJECT_PLAN v0.4 → CLAUDE.md v0.5.*

*v0.4 — folded DOCS_INBOX 15-22 (cycle 3 — Backend M0 contract + ingest/relationships endpoints + extraction module factory + quota guard + Infra domain + PM billing roadmap). Cascade: PRODUCT_STRATEGY v0.2 → BRD v0.4 → SRS v0.2 → Glossary v0.3 → PROJECT_PLAN v0.3 → CLAUDE.md v0.4.*

*v0.3 — folded DOCS_INBOX 13/14 (DEC-018 Vertical OPEN + PRODUCT_STRATEGY canonical adoption). Cascade: PRODUCT_STRATEGY v0.2 → BRD v0.3 → SRS v0.1 → Glossary v0.2 → PROJECT_PLAN v0.2 → CLAUDE.md v0.3.*

*v0.2 — folded Sprint 0 DOCS_INBOX entries 1-11 (Strategy v2 / DEC-006 Telegram / Backend scaffold / Infra CI/CD / AI extraction insight). Cascade: BRD v0.2 → SRS v0.1 → Glossary v0.1 → PROJECT_PLAN v0.1 → CLAUDE.md v0.2.*
