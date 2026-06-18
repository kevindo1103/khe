# BA — Phân tích Logic Xử lý Hợp đồng
## Khế MVP · v0.1 · 2026-06-18

> **Trạng thái:** Draft — PM_Assistant · Chờ KHE_Docs fold canonical
> **Áp dụng cho:** KHE_Backend (#26), KHE_AI (#28), KHE_QC (#33), KHE_Frontend_Admin (#30)
> **Tham chiếu:** BRD §7 FR-EX / FR-OB · SRS v0.1 §schema · CLAUDE.md §D-rules

---

## 1. Bối cảnh và vấn đề

Một "hợp đồng" trong thực tế SME không phải là một tài liệu đơn — mà là một **chuỗi tài liệu pháp lý có quan hệ cha-con**:

```
Hợp đồng thuê mặt bằng số 01/2024 (HĐ chính)
    ├── Phụ lục 01 — Gia hạn thêm 12 tháng (ký 01/06/2024)
    │       └── Phụ lục 02 — Sửa PL01, chỉ gia hạn 6 tháng (ký 01/09/2025)
    └── Phụ lục 03 — Điều chỉnh giá thuê (ký 01/01/2025)
```

**Điều 403 BLDS 2015** quy định:
- Phụ lục có hiệu lực như hợp đồng
- Phụ lục trái nội dung HĐ → vô hiệu, **trừ khi** hai bên chấp nhận → coi HĐ chính đã được sửa đổi

Khế phải xác định được: **"Nghĩa vụ (obligation) hiệu lực tại thời điểm T là gì?"** — từ chuỗi tài liệu, không phải từng tài liệu riêng lẻ.

---

## 2. Phân loại tài liệu (Document Taxonomy)

| `doc_type` | Mô tả | Ví dụ | Quan hệ |
|---|---|---|---|
| `main_contract` | Hợp đồng gốc | HĐ thuê MB số 01/2024 | Gốc của chuỗi |
| `annex` | Phụ lục — quy định chi tiết | Phụ lục 01 — danh sách thiết bị | Con của `main_contract` hoặc `annex` |
| `amendment` | Phụ lục sửa đổi — thay đổi điều khoản | Phụ lục 02 — điều chỉnh thời hạn PL01 | Con của `annex` hoặc `main_contract` |
| `appendix` | Tài liệu đính kèm tham chiếu (bản đồ, bản vẽ) | Sơ đồ mặt bằng | Con, không tạo obligation |
| `standalone` | Văn bản độc lập không thuộc chuỗi | Biên bản bàn giao | Không có parent |

> **Lưu ý:** `annex` và `amendment` phân biệt theo nội dung — `annex` bổ sung chi tiết, `amendment` thay đổi giá trị đã có. Extraction model phân loại, SME confirm nếu `needs_review`.

---

## 3. Mô hình dữ liệu (Schema additions — Sprint 1)

### 3.1 Bảng `documents` — bổ sung fields

```sql
-- Thêm vào per-tenant schema (tenants/<slug>.db)
ALTER TABLE documents ADD COLUMN doc_type TEXT DEFAULT 'standalone';
    -- VALUES: 'main_contract' | 'annex' | 'amendment' | 'appendix' | 'standalone'

ALTER TABLE documents ADD COLUMN parent_doc_id INTEGER REFERENCES documents(id);
    -- NULL nếu là HĐ chính hoặc standalone

ALTER TABLE documents ADD COLUMN seq_order INTEGER DEFAULT 0;
    -- Thứ tự trong chuỗi: HĐ chính = 0, PL01 = 1, PL02 = 2...
    -- Dùng để sort chain khi resolve obligation

ALTER TABLE documents ADD COLUMN doc_date DATE;
    -- Ngày ký / ngày hiệu lực tài liệu — fallback sort nếu seq_order không có
```

### 3.2 Bảng `terms` — bổ sung fields

```sql
ALTER TABLE terms ADD COLUMN overrides_term_id INTEGER REFERENCES terms(id);
    -- FK trỏ về term bị override bởi term này
    -- NULL nếu term gốc; NOT NULL nếu là override từ annex/amendment

ALTER TABLE terms ADD COLUMN effective_from DATE;
    -- Ngày term này có hiệu lực (thường = doc_date của document chứa nó)

ALTER TABLE terms ADD COLUMN is_superseded BOOLEAN DEFAULT FALSE;
    -- TRUE khi term này đã bị override bởi một term mới hơn trong chain
    -- Cập nhật bởi Obligation Engine sau khi resolve
```

### 3.3 Bảng `obligations` — bổ sung fields

```sql
ALTER TABLE obligations ADD COLUMN source_doc_chain TEXT;
    -- JSON array: ["doc_id_1", "doc_id_2"] — danh sách documents đóng góp vào obligation này
    -- Dùng cho audit + UI hiển thị "Nghĩa vụ này từ HĐ + PL01 + PL02"

ALTER TABLE obligations ADD COLUMN resolution_method TEXT DEFAULT 'single_doc';
    -- 'single_doc': chỉ từ 1 tài liệu
    -- 'chain_resolved': từ chuỗi, đã resolve xung đột
    -- 'human_confirmed': SME đã xác nhận kết quả resolve
    -- 'needs_review': flagged, chờ SME
```

---

## 4. Luồng xử lý (Processing Flow)

### 4.1 Ingest Phase

```
SME upload tài liệu
    ↓
[Bước 1] Classify document
    - VisionExtractionProvider nhận diện doc_type từ header/title
    - Tìm parent: "Phụ lục X của HĐ số Y" → match parent_doc_id
    - Gán seq_order = max(seq_order trong cùng chain) + 1
    - Nếu không tìm được parent → doc_type = 'standalone', cảnh báo SME
    ↓
[Bước 2] Check consent (NĐ 13/2023)
    - Nếu chưa consent → 403, STOP
    ↓
[Bước 3] Extract terms
    - Xem §5 chi tiết
    ↓
[Bước 4] Obligation resolution
    - Xem §6 chi tiết
    ↓
[Bước 5] Notify + queue review nếu needs_review
```

### 4.2 Upload UI flow cho SME

```
SME upload file
    ↓
Hệ thống hỏi: "Đây là tài liệu gì?"
    ├── Hợp đồng chính mới → tạo chain mới
    ├── Phụ lục / Sửa đổi của hợp đồng nào? → search + link parent
    └── Tài liệu độc lập → standalone
    ↓
SME confirm hoặc để hệ thống tự phân loại (auto-classify)
```

---

## 5. Extraction Logic — Context-Aware

### 5.1 Nguyên tắc

- **Tài liệu đầu tiên trong chain (HĐ chính):** Extract toàn bộ terms chuẩn.
- **Tài liệu tiếp theo (annex/amendment):** Extract với **context injection** — cung cấp các terms đã biết từ chain cho model, yêu cầu model chỉ ra: **(a) điều khoản nào thay đổi, (b) giá trị mới, (c) điều khoản nào giữ nguyên.**

### 5.2 Prompt template cho annex/amendment

```
[System]
Bạn đang phân tích tài liệu pháp lý Việt Nam. Trích xuất ĐÚNG giá trị
có trong tài liệu — KHÔNG sinh nội dung, KHÔNG suy diễn. (D-06)

[Context từ chain hiện tại]
Tài liệu: {doc_type} số {doc_ref} của hợp đồng {parent_ref}
Chuỗi tài liệu đã xử lý:
{for each prior_doc in chain}
  - {prior_doc.doc_type} ({prior_doc.doc_date}): {prior_doc.terms_summary}
{endfor}

[Task]
Từ tài liệu đính kèm, trích xuất:
1. "modified": điều khoản nào bị thay đổi so với tài liệu trước?
   → Trả về: [{ field_name, old_value, new_value, source_clause }]
2. "unchanged": điều khoản nào được xác nhận giữ nguyên?
   → Trả về: [{ field_name, confirmed_value }]
3. "new": điều khoản mới chưa có trong chain?
   → Trả về: [{ field_name, value, source_clause }]
4. "doc_type_confirm": xác nhận loại tài liệu này (annex/amendment/appendix)

Output JSON only. Nếu không chắc → đặt needs_review: true.
```

### 5.3 Fields chuẩn cần extract

| Field name | Loại | Ghi chú |
|---|---|---|
| `ngay_ky` | DATE | Ngày ký văn bản |
| `ngay_hieu_luc` | DATE | Ngày bắt đầu có hiệu lực |
| `ngay_het_han` | DATE | Ngày kết thúc (có thể NULL — derive từ thời_hạn) |
| `thoi_han_hd` | TEXT | "24 tháng", "vô thời hạn", "đến khi thanh lý" |
| `gia_tri_hd` | NUMBER | Giá trị hợp đồng (VND) |
| `don_vi_tien_te` | TEXT | VND mặc định |
| `ben_a` | TEXT | Tên bên A |
| `ben_b` | TEXT | Tên bên B |
| `doi_tuong_hd` | TEXT | Đối tượng hợp đồng (mặt bằng, dịch vụ...) |
| `dieu_khoan_phat` | TEXT | Điều khoản phạt vi phạm |
| `gia_han_mac_dinh` | BOOL | Tự động gia hạn nếu không thông báo trước? |
| `thoi_han_thong_bao` | TEXT | Thời hạn thông báo khi không gia hạn |

---

## 6. Obligation Resolution Algorithm

### 6.1 Nguyên tắc: Last Writer Wins (per field_name)

```python
def resolve_obligations(tenant_id: str, root_doc_id: int) -> list[Obligation]:
    """
    Với mỗi field_name, lấy giá trị từ document có seq_order CAO NHẤT
    trong chain — document mới nhất override document cũ.
    """
    chain = get_document_chain(tenant_id, root_doc_id)
    # chain đã sort: [HĐ chính (seq=0), PL01 (seq=1), PL02 (seq=2)...]

    resolved_terms: dict[str, Term] = {}
    conflict_log: list[ConflictEntry] = []

    for doc in chain:  # iterate theo thứ tự seq_order tăng dần
        for term in get_terms(tenant_id, doc.id):
            if term.field_name in resolved_terms:
                old = resolved_terms[term.field_name]
                conflict_log.append(ConflictEntry(
                    field_name=term.field_name,
                    old_value=old.field_value,
                    old_doc=old.doc_id,
                    new_value=term.field_value,
                    new_doc=term.doc_id,
                ))
                # Mark old term as superseded
                mark_superseded(tenant_id, old.id)
                term.overrides_term_id = old.id
            resolved_terms[term.field_name] = term

    # Derive ngay_het_han nếu thiếu (FR-OB-01)
    resolved_terms = apply_derivation_rules(resolved_terms)

    # Tạo obligations từ resolved_terms
    obligations = build_obligations(tenant_id, resolved_terms, chain)

    # Flag nếu có conflict hoặc chain phức tạp
    if len(conflict_log) > 0 or len(chain) > 2:
        for ob in obligations:
            ob.needs_review = True
            ob.resolution_method = 'chain_resolved'

    return obligations
```

### 6.2 Derivation rules (FR-OB-01)

```python
def apply_derivation_rules(terms: dict) -> dict:
    """
    Rule 1: Nếu ngay_het_han NULL + thoi_han_hd là số + ngay_hieu_luc có
    → derive: ngay_het_han = ngay_hieu_luc + parse(thoi_han_hd)
    
    Rule 2: thoi_han_hd = "vô thời hạn" hoặc "không xác định"
    → ngay_het_han = NULL, tạo obligation type = 'open_ended', needs_review = True
    
    Rule 3: gia_han_mac_dinh = True + thoi_han_thong_bao có
    → tạo thêm obligation type = 'renewal_notice' với due_date = ngay_het_han - thoi_han_thong_bao
    """
    ...
```

### 6.3 Ví dụ cụ thể — Case Kevin nêu

```
Input chain:
  doc_0 (HĐ chính, seq=0): thoi_han_hd="24 tháng", ngay_hieu_luc=2024-01-01
  doc_1 (PL01, seq=1):     thoi_han_hd="+12 tháng gia hạn"
  doc_2 (PL02, seq=2):     thoi_han_hd="+6 tháng (sửa PL01)"

Resolution:
  Pass 1 (doc_0): resolved["thoi_han_hd"] = "24 tháng"
  Pass 2 (doc_1): conflict! "24 tháng" → "+12 tháng" → mark doc_0.term superseded
                  resolved["thoi_han_hd"] = "+12 tháng"
  Pass 3 (doc_2): conflict! "+12 tháng" → "+6 tháng" → mark doc_1.term superseded
                  resolved["thoi_han_hd"] = "+6 tháng"

Derivation:
  ngay_hieu_luc = 2024-01-01 (từ HĐ chính, không bị override)
  thoi_han_hd gốc = 24 tháng → ngay_het_han baseline = 2025-12-31
  PL01 thêm 12 → 2026-12-31 (superseded)
  PL02 sửa thành 6 → 2026-06-30 ✓

Output obligation:
  type = 'contract_expiry'
  due_date = 2026-06-30
  needs_review = True  (chain có conflict)
  source_doc_chain = [doc_0.id, doc_1.id, doc_2.id]
  resolution_method = 'chain_resolved'
```

---

## 7. Trigger `needs_review = True`

| Điều kiện | Lý do | Action UI |
|---|---|---|
| Chain có ≥ 1 conflict (field bị override) | Điều 403: cần xác nhận SME chấp nhận | Banner "Tài liệu có điều khoản sửa đổi — xem xét" |
| Chain có ≥ 3 documents | Độ phức tạp cao | Badge "Chuỗi phức tạp" + link xem chain |
| `thoi_han_hd` không parse được (phi-số) | "vô thời hạn", "đến khi thanh lý" | Flag "Thời hạn cần xác nhận" |
| `doc_type` extraction confidence < 0.8 | Model không chắc | "Phân loại tài liệu cần xác nhận" |
| `ngay_het_han` derived (không explicit) | FR-OB-01 derivation, không phải từ văn bản | Hiển thị "Ước tính: [date] — dựa trên thời hạn HĐ" |
| Parent không tìm được (orphan annex) | Upload sai thứ tự hoặc thiếu HĐ chính | "Chưa liên kết HĐ chính — vui lòng chọn" |

---

## 8. Human Review UI Spec (→ KHE_Frontend_Admin)

### 8.1 Document chain viewer

```
┌─ HĐ Thuê MB 01/2024 [main_contract] ──────────────────────┐
│  Ký: 01/01/2024 | Hiệu lực: 01/01/2024 | Hết: (derived)  │
│                                                             │
│  ├─ Phụ lục 01 [annex] ──────────────────────────────────┐ │
│  │  Ký: 01/06/2024 | Thay đổi: thời hạn +12 tháng        │ │
│  │  ⚠ Bị sửa đổi bởi Phụ lục 02                         │ │
│  │                                                         │ │
│  │  └─ Phụ lục 02 [amendment] ─────────────────────────┐ │ │
│  │     Ký: 01/09/2025 | Sửa PL01: thời hạn → +6 tháng  │ │ │
│  │     ✓ Điều khoản hiệu lực hiện tại                   │ │ │
│  │                                                       └─┘ │
│  │                                                           │
│  └─ Phụ lục 03 [annex] ──────────────────────────────────┐  │
│     Ký: 01/01/2025 | Điều chỉnh: giá thuê +10%           │  │
│     ✓ Điều khoản hiệu lực hiện tại                       └──┘
└──────────────────────────────────────────────────────────────┘

Obligation được tạo:
  [!] Hết hạn HĐ: 30/06/2026 (từ chain) — Chờ xác nhận
  [!] Nhắc gia hạn: 01/04/2026 (30 ngày trước hết hạn)
  [✓] Điều chỉnh giá: 01/01/2026 (từ PL03)

[Xác nhận tất cả]  [Xem chi tiết từng mục]
```

### 8.2 Conflict resolution UI

Khi SME nhấn "Xem chi tiết" trên obligation `needs_review`:

```
Điều khoản thời hạn — Lịch sử thay đổi:

HĐ chính (01/01/2024): "24 tháng"
  ↓ Bị thay đổi bởi Phụ lục 01
Phụ lục 01 (01/06/2024): "gia hạn thêm 12 tháng"
  ↓ Bị sửa đổi bởi Phụ lục 02
Phụ lục 02 (01/09/2025): "chỉ gia hạn 6 tháng" ← ĐANG ÁP DỤNG

Ngày hết hạn tính toán: 30/06/2026

[✓ Xác nhận đúng]  [Sửa thủ công]
```

---

## 9. D-rules Mapping

| D-rule | Áp dụng trong module này | Cụ thể |
|---|---|---|
| **D-01** | Obligation engine | Resolved obligation là suggestion — SME phải confirm mới thành active |
| **D-02** | Human review gate | Chain conflict LUÔN cần `needs_review` + SME confirm |
| **D-06** | Extraction | AI chỉ đọc và trích xuất — KHÔNG suy diễn ý nghĩa pháp lý, KHÔNG điền template |
| **D-07** | SME edit obligation | Mọi edit sau khi obligation active → ghi `events` row với `event_type=field_edited` |
| **D-08** | Chat query | Nếu chain chưa resolved → chat trả "Không tìm thấy" thay vì guess |

---

## 10. Scope cho từng Sprint

### Sprint 1 (implement ngay)

| Item | Owner | Issue |
|---|---|---|
| Schema: `doc_type`, `parent_doc_id`, `seq_order`, `doc_date` vào `documents` | KHE_Backend | #26 |
| Schema: `overrides_term_id`, `effective_from`, `is_superseded` vào `terms` | KHE_Backend | #26 |
| Schema: `source_doc_chain`, `resolution_method` vào `obligations` | KHE_Backend | #26 |
| Extract `doc_type` + `parent_doc_id` trong VisionExtraction (single-doc) | KHE_AI | #28 |
| Obligation resolution: last-writer-wins + FR-OB-01 derivation | KHE_Backend | #26 |
| `needs_review` flag triggers (§7) | KHE_Backend | #26 |
| QC: test D-07 event_type=field_edited + D-08 no-match | KHE_QC | #33 |

### Sprint 2 (sau pilot feedback)

| Item | Owner |
|---|---|
| Context-aware extraction (inject prior terms vào prompt) | KHE_AI |
| Document chain viewer UI (§8.1) | KHE_Frontend_Admin |
| Conflict resolution UI per field (§8.2) | KHE_Frontend_Admin |
| `thoi_han_hd` phi-số policy (Q-1 — pending Kevin decision) | KHE_Backend |

### Phase 2+ (không thuộc MVP)

| Item | Lý do defer |
|---|---|
| Config-driven legal rule engine (Điều 403, Điều 407...) | Cần pilot data; D-02 blocker |
| Auto-resolve conflict không cần human confirm | D-01, D-02 violation |
| NLP parse "thời hạn" phi-số ("đến khi thanh lý", "theo đơn đặt hàng") | Cần corpus từ pilot |

---

## 11. Open Questions (cần Kevin quyết)

| ID | Câu hỏi | Impact |
|---|---|---|
| **Q-1** | `thoi_han_hd` = "vô thời hạn" — tạo obligation `open_ended` và nhắc mỗi năm, hay chỉ flag và không nhắc? | Obligation engine + reminder logic |
| **Q-2** | Khi SME upload PL mà không có HĐ chính trong hệ thống — xử lý như `standalone` hay block và yêu cầu upload HĐ chính trước? | UX ingest flow |
| **Q-3** | Chain conflict UI: hiển thị lịch sử từng field hay chỉ final resolved value với badge "đã sửa đổi"? | Sprint 2 UI scope |

---

*v0.1 — PM_Assistant draft · 2026-06-18 · Chờ KHE_Docs fold vào SRS §6 + cập nhật BRD §7 FR-EX/FR-OB*
