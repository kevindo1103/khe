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

from pydantic import BaseModel, ConfigDict, Field


class DocType(str, Enum):
    """MVP-supported document types (FR-EX-01). Vertical seed: F&B / bán lẻ."""

    LEASE = "hd_thue_mat_bang"          # HĐ thuê mặt bằng
    SUPPLIER = "hd_nha_cung_cap"        # HĐ nhà cung cấp
    LABOR = "hd_lao_dong"               # HĐ lao động
    OTHER = "khac"                      # fallback — flagged for human triage


# Canonical extracted fields (FR-EX-02). Keys are stable snake_case Vietnamese
# so downstream (obligation engine, frontend) bind to one source of truth.
CANONICAL_FIELDS: tuple[str, ...] = (
    "doi_tac",                # parties / bên ký
    "ngay_hieu_luc",          # effective date (ISO yyyy-mm-dd when parseable)
    "ngay_het_han",           # expiry date — M-3 target ≥90%
    "gia_tri_hd",             # contract value
    "thoi_han_hd",            # contract term / duration
    "dieu_khoan_gia_han",     # renewal clause
    "dieu_khoan_thanh_toan",  # payment terms
)

# Fields the Sprint-0 benchmark scores against (issue #3 acceptance):
# ngày hết hạn · giá trị HĐ · bên ký · thời hạn HĐ.
BENCHMARK_TARGET_FIELDS: tuple[str, ...] = (
    "ngay_het_han",
    "gia_tri_hd",
    "doi_tac",
    "thoi_han_hd",
)


class ExtractedField(BaseModel):
    """One extracted Term. value is None when not found on the page (D-08: say so,
    don't guess). confidence ∈ [0,1]; needs_review flags low-confidence / ambiguous."""

    model_config = ConfigDict(from_attributes=True)

    value: Optional[str] = Field(
        default=None,
        description="Giá trị bóc ra đúng như trên tài liệu, hoặc null nếu không tìm thấy.",
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Độ tin cậy 0..1."
    )
    needs_review: bool = Field(
        default=True, description="True nếu cần người kiểm tra (FR-EX-05)."
    )


class TokenUsage(BaseModel):
    """Token accounting for cost computation."""

    model_config = ConfigDict(from_attributes=True)

    input_tokens: int = 0
    output_tokens: int = 0


# --- LLM-facing structured-output schema -----------------------------------
# Flat object, fixed keys, no recursion → compatible with Claude structured
# outputs and Gemini response_schema. The model fills value/confidence/needs_review
# per field. `doi_tac` is a single text field (semicolon-separated if multiple
# parties) to stay within structured-output constraints.


class ContractExtractionLLM(BaseModel):
    """Exactly what we ask the model to emit. Mapped → ExtractionResult by providers."""

    model_config = ConfigDict(from_attributes=True)

    doc_type: DocType = Field(
        description="Loại tài liệu: hd_thue_mat_bang | hd_nha_cung_cap | hd_lao_dong | khac."
    )
    doc_type_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    doi_tac: ExtractedField = Field(default_factory=ExtractedField)
    ngay_hieu_luc: ExtractedField = Field(default_factory=ExtractedField)
    ngay_het_han: ExtractedField = Field(default_factory=ExtractedField)
    gia_tri_hd: ExtractedField = Field(default_factory=ExtractedField)
    thoi_han_hd: ExtractedField = Field(default_factory=ExtractedField)
    dieu_khoan_gia_han: ExtractedField = Field(default_factory=ExtractedField)
    dieu_khoan_thanh_toan: ExtractedField = Field(default_factory=ExtractedField)

    def as_field_map(self) -> dict[str, ExtractedField]:
        return {name: getattr(self, name) for name in CANONICAL_FIELDS}


class ExtractionResult(BaseModel):
    """Provider output consumed by the rest of Khế.

    Carries the extracted Terms + provenance. The obligation engine derives
    deadlines from `fields["ngay_het_han"]` etc.; the ledger records `provider`/
    `model` for audit (NĐ 13/2023 — who/what processed the PII)."""

    model_config = ConfigDict(from_attributes=True)

    doc_type: DocType
    doc_type_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    fields: dict[str, ExtractedField] = Field(default_factory=dict)

    provider: str = ""             # e.g. "gemini_flash"
    model: str = ""                # e.g. "gemini-2.5-flash"
    latency_ms: float = 0.0
    usage: TokenUsage = Field(default_factory=TokenUsage)
    cost_vnd: float = 0.0
    warnings: list[str] = Field(default_factory=list)

    @property
    def any_low_confidence(self) -> bool:
        return any(f.needs_review for f in self.fields.values())
