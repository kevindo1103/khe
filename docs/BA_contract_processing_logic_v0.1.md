# BA — Phân tích Logic Xử lý Hợp đồng
## Khế MVP · v0.3 · 2026-06-18

> **Trạng thái:** Draft — PM_Assistant · Chờ KHE_Docs fold canonical
> **Áp dụng cho:** KHE_Backend (#26), KHE_AI (#28), KHE_QC (#33), KHE_Frontend_Admin (#30)
> **Tham chiếu:** BRD §7 FR-EX / FR-OB · SRS v0.1 §schema · CLAUDE.md §D-rules
>
> **Changelog:**
> - v0.1: Amendment chain + last-writer-wins
> - v0.2: Thêm legal validity layer (Ls. NNB framework) — REVERTED, overscoped
> - v0.3: Rewrite theo CLM edge model. Cắt legal classification. Thêm reference chain (HĐ khung). Khế detect + surface, human decide.

---

## 1. Bài toán cốt lõi

Một "hợp đồng" trong thực tế SME là một **tập tài liệu liên kết**, không phải tài liệu đơn. Có 2 loại liên kết khác nhau về bản chất:

```
[Amendment chain]                    [Reference chain]
HĐ thuê MB 01/2024                  HĐ khung NCC Việt Foods 2024
    ├── Phụ lục 01 (gia hạn)            ├── Đơn hàng tháng 01/2025
    └── Phụ lục 02 (sửa PL01)           ├── Đơn hàng tháng 02/2025
                                         └── Đơn hàng tháng 03/2025
Con sửa đổi cha                     Con kế thừa cha + override một phần
```

Khế phải:
1. **Detect** quan hệ giữa các tài liệu
2. **Surface** conflict cho SME thấy
3. **Không phán** tài liệu nào "thắng" về pháp lý — đó là việc của SME/luật sư

---

## 2. Relationship types (theo CLM industry pattern)

| `relationship` | Cơ chế | Ví dụ |
|---|---|---|
| `amends` | Con sửa đổi/bổ sung cha. Điều khoản xung đột → con override cha. | Phụ lục gia hạn, sửa giá |
| `supersedes` | Con thay thế hoàn toàn cha. Cha không còn hiệu lực. | HĐ ký lại thay HĐ cũ |
| `references_framework` | Con kế thừa terms từ cha (framework), override nếu ghi rõ. | Đơn hàng tháng → HĐ khung |
| `renews` | Gia hạn kỳ tiếp theo với cùng terms. Có thể kèm thay đổi nhỏ. | HĐ thuê gia hạn năm 2 |
| `related` | Liên quan nhưng không có quan hệ pháp lý rõ | HĐ lao động + nội quy |

> **Scope MVP:** Implement `amends` + `references_framework`. Defer: `supersedes`, `renews`, `related`.

---

## 3. Mô hình dữ liệu

### 3.1 `documents` — thay đổi tối giản

```sql
-- Thêm vào per-tenant schema (tenants/<slug>.db)

-- doc_type: phân loại THỰC TẾ (không dùng để phán pháp lý)
ALTER TABLE documents ADD COLUMN doc_type TEXT DEFAULT 'unknown';
-- VALUES: 'main_contract' | 'amendment' | 'framework' | 'call_off' | 'mou' | 'unknown'
-- 'unknown' = AI chưa classify được, SME confirm

ALTER TABLE documents ADD COLUMN doc_date DATE;
-- Ngày ký / ngày hiệu lực — dùng để sort trong chain
```

### 3.2 `document_relationships` — bảng EDGE mới (quan trọng)

```sql
CREATE TABLE document_relationships (
    id              INTEGER PRIMARY KEY,
    from_doc_id     INTEGER NOT NULL REFERENCES documents(id),
    to_doc_id       INTEGER NOT NULL REFERENCES documents(id),
    -- "from_doc amends/references to_doc"
    -- ví dụ: Phụ lục 01 --[amends]--> HĐ chính

    relationship    TEXT NOT NULL,
    -- VALUES: 'amends' | 'references_framework' | 'supersedes' | 'renews' | 'related'

    seq_order       INTEGER DEFAULT 0,
    -- Thứ tự trong amendment chain (nếu relationship = 'amends')
    -- PL01=1, PL02=2 → dùng cho last-writer-wins sort

    source          TEXT DEFAULT 'ai_suggested',
    -- 'ai_suggested': AI đề xuất dựa trên nội dung
    -- 'sme_confirmed': SME đã xác nhận
    -- 'sme_manual': SME tự link thủ công

    confidence      REAL DEFAULT 0.0,
    -- Độ tin cậy của AI suggestion (0.0 - 1.0)

    tenant_id       TEXT NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

> **Tại sao edge table thay vì `parent_doc_id`?**
> Một tài liệu có thể có nhiều quan hệ. Đơn hàng tháng 3 có thể `references_framework` HĐ khung VÀ `amends` đơn hàng tháng 2 (nếu sửa điều khoản từ đơn trước). Edge table handle n-n; `parent_doc_id` chỉ handle 1-n.

### 3.3 `terms` — bổ sung fields

```sql
ALTER TABLE terms ADD COLUMN overrides_term_id INTEGER REFERENCES terms(id);
-- FK trỏ về term bị override. NULL nếu term gốc.

ALTER TABLE terms ADD COLUMN inherited_from_doc_id INTEGER REFERENCES documents(id);
-- NULL nếu term từ chính tài liệu này.
-- NOT NULL nếu term kế thừa từ framework (references_framework chain).

ALTER TABLE terms ADD COLUMN is_superseded BOOLEAN DEFAULT FALSE;
-- TRUE khi term này đã bị override bởi term mới hơn trong chain.

ALTER TABLE terms ADD COLUMN effective_from DATE;
-- Ngày term này có hiệu lực.
```

### 3.4 `obligations` — bổ sung fields

```sql
ALTER TABLE obligations ADD COLUMN source_doc_chain TEXT;
-- JSON: ["doc_id_1", "doc_id_2"] — docs đóng góp vào obligation

ALTER TABLE obligations ADD COLUMN resolution_method TEXT DEFAULT 'single_doc';
-- 'single_doc' | 'amendment_chain' | 'framework_inherit' | 'human_confirmed'
```

---

## 4. Extraction Logic

### 4.1 Những gì AI extract — chỉ facts, không phán pháp lý

**Terms chuẩn (không thay đổi):**

| Field | Loại |
|---|---|
| `ngay_ky` | DATE |
| `ngay_hieu_luc` | DATE |
| `ngay_het_han` | DATE (nullable) |
| `thoi_han_hd` | TEXT |
| `gia_tri_hd` | NUMBER |
| `ben_a`, `ben_b` | TEXT |
| `doi_tuong_hd` | TEXT |
| `dieu_khoan_phat` | TEXT |
| `gia_han_mac_dinh` | BOOL |
| `thoi_han_thong_bao` | TEXT |

**Facts bổ sung để surface cho SME (không dùng để phán):**

| Field | Mô tả | Dùng để |
|---|---|---|
| `doc_type_suggested` | AI đề xuất loại tài liệu | SME confirm → gán `doc_type` |
| `references_doc_hint` | Text hint về document được reference ("theo HĐ khung số...") | Gợi ý link relationship |
| `has_signature_both_parties` | Bool — cả 2 bên có chữ ký không | Surface cho SME, không phán pháp lý |
| `replacement_language` | Câu văn thay thế nếu có ("thay thế khoản X") | Highlight conflict trong UI |
| `contains_new_terms` | Bool — có term chưa có trong parent không | Trigger needs_review |

### 4.2 Context injection khi extract amendment/call-off

Khi extract tài liệu đã link vào chain, inject context từ parent:

```
[Prompt]
Tài liệu này là {relationship} của: {parent_doc_summary}

Terms đã biết từ parent:
{for term in parent_terms}
  - {term.field_name}: {term.field_value} (từ {parent_doc.doc_date})
{endfor}

Trích xuất:
1. "modified": term nào khác với parent? → {field_name, old_value, new_value}
2. "new": term hoàn toàn mới không có trong parent?
3. "inherited": term không đề cập → kế thừa từ parent
4. "references_doc_hint": có nhắc đến tài liệu khác không?

Output JSON. Nếu không chắc → needs_review: true.
```

---

## 5. Obligation Resolution

### 5.1 Amendment chain — Last-writer-wins

```python
def resolve_amendment_chain(tenant_id, root_doc_id):
    """
    Lấy chain theo seq_order tăng dần.
    Với mỗi field_name: document có seq_order cao nhất wins.
    """
    chain = get_amendment_chain(tenant_id, root_doc_id)
    # Bao gồm root + tất cả documents có relationship='amends' trỏ về root
    # Sort: root (seq=0) → PL01 (seq=1) → PL02 (seq=2)

    resolved = {}
    for doc in sorted(chain, key=lambda d: d.seq_order):
        for term in get_terms(tenant_id, doc.id):
            if term.field_name in resolved:
                old = resolved[term.field_name]
                mark_superseded(tenant_id, old.term_id)
                term.overrides_term_id = old.term_id
            resolved[term.field_name] = term

    return build_obligations(resolved)
```

### 5.2 Reference chain — Inherit + override

```python
def resolve_reference_chain(tenant_id, call_off_doc_id):
    """
    Call-off (HĐ cụ thể) kế thừa framework terms.
    Call-off terms override framework nếu cùng field_name.
    Framework fills gaps (fields không có trong call-off).
    """
    framework_doc_id = get_framework_doc(tenant_id, call_off_doc_id)

    # Baseline: toàn bộ terms từ framework
    resolved = {}
    for term in get_terms(tenant_id, framework_doc_id):
        term.inherited_from_doc_id = framework_doc_id
        resolved[term.field_name] = term

    # Override bằng terms từ call-off
    for term in get_terms(tenant_id, call_off_doc_id):
        if term.field_name in resolved:
            # Call-off override framework — mark framework term inherited
            resolved[term.field_name].is_superseded = True
        resolved[term.field_name] = term  # call-off wins

    return build_obligations(resolved, method='framework_inherit')
```

### 5.3 Derivation rule (FR-OB-01)

```python
def apply_derivation(terms):
    """
    Nếu ngay_het_han NULL + thoi_han_hd là số + ngay_hieu_luc có
    → derive: ngay_het_han = ngay_hieu_luc + parse(thoi_han_hd)
    Nếu thoi_han_hd = "vô thời hạn" / phi-số → needs_review = True (Q-1)
    """
```

---

## 6. `needs_review` Triggers

| Điều kiện | Review reason |
|---|---|
| `source = 'ai_suggested'` trên relationship | "Liên kết tài liệu chờ xác nhận" |
| Amendment chain có conflict | "Có điều khoản thay đổi — xem lại" |
| `has_signature_both_parties = False` | "Chưa đủ chữ ký — cần kiểm tra" |
| `contains_new_terms = True` trong amendment | "Có điều khoản mới — xem lại" |
| `ngay_het_han` derived, không explicit | "Ngày hết hạn ước tính" |
| Chain ≥ 3 documents | "Chuỗi phức tạp — nên xem toàn bộ" |
| `thoi_han_hd` phi-số | "Thời hạn cần xác nhận thủ công" |
| `doc_type = 'unknown'` | "Loại tài liệu chưa xác định" |

> **Nguyên tắc:** Khế **surface** vấn đề, SME/luật sư **quyết**. Không auto-resolve.

---

## 7. UX flow — Link tài liệu

### 7.1 AI suggest → SME confirm

```
SME upload "Phụ lục 01 - Gia hạn HĐ thuê MB 01-2024.pdf"
    ↓
AI extract: doc_type_suggested = 'amendment'
            references_doc_hint = "HĐ thuê mặt bằng số 01/2024"
    ↓
UI: "Tài liệu này có liên quan đến HĐ 01/2024 không?"
    [Có, đây là phụ lục] ← SME confirm → tạo relationship 'amends' source='sme_confirmed'
    [Không, tài liệu độc lập]
    [Tìm tài liệu khác...]
    ↓
Obligation Engine chạy resolve → obligations với needs_review nếu có conflict
```

### 7.2 SME tự link (manual)

```
SME vào document detail → "Liên kết tài liệu"
    → Chọn relationship type: [Phụ lục / sửa đổi của] [Áp dụng theo HĐ khung]
    → Search + chọn tài liệu cha
    → Confirm → tạo relationship source='sme_manual'
```

### 7.3 Contract family view

```
┌─ HĐ khung NCC Việt Foods 2024 ─────────────────────────────┐
│  Giá trị: theo từng đơn | Phat chậm: 0.05%/ngày            │
│                                                             │
│  ├─ Đơn hàng T1/2025 [references_framework] ──────────────┐ │
│  │  Giá trị: 50tr | Hết: 31/01 | ⚠ Quá hạn 12 ngày       │ │
│  │                                                         │ │
│  ├─ Đơn hàng T2/2025 [references_framework] ──────────────┐ │
│  │  Giá trị: 65tr | Hết: 28/02 | ✓ Đã thanh toán         │ │
│  │                                                         │ │
│  └─ Đơn hàng T3/2025 [references_framework] ──────────────┐ │
│     Giá trị: 72tr | Hết: 31/03 | ⏰ Còn 8 ngày           │ │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Scope theo Sprint

### Sprint 1

| Item | Owner | Issue |
|---|---|---|
| `document_relationships` table (migration) | KHE_Backend | #26 |
| `doc_type`, `doc_date` vào `documents` | KHE_Backend | #26 |
| `overrides_term_id`, `is_superseded`, `inherited_from_doc_id` vào `terms` | KHE_Backend | #26 |
| Relationship `amends` + `references_framework` resolution | KHE_Backend | #26 |
| FR-OB-01 derivation rule | KHE_Backend | #26 |
| Extraction: `doc_type_suggested`, `references_doc_hint`, `has_signature_both_parties`, `replacement_language` | KHE_AI | #28 |
| Link confirmation UI (AI suggest → SME confirm) | KHE_Frontend_Admin | #30 |
| QC: amendment chain D-07 + framework inherit | KHE_QC | #33 |

### Sprint 2

| Item | Owner |
|---|---|
| Contract family view (§7.3 tree UI) | KHE_Frontend_Admin |
| Context injection khi extract (prior terms → prompt) | KHE_AI |
| `supersedes`, `renews` relationships | KHE_Backend |

### Phase 2+

| Item | Lý do defer |
|---|---|
| Legal validity classification | Out of scope — D-01/D-02, luật sư việc |
| Auto-resolve conflict | D-01 violation |
| MOU obligation parsing | Cần corpus pilot |

---

## 9. Open Questions (cần Kevin quyết)

| ID | Câu hỏi | Impact |
|---|---|---|
| **Q-1** | `thoi_han_hd` = "vô thời hạn" — obligation `open_ended` nhắc hàng năm, hay chỉ flag? | Reminder logic |
| **Q-2** | Upload amendment trước HĐ gốc — xử lý `unknown` hay yêu cầu upload HĐ gốc trước? | Ingest UX |
| **Q-3** | Conflict UI — lịch sử từng field hay chỉ final + badge? | Sprint 2 UI scope |

---

## 10. D-rules Mapping

| D-rule | Áp dụng | Cụ thể |
|---|---|---|
| **D-01** | Obligation engine | Resolved obligation là suggestion — SME phải confirm |
| **D-02** | Human review gate | AI suggest link/conflict, SME xác nhận trước khi active |
| **D-06** | Extraction | AI chỉ đọc — KHÔNG phán điều khoản nào hợp lệ pháp lý |
| **D-07** | SME edit | Mọi edit obligation → ghi `events.field_edited` |
| **D-08** | Chat query | Chain chưa resolved → "Không tìm thấy", không guess |

---

*v0.3 — PM_Assistant · 2026-06-18 · Chờ KHE_Docs fold vào SRS §6 + BRD §7 FR-EX/FR-OB*
