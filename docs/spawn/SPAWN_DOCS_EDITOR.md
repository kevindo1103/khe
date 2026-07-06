# SPAWN_DOCS_EDITOR — Docs-Editor Session Entry

> Đọc sau `docs/NEW_SESSION_INSTRUCTION.md`. Dành cho branch `claude/edit-git-docs-Khe01` (long-lived, single-owner).
> Cairn framework component. Version: v0.7. Khế customization applied.

---

## ⚠️ Scope lock — BẮT BUỘC

Bạn **chỉ sửa `docs/**` + root `*.md`**. KHÔNG sửa code, KHÔNG sửa `.github/workflows/`.

- FM-16 từng xảy ra thật: docs-editor session mở rộng scope sang backend/frontend code.
- Nếu fold task cần thay đổi code → file `task-assignment` issue cho team đúng, KHÔNG tự làm.
- Mọi commit phải kèm `git log <hash> --oneline` hoặc diff link (**P-10**).
- **Sub-ownership:** KHE_Designer sở hữu `docs/mockup_*.jsx` — docs-editor KHÔNG sửa mockups; docs-editor sở hữu canonical spec (BRD/SRS/Glossary/PROJECT_PLAN/CLAUDE.md).

---

## Kickoff sequence

```
1. Đọc CLAUDE.md                          ← topology, protocols, D-rules, Multi-Tenant DB
2. Check Weekly Review (xem §Weekly Review bên dưới)
3. Bước 0: list issues for:docs state:open   ← inbox
4. Đọc GitHub issue #1 (DOCS_INBOX Relay) — comments mới nhất chưa reply ✅ = pending fold
5. Fold theo cascade (xem §Fold workflow)
```

---

## §Weekly Review — BẮT BUỘC

Đầu mỗi session docs-editor, check xem last review > 7 ngày hoặc hôm nay là Monday.
Nếu có → chạy checklist 8 items TRƯỚC khi fold task khác:

1. Tất cả Pending comments trong GitHub issue #1 đã có plan xử lý chưa?
2. TEAM_STATE files của tất cả teams có được update gần đây không?
3. Canonical docs (BRD/SRS/Glossary) có version lag so với code đã merge không?
4. Issue kanban có issue nào stuck ở `status:in-progress` quá 5 ngày không?
5. Có `cairn-learning` issue nào chưa fold vào CAIRN_KNOWLEDGE.md không? (framework repo)
6. Có pattern lặp lại trong reports → candidate cho `Common Bug Patterns` trong CLAUDE.md?
7. Post-merge rule violation: có PR merge mà không có DOCS_INBOX comment trong 24h không?
8. Danh sách docs bị ảnh hưởng: có gì cần update mà chưa vào queue không?

Append findings vào `## Weekly Review Log` trong GitHub issue #1. Finding actionable → tạo issue.

---

## §Fold workflow (Khế cascade)

**Cascade order (BẮT BUỘC):** PRODUCT_STRATEGY → BRD → SRS → Glossary → PROJECT_PLAN → CLAUDE.md → Mockup

Reasoning: strategy (WHY/who) drives business rule (BRD) drives spec (SRS) drives terminology (Glossary) drives planning (PROJECT_PLAN) drives operational notes (CLAUDE.md). Mockup last (UI follows spec, owned by Designer).

```
1. Đọc comment trong GitHub issue #1 (Pending — chưa reply ✅)
2. Locate section cần update (partial-read — xem §anchor, không full file)
3. Fold nội dung: update canonical doc, bump version + append changelog entry
4. Commit per layer (1 commit per canonical doc bị chạm)
5. TRƯỚC push: verify author email `noreply@anthropic.com` (`git log --format='%h %ae' -3`)
6. Push
7. Reply GitHub issue #1 comment: "✅ Folded — <docs/version kết quả>"
```

---

## Trách nhiệm Docs-Editor

| Làm | Không làm |
|-----|-----------|
| Fold DOCS_INBOX comments vào canonical docs | Sửa code / `.github/workflows/` |
| Bump version + changelog mỗi file bị ảnh hưởng | Self-decide ambiguity — nêu trong reply comment |
| Reply DOCS_INBOX comment với ✅ Folded | Merge PR của session khác |
| Cascade downstream sau khi upstream change (BRD → SRS → Glossary...) | Sửa `mockup_*.jsx` (Designer scope) |
| Chạy `git diff --name-only origin/main..HEAD` verify docs-only trước push | Resolve code conflict — escalate lead |

---

## DOCS_INBOX comment template (để nhận từ các session khác qua GitHub issue #1)

```
### <YYYY-MM-DD> — <session / branch>
- PR / trigger: #<số> → <base branch>
- Đã đụng: <file / module / area>
- Thay đổi: <tóm tắt>
- Docs cần cập nhật: <BRD §x / SRS §y / Glossary / PROJECT_PLAN / CLAUDE.md / "chưa rõ">
- Ambiguity / cần PM xác nhận: <nếu có, hoặc "none">
```

---

## §0a. Partial-read discipline (BẮT BUỘC)

Doc lớn — đọc theo **section anchor** (`§4.2`, `§3.1`), KHÔNG full file trừ khi < 200 dòng.

---

*Cairn v0.7. Khế customization applied. Thay `{{PLACEHOLDER}}` khi bootstrap.*
