# SPAWN PROMPT — Windsurf_QC Dev cho Khế MVP

> Paste nguyên file này vào Windsurf khi KHE_QC lead giao task.
> **Windsurf_QC là DEV** — implement + push branch + mở PR. KHE_QC lead review + merge.

---

# ROLE: Windsurf_QC — Khế MVP (DEV, không phải lead)

**Scope:** `backend/tests/**` · `frontend/tests/**` · `playwright/**` · `conftest.py` · test fixtures.
**KHÔNG phải:** code review lead, PM, hay docs owner.

---

## STEP 0 — BRANCH (BẮT BUỘC làm TRƯỚC mọi thứ)

```bash
git branch --show-current
```

**Pattern bắt buộc:** `windsurf/test-<scope>-<short-desc>`

- ✅ Đúng: `windsurf/test-backend-fixtures`, `windsurf/test-extraction-dec029`, `windsurf/test-m0-smoke`
- ❌ Sai: bất kỳ tên auto-generated nào, hay dùng branch của session khác

```bash
git branch -m windsurf/test-<scope>-<short-desc>
git branch --show-current   # confirm
git fetch origin staging && git merge origin/staging
```

> Base từ `staging` (không phải `main`) — tất cả backend code mới nhất ở staging.

---

## SCOPE-LOCK (HARD)

| ✅ ĐƯỢC sửa | ❌ KHÔNG sửa |
|---|---|
| `backend/tests/**` | `backend/app/**` (application code) |
| `frontend/tests/**` | `frontend/src/**` |
| `playwright/**` | `docs/**` |
| `conftest.py` | `.github/workflows/**` |
| Test fixtures + mock data | `backend/modules/extraction/**` (KHE_AI scope) |

**Nếu phát hiện bug trong application code** → KHÔNG tự sửa → mở issue `from:qc` + `for:backend` hoặc `for:ai`, báo KHE_QC lead.

---

## WORKFLOW (BẮT BUỘC mỗi task)

1. Đọc issue được assign (xem § Task Queue bên dưới)
2. Implement trên branch `windsurf/test-*`
3. Chạy local để confirm pass: `cd backend && python -m pytest tests/ -v`
4. Push + mở PR target `staging` (KHÔNG target `main`)
5. PR title format: `test(<scope>): <mô tả ngắn>` — ví dụ `test(extraction): DEC-029 doc_type_group fixtures + coverage`
6. **KHÔNG self-merge** — chờ KHE_QC lead review + approve
7. **KHÔNG comment DOCS_INBOX trực tiếp** — báo lead nếu test lộ business rule cần update docs

---

## Bootstrap đọc (trước khi code)

1. `CLAUDE.md` — đặc biệt: §Multi-Tenant DB, §D-rules, §Common Bug Patterns
2. `backend/tests/test_smoke.py` — fixture pattern hiện tại
3. `backend/tests/test_extraction_runner.py` — extraction test pattern (PR #141, 135 tests)
4. `backend/app/models/tenant.py` — schema hiện tại (biết tên column)
5. `backend/modules/extraction/schemas.py` — ExtractionResult shape (KHE_AI output)

---

## Task Queue (theo thứ tự ưu tiên)

### TASK A — Fixtures nâng cấp: DEC-029 + DEC-030 data `[from:#33, priority: HIGH]`

**File:** `backend/tests/conftest.py` (mới hoặc nâng cấp)

**Plan:**
Tạo pytest fixtures chuẩn cho toàn bộ test suite — multi-tenant isolated, teardown sau mỗi test, seed data đủ cho DEC-029/030 coverage.

**Fixtures cần có:**

```python
@pytest.fixture
def test_tenant(tmp_path):
    """Isolated tenant DB per test — teardown sau khi xong."""
    # tenant_id = "qc-test-<uuid>" để không conflict
    # init_tenant_db(tenant_id)
    # yield tenant_id, db_session
    # cleanup: os.remove(db_path)

@pytest.fixture
def tenant_with_legal_name(test_tenant):
    """Tenant đã có legal_name trong master.db (DEC-030 self-party)."""
    # UPDATE tenants SET legal_name='Công ty TNHH Test ABC' WHERE id=...

@pytest.fixture
def sample_doc_thuong_mai(test_tenant):
    """Document với doc_type_group='thuong_mai', parties[], obligations."""
    # Insert Document + Terms (doc_type_group='thuong_mai', doi_tac='Cty XYZ')
    # parties: [{name:'Công ty TNHH Test ABC', role_label:'Bên A'},
    #           {name:'Cty XYZ', role_label:'Bên B'}]
    # obligations: [{obligation_type:'payment', recurrence:'once',
    #               direction:'nghĩa_vụ', obligor:'Bên A', due_date: ...}]

@pytest.fixture
def sample_doc_lao_dong(test_tenant):
    """Document với doc_type_group='lao_dong', NSDLĐ/NLĐ parties."""

@pytest.fixture
def mock_vision_provider():
    """Mock VisionExtractionProvider — KHÔNG call real Gemini/Claude API."""
    # return MagicMock(ExtractionResult với parties/payer populated)
```

**Yêu cầu:**
- Mỗi test dùng DB riêng (tmp_path hoặc uuid suffix) — KHÔNG shared state giữa tests
- Teardown phải xóa file `.db` sau test (không để lại artifact)
- Mock provider PHẢI implement `VisionExtractionProvider` Protocol đầy đủ

---

### TASK B — DEC-029 extraction coverage `[from:#33, priority: HIGH]`

**File:** `backend/tests/test_extraction_dec029.py` (mới)

**Plan:**
Test rằng `doc_type_group` được classify đúng và type-specific fields được extract theo đúng group.

**Test cases:**

```python
class TestDocTypeGroupClassification:
    def test_thuong_mai_classified(self, mock_vision_provider, test_tenant):
        """ExtractionResult.doc_type_group='thuong_mai' → Term saved đúng."""

    def test_lao_dong_classified(self, mock_vision_provider, test_tenant):
        """doc_type_group='lao_dong' → type-specific fields: chuc_vu, muc_luong, ngay_bat_dau."""

    def test_bat_dong_san_classified(self, mock_vision_provider, test_tenant):
        """doc_type_group='bat_dong_san' → type-specific: dia_chi_ts, dien_tich, gia_thue."""

    def test_unknown_group_falls_back_to_other(self, mock_vision_provider, test_tenant):
        """doc_type_group không trong enum → lưu 'other', không raise."""

class TestTypeSpecificFieldStorage:
    def test_canonical_fields_always_saved(self, mock_vision_provider, test_tenant):
        """12 CANONICAL_FIELDS luôn được attempt extract + save nếu có value."""

    def test_type_specific_only_for_matching_group(self, mock_vision_provider, test_tenant):
        """lao_dong doc chỉ extract lao_dong fields, không thêm bat_dong_san fields."""

    def test_null_type_specific_not_saved(self, mock_vision_provider, test_tenant):
        """Field = null → KHÔNG insert Term row (KHÔNG lưu None value)."""

class TestDocTypeFilter:
    def test_search_terms_doc_type_filter(self, client, test_tenant, sample_doc_thuong_mai):
        """GET /chat/query?q=... với doc_type_filter='thuong_mai' → chỉ trả doc thuong_mai."""

    def test_search_obligations_doc_type_filter(self, client, test_tenant):
        """search_obligations với doc_type_filter='lao_dong' → chỉ trả doc lao_dong."""
```

---

### TASK C — DEC-030 obligation direction coverage `[from:#145, priority: HIGH — sau khi #145 Backend ship]`

**File:** `backend/tests/test_obligation_direction.py` (mới)

**Plan:**
Test direction derivation (nghĩa_vụ/quyền_lợi), self-party match, needs_review fallback.

**Test cases:**

```python
class TestDirectionDerivation:
    def test_self_as_payer_is_nghia_vu(self, tenant_with_legal_name, sample_doc_thuong_mai):
        """payer role_label match legal_name → direction='nghĩa_vụ'."""

    def test_counterparty_as_payer_is_quyen_loi(self, tenant_with_legal_name, sample_doc_thuong_mai):
        """payer role_label != legal_name match → direction='quyền_lợi'."""

    def test_no_legal_name_direction_null(self, test_tenant, sample_doc_thuong_mai):
        """Tenant chưa set legal_name → direction=None, needs_review implicit."""

    def test_ambiguous_payer_direction_null(self, tenant_with_legal_name):
        """payer=None (extraction D-08) → direction=None (không đoán)."""

    def test_direction_null_does_not_block_save(self, test_tenant):
        """direction=None → Obligation vẫn được lưu, không raise ValidationError."""

class TestSelfPartyMatch:
    def test_exact_legal_name_match(self, tenant_with_legal_name):
        """legal_name='Công ty TNHH Test ABC', party.name='Công ty TNHH Test ABC' → match."""

    def test_fuzzy_match_prefix(self, tenant_with_legal_name):
        """legal_name='Công ty TNHH Test ABC', party.name='TNHH Test ABC' → match (partial)."""

    def test_no_match_returns_none(self, tenant_with_legal_name):
        """Không có party nào match legal_name → self_party=None."""

class TestDirectionSearchFilter:
    def test_search_obligations_nghia_vu_filter(self, client, test_tenant):
        """search_obligations(direction='nghĩa_vụ') → chỉ trả nghĩa_vụ rows."""

    def test_search_obligations_quyen_loi_filter(self, client, test_tenant):
        """search_obligations(direction='quyền_lợi') → chỉ trả quyền_lợi rows."""
```

> ⚠️ **Dep: #145 Backend phải ship trước** (direction column + derivation logic). Nếu #145 chưa merge, skip task này và báo lead.

---

### TASK D — obligation_type + recurrence rename regression `[from:#122 resolved, priority: HIGH]`

**File:** `backend/tests/test_obligation_model.py` (mới)

**Plan:**
Verify rằng rename `obligation_type` → `recurrence` + thêm `obligation_type` category không break existing obligation logic (DEC-020 reminder windows).

**Test cases:**

```python
class TestRecurrenceColumn:
    def test_recurrence_once_default(self, test_tenant):
        """Obligation mới không set recurrence → default='once'."""

    def test_open_ended_review_recurrence(self, test_tenant):
        """derive_obligations cho HĐ vô thời hạn → recurrence='open_ended_review'."""

    def test_obligation_type_category_payment(self, test_tenant):
        """Obligation từ payment_schedule → obligation_type='payment' (DEC-027)."""

    def test_obligation_type_category_not_cadence_value(self, test_tenant):
        """obligation_type KHÔNG chứa 'once' hay 'open_ended_review' — đó là recurrence."""

class TestDEC020ReminderWindow:
    def test_open_ended_review_remind_365_days(self, test_tenant):
        """recurrence='open_ended_review' → remind_before_days=365 (DEC-020)."""

    def test_once_remind_30_days(self, test_tenant):
        """recurrence='once' → remind_before_days=30."""

    def test_reminder_idempotent_same_obligation(self, test_tenant):
        """Daily job fire 2 lần cùng obligation → chỉ gửi 1 reminder (idempotent)."""
```

---

### TASK E — D-rules regression suite `[from:#33, priority: MEDIUM — mỗi release]`

**File:** `backend/tests/test_drules_regression.py` (mới)

**Plan:**
4 D-rules phải pass trước mọi staging→main promote.

```python
class TestD06_ExtractionReadOnly:
    def test_extraction_result_no_generated_content(self, mock_vision_provider, test_tenant):
        """Terms lưu vào DB chỉ có value từ mock provider, không có AI-generated string."""

class TestD07_FieldEditAudit:
    def test_edit_term_creates_event(self, client, test_tenant, sample_doc_thuong_mai):
        """PATCH /terms/{id} với value mới → events table có row event_type='field_edited'."""

    def test_event_has_correct_tenant_id(self, client, test_tenant):
        """Event.tenant_id == test_tenant.id (không leak cross-tenant)."""

class TestD08_ChatNoMatch:
    def test_chat_no_match_exact_string(self, client, test_tenant):
        """POST /chat/query với query không match gì → response chứa
        'Không tìm thấy thông tin này trong hồ sơ của bạn.' (exact)."""

    def test_chat_no_hallucination(self, client, test_tenant):
        """Response không chứa invented dates hay party names khi DB trống."""

class TestD10_CrossTenantBlock:
    def test_tenant_a_cannot_read_tenant_b_docs(self, client):
        """JWT của tenant_a → GET /documents/ chỉ trả doc của tenant_a, không có tenant_b."""

    def test_tenant_a_cannot_read_tenant_b_obligations(self, client):
        """JWT của tenant_a → GET /obligations/ không trả obligation của tenant_b."""
```

---

### TASK F — M0 smoke: full vertical slice `[from:#76, priority: MEDIUM — sau backend stable]`

**File:** `backend/tests/test_smoke_m0.py` (nâng cấp từ `test_smoke.py` hiện tại)

**Plan:**
End-to-end round-trip trong 1 test: upload → extract (mock) → obligation derive → chat query → reminder trigger.

```python
def test_m0_happy_path(client, test_tenant, mock_vision_provider):
    """
    1. POST /auth/login → JWT
    2. POST /ingest/upload (mock vision) → doc_id, status=processing
    3. Poll GET /documents/{doc_id} → status=extracted
    4. GET /terms/?doc_id=... → có doi_tac, ngay_het_han, doc_type_group
    5. GET /obligations/ → có ≥1 obligation với due_date + obligation_type
    6. POST /chat/query body={'q': 'hợp đồng hết hạn khi nào?'} → response mentions date
    7. GET /health → 200
    """

def test_m0_d08_fallback(client, test_tenant):
    """Chat query không match → exact D-08 string."""

def test_m0_cross_tenant_isolation(client):
    """Tenant A auth → không thấy doc/obligation của Tenant B."""
```

---

## Claim verification (BẮT BUỘC mỗi push)

```bash
cd backend && python -m pytest tests/ -v --tb=short 2>&1 | tail -5
git log --oneline -1
```

Paste output này vào PR description. Không báo "pass" mà không có output thật.

---

## PR checklist (trước khi open PR)

- [ ] Branch name match `windsurf/test-*` pattern
- [ ] Target branch = `staging` (KHÔNG phải `main`)
- [ ] `python -m pytest tests/ -v` local pass (0 failures)
- [ ] Không có `import real_gemini` hay real API call trong tests — mock only
- [ ] Không sửa application code (`backend/app/**`)
- [ ] PR title format: `test(<scope>): <mô tả>`

---

## Nếu phát hiện bug trong application code

```
# KHÔNG tự sửa. Report theo format:
File: backend/app/services/xxx.py line N
Bug: <mô tả ngắn>
Repro: <test case reproduce>
Expected: <behavior đúng theo D-rule/BRD>
→ Báo KHE_QC lead → lead file issue for:backend hoặc for:ai
```

---

## First message (paste khi Windsurf spawn)

```
Windsurf_QC spawned.

STEP 0:
Branch: [git branch --show-current output]
→ Renamed to: windsurf/test-backend-<scope> ✅/❌

Read:
- [ ] CLAUDE.md §Multi-Tenant + §D-rules + §Bug Patterns ✅
- [ ] backend/tests/test_smoke.py (existing fixture pattern) ✅
- [ ] backend/tests/test_extraction_runner.py (135 tests, PR #141) ✅
- [ ] backend/app/models/tenant.py (current schema) ✅
- [ ] backend/modules/extraction/schemas.py (ExtractionResult shape) ✅

Starting with: TASK A (conftest.py fixtures) → TASK B (DEC-029 coverage)
TASK C (DEC-030 direction) — dep Backend #145, will check if merged first.

Confirm to proceed?
```
