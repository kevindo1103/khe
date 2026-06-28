"""Extraction schemas — the contract between providers and the rest of Khế.

Two layers:
- `ContractExtractionLLM` — the shape we ask the model to fill (structured output).
  Kept flat + within structured-output limitations (no recursion, fixed keys).
- `ExtractionResult` — what a `VisionExtractionProvider.extract()` returns:
  the extracted fields PLUS provenance/metrics (provider, model, latency, cost,
  token usage). This is the object the obligation engine consumes later.

D-06: every field is READ-ONLY extraction. `needs_review` + `confidence` (FR-EX-05)
let the human verify; nothing here authors legal content.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocType(str, Enum):
    """MVP-supported document types (FR-EX-01). Vertical seed: F&B / bán lẻ."""

    LEASE = "hd_thue_mat_bang"          # HĐ thuê mặt bằng
    SUPPLIER = "hd_nha_cung_cap"        # HĐ nhà cung cấp
    LABOR = "hd_lao_dong"               # HĐ lao động
    OTHER = "khac"                      # fallback — flagged for human triage


# Canonical extracted fields (FR-EX-02). Keys are stable snake_case Vietnamese
# so downstream (obligation engine, frontend) bind to one source of truth.
#
# Split into two tiers because Claude's structured-output grammar rejects a wide
# schema ("Schema is too complex"):
# - BASE_CANONICAL_FIELDS (7): the lean set Claude (fallback) extracts. Includes ALL
#   benchmark targets (ngay_het_han, gia_tri_hd, doi_tac, thoi_han_hd).
# - V2_UNIVERSAL_FIELDS (5, DEC-029): extracted by Gemini (primary) only. Appear in
#   80%+ of the 126 contract types but live on the Full schema to keep Claude valid.
BASE_CANONICAL_FIELDS: tuple[str, ...] = (
    "doi_tac",                # parties / bên ký
    "ngay_hieu_luc",          # effective date (ISO yyyy-mm-dd when parseable)
    "ngay_het_han",           # expiry date — M-3 target ≥90%
    "gia_tri_hd",             # contract value
    "thoi_han_hd",            # contract term / duration
    "dieu_khoan_gia_han",     # renewal clause
    "dieu_khoan_thanh_toan",  # payment terms
)
V2_UNIVERSAL_FIELDS: tuple[str, ...] = (
    "doc_type_group",         # enum DOC_TYPE_GROUPS — classified first
    "tieu_de_hd",             # R1: contract title (heading from doc body, not filename)
    "so_hop_dong",            # R1: contract number (pattern "số XX/YY/ZZZZ")
    "ngay_ky",                # signing date (≠ effective date — common gap)
    "ngay_khai_truong",       # R6: commencement/opening date (≠ effective date)
    "tien_dat_coc",           # deposit / guarantee amount
    "thoi_han_bao_hanh",      # warranty period
    "thoi_han_thong_bao",     # notice period before termination
)
# Full universal set (12) — what the terms layer + Gemini Full schema bind to.
CANONICAL_FIELDS: tuple[str, ...] = (*BASE_CANONICAL_FIELDS, *V2_UNIVERSAL_FIELDS)

# Fields the Sprint-0 benchmark scores against (issue #3 acceptance):
# ngày hết hạn · giá trị HĐ · bên ký · thời hạn HĐ.
BENCHMARK_TARGET_FIELDS: tuple[str, ...] = (
    "ngay_het_han",
    "gia_tri_hd",
    "doi_tac",
    "thoi_han_hd",
)

# doc_type_group enum (DEC-029) — 10 groups collapsed from the 126-type lawyer
# catalogue + "other" fallback. AI classifies this FIRST; if unsure → "other"
# (D-08 spirit: never guess). D-05: general core, no hardcoded vertical lock-in.
DOC_TYPE_GROUPS: tuple[str, ...] = (
    "dan_su",             # Dân sự: cho mượn, vay, dịch vụ, ủy quyền
    "thuong_mai",         # Thương mại: NDA, MOU, đại lý, nhượng quyền
    "lao_dong",           # Lao động & việc làm — NĐ 337/2025 catalyst
    "bat_dong_san",       # Bất động sản & đất đai
    "van_tai_logistics",  # Vận tải, hạ tầng, năng lượng, logistics
    "xay_dung",           # Xây dựng, tư vấn thiết kế, cung ứng, bảo trì
    "cong_nghe_ip",       # Công nghệ, SaaS, sở hữu trí tuệ
    "tai_chinh",          # Tài chính, ngân hàng, bảo hiểm
    "bao_dam",            # Thế chấp, cầm cố, bảo lãnh, đặt cọc, ký quỹ
    "hanh_chinh",         # Ủy quyền, APA, công chứng, hành chính DN
    "other",              # Không xác định / mixed
)

# Type-specific field sets (DEC-029) — extracted only when doc_type_group matches.
# Stored as Term rows like any other field (terms table is key-value → no migration).
LABOR_FIELDS: tuple[str, ...] = (
    "luong_co_ban", "thoi_gian_thu_viec", "chu_ky_dong_bao_hiem",
)
REALESTATE_FIELDS: tuple[str, ...] = (
    "dia_chi_tai_san", "dien_tich", "lich_nop_tien_theo_tien_do",
)
CONSTRUCTION_FIELDS: tuple[str, ...] = (
    "tien_bao_lanh_thuc_hien", "tien_giu_lai_bao_hanh", "lich_tien_do_thi_cong",
)
SECURITY_FIELDS: tuple[str, ...] = (
    "tai_san_the_chap", "gia_tri_bao_dam", "thoi_han_dang_ky_bien_phap",
)
TECH_FIELDS: tuple[str, ...] = (
    "so_luong_nguoi_dung", "uptime_cam_ket", "chu_ky_gia_han_ban_quyen",
)
COMMERCIAL_FIELDS: tuple[str, ...] = (
    "pham_vi_dia_ly", "chi_tieu_doanh_so", "thoi_han_doc_quyen", "thoi_han_bao_mat",
)
TRANSPORT_FIELDS: tuple[str, ...] = (
    "tuyen_duong", "trong_tai_hang_hoa", "phuong_thuc_van_chuyen",
)
FINANCE_FIELDS: tuple[str, ...] = (
    "lai_suat", "lich_tra_goc_lai", "tai_san_dam_bao",
)
ADMIN_FIELDS: tuple[str, ...] = (
    "pham_vi_uy_quyen", "thoi_han_uy_quyen",
)

TYPE_SPECIFIC_FIELDS: dict[str, tuple[str, ...]] = {
    "lao_dong": LABOR_FIELDS,
    "bat_dong_san": REALESTATE_FIELDS,
    "xay_dung": CONSTRUCTION_FIELDS,
    "bao_dam": SECURITY_FIELDS,
    "cong_nghe_ip": TECH_FIELDS,
    "thuong_mai": COMMERCIAL_FIELDS,
    "van_tai_logistics": TRANSPORT_FIELDS,
    "tai_chinh": FINANCE_FIELDS,
    "hanh_chinh": ADMIN_FIELDS,
}

# Flat, de-duplicated tuple of every type-specific field (stable order).
ALL_TYPE_SPECIFIC_FIELDS: tuple[str, ...] = tuple(
    dict.fromkeys(f for fields in TYPE_SPECIFIC_FIELDS.values() for f in fields)
)


def _clamp_confidence(v: float) -> float:
    """Clamp to [0,1] in code instead of via Field(ge/le).

    Pydantic's ge/le emit JSON-schema minimum/maximum, which Gemini's structured-output
    grammar turns into a 'complex value matcher' — across many fields these blow past
    the 'too many states for serving' limit. A validator keeps the [0,1] invariant
    without putting bounds in the response schema."""
    try:
        return min(1.0, max(0.0, float(v)))
    except (TypeError, ValueError):
        return 0.0


class ExtractedField(BaseModel):
    """One extracted Term. value is None when not found on the page (D-08: say so,
    don't guess). confidence ∈ [0,1] (clamped); needs_review flags low-confidence."""

    model_config = ConfigDict(from_attributes=True)

    value: Optional[str] = Field(
        default=None,
        description="Giá trị bóc ra đúng như trên tài liệu, hoặc null nếu không tìm thấy.",
    )
    confidence: float = Field(default=0.0, description="Độ tin cậy 0..1.")
    needs_review: bool = Field(
        default=True, description="True nếu cần người kiểm tra (FR-EX-05)."
    )

    @field_validator("confidence")
    @classmethod
    def _clamp(cls, v: float) -> float:
        return _clamp_confidence(v)


class AnchoredField(ExtractedField):
    """An ExtractedField that also records WHERE on the source document the value was
    read — the trust anchor for Stage 3 ref-navigation (FR-EX-05, #230).

    Gemini-only: these slots live on the Full schema, NOT the lean Claude base, to stay
    within Claude's structured-output grammar budget ("Schema is too complex"). The
    merged Backend contract (#217) persists `page_num`/`ref`/`bbox` via getattr, so a
    plain ExtractedField (Claude fallback) degrades gracefully to NULL anchors → the FE
    shows plain text instead of a dead ref-link.

    READ-ONLY provenance (D-06): page/ref describe where the value sits; they never
    generate or alter legal content. Both are null when the model can't place the value
    (D-08 — no fabricated locations)."""

    page_num: Optional[int] = Field(
        default=None,
        description="Số trang (BẮT ĐẦU TỪ 1) nơi giá trị xuất hiện. null nếu không xác định được (D-08).",
    )
    ref: Optional[str] = Field(
        default=None,
        description='Nhãn điều/khoản/mục nơi giá trị xuất hiện, vd "Điều 8", "Khoản 2.3". null nếu không có.',
    )
    # `bbox` ([x0,y0,x1,y1] normalized 0..1) DEFERRED (#230): a list[float] on every field
    # expands Gemini's grammar state budget (the "too many states" failure mode). Populate
    # only after the page_num/ref grammar impact is measured on a live run. The Backend
    # column already exists (#217) → adding it later is forward-compatible, no migration.


class NamedExtractedField(AnchoredField):
    """An ExtractedField that names its own canonical key (DEC-029).

    Type-specific fields are emitted as ONE list of these instead of ~27 fixed object
    properties — a single array is far cheaper in Gemini's grammar state budget than
    dozens of optional bounded objects. `key` must be one of ALL_TYPE_SPECIFIC_FIELDS;
    unknown keys are dropped on mapping (no fabricated field names).

    Carries source anchors (page_num/ref) like every Gemini-path field (#230)."""

    key: str = Field(description="Canonical key của trường, vd 'luong_co_ban'.")



class TokenUsage(BaseModel):
    """Token accounting for cost computation."""

    model_config = ConfigDict(from_attributes=True)

    input_tokens: int = 0
    output_tokens: int = 0


class ClauseItem(BaseModel):
    """One numbered clause/article lifted verbatim from the document (DEC-026 + R3 #365).

    Feeds the `clauses` table (Backend #99) so chat function-calling has full clause
    text. READ-ONLY like every other extracted value (D-06): `content` is the clause
    text exactly as written — never translated, summarized, or paraphrased."""

    model_config = ConfigDict(from_attributes=True)

    num: Optional[str] = Field(
        default=None, description='Số hiệu điều/khoản/mục, vd "Điều 8", "Khoản 2.3", "Mục IV". null nếu không có.'
    )
    title: Optional[str] = Field(
        default=None, description='Tiêu đề điều khoản, vd "Chấm dứt hợp đồng". null nếu không có.'
    )
    content: str = Field(
        description="Toàn văn điều khoản, giữ nguyên tiếng Việt — KHÔNG dịch/tóm tắt."
    )
    level: Optional[int] = Field(
        default=None,
        description="Cấp bậc phân cấp: 1=Điều/Chương, 2=Khoản/Mục, 3=Điểm/tiểu mục. null nếu không xác định.",
    )
    clause_path: Optional[str] = Field(
        default=None,
        description='Đường dẫn phân cấp số hiệu, vd "2", "2.1", "2.1.1". null nếu không đánh số theo cấp.',
    )


class PaymentScheduleItem(BaseModel):
    """One payment/installment due in the contract (DEC-027 / #117).

    Backend `derive_obligations` turns each entry with a `due_date` into a
    `payment`-type Obligation row. Unstructured payment text ("theo từng đợt theo
    thông báo") → emit nothing here and keep the free-text `dieu_khoan_thanh_toan`
    Term instead (D-06 — no fabrication when structure isn't extractable)."""

    model_config = ConfigDict(from_attributes=True)

    amount: Optional[str] = Field(
        default=None, description="Số tiền của kỳ thanh toán (VND, giữ nguyên như trên tài liệu). null nếu không rõ."
    )
    due_date: Optional[str] = Field(
        default=None, description="Ngày đến hạn — ISO yyyy-mm-dd nếu rõ, hoặc mô tả tương đối nếu không. null nếu không có."
    )
    milestone: Optional[str] = Field(
        default=None, description='Mốc/diễn giải kỳ thanh toán, vd "Tạm ứng 30%". null nếu không có.'
    )
    recurrence: Optional[str] = Field(
        default=None, description='Chu kỳ lặp: "monthly" | "quarterly" | null (một lần). KHÔNG đoán nếu không nêu rõ.'
    )
    payer: Optional[str] = Field(
        default=None,
        description='Bên PHẢI TRẢ kỳ này — tên hoặc vai trò đúng như trên tài liệu (vd "Owner", "Bên B"). '
        "Để Backend phân biệt nghĩa vụ (mình trả) vs quyền lợi (đối tác trả cho mình). null nếu không rõ (DEC-030).",
    )


class ObligationScheduleItem(BaseModel):
    """One scheduled obligation lifted from the contract (DEC-030 Phase 2, #154).

    Generalizes the earlier `PaymentScheduleItem` to EVERY obligation category
    (payment · delivery · handover · expiration · renewal · review · warranty · other),
    plus event-triggered milestones and multi-installment series. Backend #153 Part 2
    maps each entry → an Obligation DB row.

    READ-ONLY (D-06): every value is verbatim. When a milestone anchors to an event
    rather than a fixed date ("sau nghiệm thu", "khi giao hàng"), `trigger="event"` and
    `due_date=None` — never fabricate a date (D-08). `amount_raw` is the raw string
    ("40%", "150.000.000 VND"), NOT parsed — Backend normalizes downstream."""

    model_config = ConfigDict(from_attributes=True)

    obligation_type: str = Field(
        description="Loại nghĩa vụ: payment | delivery | handover | expiration | renewal | "
        "review | warranty | other. Dùng 'other' nếu không khớp loại nào (KHÔNG ép loại, D-08)."
    )
    description: str = Field(
        description='Diễn giải đợt/nghĩa vụ, nguyên văn — vd "Đợt 2 — giao 40% hàng".'
    )
    amount_raw: Optional[str] = Field(
        default=None,
        description='Số tiền/giá trị NGUYÊN VĂN, KHÔNG parse — vd "40%", "150.000.000 VND". null nếu không có.',
    )
    due_date: Optional[str] = Field(
        default=None,
        description="Ngày đến hạn — ISO yyyy-mm-dd nếu rõ. null nếu trigger=event (D-08: không bịa ngày).",
    )
    recurrence: Optional[str] = Field(
        default=None,
        description='Chu kỳ lặp: "monthly" | "quarterly" | "yearly" | null (một lần). KHÔNG đoán nếu không nêu.',
    )
    obligor: Optional[str] = Field(
        default=None,
        description='Bên THỰC HIỆN nghĩa vụ này — tên hoặc vai trò đúng như trên tài liệu (vd "Owner", "Bên B"). '
        "Để Backend chia nghĩa vụ (mình làm) vs quyền lợi (đối tác làm cho mình). null nếu không rõ.",
    )
    # Series — set together when ONE obligation is split into multiple đợt (T3).
    series_id: Optional[str] = Field(
        default=None,
        description="Cùng một chuỗi đợt → cùng series_id (nhãn/uuid LLM tự sinh). null nếu nghĩa vụ đơn lẻ.",
    )
    milestone_index: Optional[int] = Field(
        default=None, description="Số thứ tự đợt trong chuỗi (bắt đầu từ 1). null nếu không phải chuỗi."
    )
    milestone_total: Optional[int] = Field(
        default=None, description="Tổng số đợt trong chuỗi. null nếu không phải chuỗi."
    )
    trigger: str = Field(
        default="date",
        description='"date" nếu đến hạn theo NGÀY; "event" nếu neo vào SỰ KIỆN (giao hàng, nghiệm thu...).',
    )
    trigger_condition: Optional[str] = Field(
        default=None,
        description='Điều kiện kích hoạt, NGUYÊN VĂN từ HĐ nếu trigger=event (vd "sau khi nghiệm thu"). null nếu trigger=date.',
    )
    trigger_delay_days: Optional[int] = Field(
        default=None,
        description='Số ngày trễ sau sự kiện nếu nêu rõ (vd 30 cho "30 ngày sau nghiệm thu"). null nếu không có.',
    )
    source_clause_num: Optional[str] = Field(
        default=None,
        description='Số hiệu điều/khoản SINH ra nghĩa vụ này, vd "Điều 5", "Khoản 3.2". '
        "Lấy đúng từ nhãn [..] của điều khoản chứa nghĩa vụ. null nếu không xác định được.",
    )
    derived_from: str = Field(
        default="original",
        description='Nguồn gốc: "original" (từ PDF gốc) hoặc "user_edit" (từ nội dung user đã sửa). '
        "Mặc định original — chỉ đặt user_edit khi re-derive từ edited_content.",
    )


class PartyItem(BaseModel):
    """A contracting party with its role label and details (DEC-030 + R2 #364).

    READ-ONLY (D-06): `role_label` is the term used IN the document — "Owner",
    "Operator", "Bên A", "Bên cho thuê", "NSDLĐ"… Which party is the SME ("self") is
    NOT decided here — Backend matches the tenant's legal name + the user confirms
    (D-02). Lets the obligation engine split nghĩa vụ (self) vs quyền lợi (đối tác)."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(description="Tên bên ký kết, đúng như trên tài liệu.")
    role_label: Optional[str] = Field(
        default=None,
        description='Vai trò trong HĐ, vd "Owner", "Operator", "Bên A", "Bên cho thuê", "NSDLĐ". null nếu không có.',
    )
    address: Optional[str] = Field(
        default=None,
        description="Địa chỉ bên ký kết, nguyên văn từ tài liệu. null nếu không có.",
    )
    representative: Optional[str] = Field(
        default=None,
        description='Người đại diện (vd "Ông Nguyễn Văn A — Giám đốc"). null nếu không có.',
    )
    tax_code: Optional[str] = Field(
        default=None,
        description="Mã số thuế (MST) bên ký kết. null nếu không có.",
    )


class DefinedTermItem(BaseModel):
    """A defined term from the contract's definitions section (R9 #372).

    READ-ONLY (D-06): both term and definition are verbatim from the document.
    NOT party aliases (those go in PartyItem) — these are legal/technical terms
    like "Năm Tài chính", "Khách sạn", "Thương hiệu"."""

    model_config = ConfigDict(from_attributes=True)

    term: str = Field(description='Thuật ngữ được định nghĩa, vd "Năm Tài chính", "Khách sạn".')
    definition: str = Field(description="Nội dung định nghĩa, nguyên văn từ tài liệu.")
    source_clause: Optional[str] = Field(
        default=None,
        description='Điều/mục chứa định nghĩa, vd "Phụ lục A", "Điều 1". null nếu không rõ.',
    )


class CrossReferenceItem(BaseModel):
    """A cross-reference between clauses/appendices detected in the document (R10 #373).

    READ-ONLY (D-06): captures reference patterns like "theo Điều 5",
    "quy định tại Phụ lục E". Backend resolves to actual clause/doc targets."""

    model_config = ConfigDict(from_attributes=True)

    source_clause: str = Field(
        description='Điều/khoản CHỨA tham chiếu, vd "Điều 3", "Khoản 2.1".',
    )
    target_ref: str = Field(
        description='Đích tham chiếu nguyên văn, vd "Điều 5", "Phụ lục E", "Khoản 8.2".',
    )
    context: Optional[str] = Field(
        default=None,
        description='Ngữ cảnh ngắn quanh tham chiếu, vd "theo quy định tại Điều 5". null nếu không cần.',
    )


# --- LLM-facing structured-output schemas ----------------------------------
# Two tiers:
#
# ContractExtractionLLM — **flat**, no nested arrays.
#   Used by Claude providers (claude-haiku-4-5 / claude-sonnet-4-6 via messages.parse /
#   output_format). Claude's grammar compiler times out on list[ClauseItem], so the
#   base schema stays flat — same constraint as the original design.
#   Result: ExtractionResult.clauses = [] for Claude fallbacks.
#
# ContractExtractionLLMFull(ContractExtractionLLM) — adds clauses list.
#   Used by GeminiFlashProvider (response_schema=). Gemini handles nested object
#   arrays without issue. Both Terms AND clauses come back in ONE vision call
#   (DEC-026 — no extra API call). `to_result()` reads clauses via getattr so it
#   works with both schemas.


class ContractExtractionLLM(BaseModel):
    """Lean flat schema for Claude structured outputs (output_format=). No nested
    arrays, only the 7 BASE_CANONICAL_FIELDS — Claude rejects a wider schema
    ('Schema is too complex'). Includes every benchmark target field."""

    model_config = ConfigDict(from_attributes=True)

    doc_type: DocType = Field(
        description="Loại tài liệu: hd_thue_mat_bang | hd_nha_cung_cap | hd_lao_dong | khac."
    )
    # No ge/le here — bounds become a Gemini grammar 'complex matcher' (state blow-up).
    # Clamp in a validator instead (mirrors ExtractedField.confidence) so an LLM that
    # returns >1.0 doesn't trip ExtractionResult's ge/le → ValidationError (#139).
    doc_type_confidence: float = Field(default=0.0)

    # original 7 (BASE_CANONICAL_FIELDS)
    doi_tac: ExtractedField = Field(default_factory=ExtractedField)
    ngay_hieu_luc: ExtractedField = Field(default_factory=ExtractedField)
    ngay_het_han: ExtractedField = Field(default_factory=ExtractedField)
    gia_tri_hd: ExtractedField = Field(default_factory=ExtractedField)
    thoi_han_hd: ExtractedField = Field(default_factory=ExtractedField)
    dieu_khoan_gia_han: ExtractedField = Field(default_factory=ExtractedField)
    dieu_khoan_thanh_toan: ExtractedField = Field(default_factory=ExtractedField)

    @field_validator("doc_type_confidence")
    @classmethod
    def _clamp_doc_type_conf(cls, v: float) -> float:
        return _clamp_confidence(v)

    def as_field_map(self) -> dict[str, ExtractedField]:
        return {name: getattr(self, name) for name in BASE_CANONICAL_FIELDS}


class ContractExtractionLLMFull(ContractExtractionLLM):
    """Extended schema for Gemini (response_schema=). Adds the v2 universal fields
    (DEC-029), the type-specific fields as ONE keyed list, the clause list (DEC-026),
    the scheduled-obligation list (DEC-030 Phase 2 / #154), and parties (DEC-030).

    Gemini handles nested arrays + a wider field set; Claude rejects them, so Claude
    stays on the lean base. Type-specific fields use a single `type_specific` array
    (not ~27 object properties) to stay within Gemini's grammar state budget.
    `to_result()` reads the extras via getattr, so both tiers map cleanly."""

    # Source anchors (#230): on the Gemini Full path EVERY universal field is an
    # AnchoredField (page_num/ref). The base 7 are re-declared here to upgrade their
    # type from the lean base (ExtractedField) — Claude's base stays anchor-free.
    doi_tac: AnchoredField = Field(default_factory=AnchoredField)
    ngay_hieu_luc: AnchoredField = Field(default_factory=AnchoredField)
    ngay_het_han: AnchoredField = Field(default_factory=AnchoredField)
    gia_tri_hd: AnchoredField = Field(default_factory=AnchoredField)
    thoi_han_hd: AnchoredField = Field(default_factory=AnchoredField)
    dieu_khoan_gia_han: AnchoredField = Field(default_factory=AnchoredField)
    dieu_khoan_thanh_toan: AnchoredField = Field(default_factory=AnchoredField)

    # v2 universal (DEC-029) — Gemini-only (Claude base omits them to stay valid)
    doc_type_group: AnchoredField = Field(default_factory=AnchoredField)
    tieu_de_hd: AnchoredField = Field(default_factory=AnchoredField)
    so_hop_dong: AnchoredField = Field(default_factory=AnchoredField)
    ngay_ky: AnchoredField = Field(default_factory=AnchoredField)
    ngay_khai_truong: AnchoredField = Field(default_factory=AnchoredField)
    tien_dat_coc: AnchoredField = Field(default_factory=AnchoredField)
    thoi_han_bao_hanh: AnchoredField = Field(default_factory=AnchoredField)
    thoi_han_thong_bao: AnchoredField = Field(default_factory=AnchoredField)

    type_specific: list[NamedExtractedField] = Field(
        default_factory=list,
        description="Các trường theo nhóm doc_type_group (DEC-029), mỗi phần tử có 'key'.",
    )
    clauses: list[ClauseItem] = Field(
        default_factory=list,
        description="Danh sách MỌI điều/khoản/mục trong tài liệu, nguyên văn (DEC-026).",
    )
    obligation_schedule: list[ObligationScheduleItem] = Field(
        default_factory=list,
        description="MỌI nghĩa vụ có lịch/đợt (DEC-030 Phase 2 — payment/delivery/handover/...). "
        "Rỗng nếu không có nghĩa vụ cấu trúc được.",
    )
    parties: list[PartyItem] = Field(
        default_factory=list,
        description="Các bên ký kết kèm vai trò (DEC-030) — để Backend xác định 'bên mình' và chia nghĩa vụ/quyền lợi.",
    )
    defined_terms: list[DefinedTermItem] = Field(
        default_factory=list,
        description="Cặp thuật ngữ/định nghĩa từ phần Định nghĩa (R9). Rỗng nếu không có section định nghĩa.",
    )
    cross_references: list[CrossReferenceItem] = Field(
        default_factory=list,
        description="Tham chiếu chéo giữa điều/khoản/phụ lục (R10). Rỗng nếu không phát hiện tham chiếu.",
    )
    has_signature: bool = Field(
        default=False,
        description="True nếu phát hiện chữ ký/con dấu trên tài liệu (R5).",
    )
    signature_pages: list[int] = Field(
        default_factory=list,
        description="Danh sách số trang có chữ ký/con dấu (bắt đầu từ 1). Rỗng nếu không có (R5).",
    )

    def as_field_map(self) -> dict[str, ExtractedField]:
        # Universal fields are AnchoredField on this path → page_num/ref pass through
        # unchanged (pydantic keeps the subclass instance; ExtractionResult persists it).
        fields = {name: getattr(self, name) for name in CANONICAL_FIELDS}
        # Fold type-specific entries in by key; drop unknown keys (no fabricated fields).
        valid = set(ALL_TYPE_SPECIFIC_FIELDS)
        for nf in self.type_specific:
            if nf.key in valid:
                fields[nf.key] = AnchoredField(
                    value=nf.value, confidence=nf.confidence, needs_review=nf.needs_review,
                    page_num=nf.page_num, ref=nf.ref,
                )
        return fields


class ExtractionResult(BaseModel):
    """Provider output consumed by the rest of Khế.

    Carries the extracted Terms + provenance. The obligation engine derives
    deadlines from `fields["ngay_het_han"]` etc.; the ledger records `provider`/
    `model` for audit (NĐ 13/2023 — who/what processed the PII)."""

    model_config = ConfigDict(from_attributes=True)

    doc_type: DocType
    doc_type_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    fields: dict[str, ExtractedField] = Field(default_factory=dict)
    # Full clause list from the same vision call (DEC-026). Default empty →
    # backward-compatible: existing callers that ignore `clauses` keep working.
    clauses: list[ClauseItem] = Field(default_factory=list)
    # Structured scheduled obligations (DEC-030 Phase 2 / #154) → Backend #153 Part 2
    # derives one Obligation row per entry (any category, not just payment). Default
    # empty (Claude fallback + unstructured contracts).
    obligation_schedule: list[ObligationScheduleItem] = Field(default_factory=list)
    # Parties + role labels (DEC-030) → Backend matches tenant legal name to find
    # 'self', then splits obligations into nghĩa vụ (self) vs quyền lợi (đối tác).
    # Gemini-only; Claude fallback leaves [] (use flat `fields["doi_tac"]`).
    parties: list[PartyItem] = Field(default_factory=list)
    defined_terms: list[DefinedTermItem] = Field(default_factory=list)
    cross_references: list[CrossReferenceItem] = Field(default_factory=list)
    has_signature: bool = False
    signature_pages: list[int] = Field(default_factory=list)

    provider: str = ""             # e.g. "gemini_flash"
    model: str = ""                # e.g. "gemini-2.5-flash"
    latency_ms: float = 0.0
    usage: TokenUsage = Field(default_factory=TokenUsage)
    cost_vnd: float = 0.0
    warnings: list[str] = Field(default_factory=list)

    @property
    def payment_schedule(self) -> list[PaymentScheduleItem]:
        """DEPRECATED compat shim (#154) — REMOVE after Backend #153 Part 2 cuts over
        to `obligation_schedule`. Projects payment-type scheduled obligations back onto
        the old `PaymentScheduleItem` shape so Backend's PR-#141 consumer keeps working
        during the rename window (no AttributeError before the cutover lands)."""
        return [
            PaymentScheduleItem(
                amount=i.amount_raw,
                due_date=i.due_date,
                milestone=i.description,
                recurrence=i.recurrence,
                payer=i.obligor,
            )
            for i in self.obligation_schedule
            if i.obligation_type == "payment"
        ]

    @property
    def any_low_confidence(self) -> bool:
        return any(f.needs_review for f in self.fields.values())

    @property
    def is_error(self) -> bool:
        """True when the provider FAILED to process the document (API error / no
        structured output) — no tokens consumed + a warning emitted. Distinct from
        a successful extraction that merely flags fields for review (D-08). Lets
        Backend map a hard failure → 503/status=failed, and lets the fallback
        chain advance to the next provider without re-charging the happy path."""
        return bool(self.warnings) and self.usage.input_tokens == 0
