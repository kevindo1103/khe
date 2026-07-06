# SPAWN_DEV — Dev Session Entry

> Đọc sau `docs/NEW_SESSION_INSTRUCTION.md`. Dành cho branch `windsurf/<...>` hoặc `claude/<dev-role>-<...>`.
> Cairn framework component. Version: v0.7. Khế customization applied.

---

## ⚠️ Scope lock — BẮT BUỘC

Bạn **chỉ sửa file trong scope team của mình** (xem `CLAUDE.md → Session Topology → Pair table`).

- Task cần file ngoài scope → **DỪNG** → báo lead qua comment trong issue.
- Tự mở rộng scope = **FM-16** (role drift). Báo "done" với artifact không tồn tại = **FM-17**.
- Mọi claim "pushed / opened PR" phải kèm PR URL hoặc branch link (**P-10**).
- **DEC-047 PR Scope-Lock:** PR CHỈ chứa files trong lane; cross-lane = file issue, KHÔNG bundle. Trước push: `git diff --name-only origin/staging..HEAD` verify.

---

## Kickoff sequence

```
1. Xác nhận đang trên branch windsurf/<...> hoặc claude/<dev-role>-<...>  ← KHÔNG code trên claude/<lead>/ hoặc main
2. git pull origin main                        ← sync trước khi branch
3. Bước 0: list issues for:<my-team> state:open  ← đọc inbox
4. Đọc task-assignment issue được assign       ← confirm plan trước khi code
5. Comment "Confirmed plan. Branch: <x> (forked from origin/main verified). ETA: <y>."
6. Code → test local → push PR
```

---

## NGHIÊM CẤM

| Không được | Lý do |
|------------|-------|
| Merge PR của mình | Lead phải review trước |
| Push lên `claude/<lead>/`, `main`, `staging` | Scope của lead / protected |
| Tự comment DOCS_INBOX GitHub issue #1 | Lead ghi, dev báo lead biết |
| Code khi plan chưa confirmed | Plan-action decoupling → sai spec |
| Sửa file ngoài scope team | FM-16 |
| Bundle cross-lane changes vào 1 PR | DEC-047 violation — file separate issue |

---

## Multi-Tenant DB rule (BẮT BUỘC nếu backend)

- **NEVER** `SessionLocal()` cho per-tenant data — always `get_tenant_session(tid)`.
- JWT `tenant_id` PHẢI match `tenant_id` filter trên mọi query (FR-AC-01).
- `get_db()` env-gated wrapper — prod raise HTTP 500 khi thiếu tenant context, chỉ dev fallback `DEFAULT_TENANT_ID`.
- Engine cache per-tenant (SQLite WAL + `synchronous=NORMAL` anti-deadlock).
- Migration `alembic upgrade head` cho master.db; per-tenant qua `migrate_all_tenants.py` loop.

## Security rules (BẮT BUỘC nếu backend)

- JWT `Depends(get_current_user)` BẮT BUỘC trên mọi endpoint sửa data.
- Endpoints SME-side verify `tenant_id` match JWT.
- Firm portal endpoints verify consent (FR-FP-03).
- KHÔNG log: passwords, JWT secrets, Telegram bot tokens, vision provider API keys.
- SQL: chỉ ORM, KHÔNG raw SQL với f-string.

---

## Local-first rule (~70-80% fix)

Sửa code → verify local TRƯỚC khi push PR. Staging chỉ cho integration test không thể local:
- Scheduler / cron jobs (APScheduler)
- Multi-tenant / external service thật (Gemini/Claude/Telegram/DocAI)
- Environment-specific config
- Vision extraction pipeline end-to-end

---

## Trách nhiệm Dev

| Làm | Không làm |
|-----|-----------|
| Code theo plan trong task-assignment issue | Tự quyết spec khi ambiguous — hỏi lead |
| Push branch, mở PR với lead as reviewer | Tự merge, tự approve |
| Báo lead khi xong để lead ghi DOCS_INBOX GitHub issue #1 | Tự ghi DOCS_INBOX |
| Trước push: `git diff --name-only origin/staging..HEAD` (DEC-047 verify) | Assume không ai đang sửa cùng file |

---

## P-10 — khi report done

```
# Comment trong task issue:
Done. PR: https://github.com/kevindo1103/khe/pull/<n>
Branch: <windsurf/... hoặc claude/<dev-role>-...>
Tested: <how — local / staging URL>
```

---

## §0a. Partial-read discipline (BẮT BUỘC)

Doc lớn — đọc theo **section anchor** (`§4.2`, `§3.1`), KHÔNG full file trừ khi < 200 dòng.

---

*Cairn v0.7. Khế customization applied. Thay `{{PLACEHOLDER}}` khi bootstrap.*
