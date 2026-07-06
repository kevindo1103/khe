"""Two-pass map-reduce extraction — bounded, resumable large-doc clause extraction
(#448, WS2-AI of mini-sprint #443. Fixes #442: MAX_TOKENS on large docs).

Large contracts (Điều + multiple Phụ lục, e.g. doc #20) hit Gemini's output-token
ceiling in a single vision/text call because the TOÀN VĂN rule (PR #425) requires
verbatim body text for every clause. Splitting extraction into two passes keeps the
full verbatim content while bounding each individual call's output:

  Pass 1 — SKELETON (Map): one call on the full OCR text, hierarchy ONLY
    (num/title/level/clause_path), NO verbatim body → tiny output, effectively never
    hits MAX_TOKENS regardless of document size. Depends on #439's clause_path rules
    (QUY TẮC PHỤ LỤC — already shipped, PR #425) for correct Phụ lục nesting.

  Pass 2 — CONTENT FILL (Reduce), per section: given one section's OCR text (e.g. one
    Điều or one Phụ lục) + its skeleton clause list, return full verbatim content for
    just that section's clauses. Bounded because a section is a fraction of the whole
    document, not the whole thing.

  Pass 3 — PARAGRAPH SPLIT: fallback for the rare single clause whose own verbatim
    body alone exceeds the per-call budget (e.g. a giant table or a huge Phụ lục
    clause). Fills incrementally by paragraph/page; content stays LLM-cleaned per
    Kevin's ratified decision (NOT coordinate-slicing — #443).

This module owns the KHE_AI half (prompts + pass design). Backend's WS2b (#449) owns
the state machine: persisting `content_status` (skeleton/filled/truncated), grouping
clauses into sections, iterating Pass 2 per section with per-section commits (durable
checkpoints — killing mid-run and re-running resumes from non-'filled' clauses only),
and invoking Pass 3 when a section's fill hits MAX_TOKENS on a single clause.

Guardrails (same as vision extraction, D-06/D-08): read-only, never fabricate content
or clause_path; unnamed sub-clauses get title=null (never an invented title) — the
frontend renders a placeholder for those, per #443's ratified UX note.
"""

from __future__ import annotations

import os
import time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .prompts import SYSTEM_GUARDRAIL
from .providers.base import cost_vnd, finish_reason
from .schemas import TokenUsage

# Same model + pricing as GeminiFlashProvider/HybridOCRProvider — text-only calls
# (OCR text already extracted by the time two-pass runs), no vision surcharge.
_MODEL = "gemini-2.5-flash"
_IN_USD_PER_MTOK = 0.30
_OUT_USD_PER_MTOK = 2.50

# Explicit per-pass caps (#445 precedent — never rely on the SDK's implicit default).
# Skeleton is hierarchy-only so it should never approach even a small cap; the cap
# exists as a circuit breaker, not a expected-to-bind limit. Fill is per-SECTION
# (a fraction of the whole doc), so it can stay well under the 65,536 model ceiling
# used for single-call whole-document extraction. Paragraph fill is a single
# paragraph/page chunk — smallest of all.
_SKELETON_MAX_OUTPUT_TOKENS = 16_384
_FILL_MAX_OUTPUT_TOKENS = 32_768
_PARAGRAPH_MAX_OUTPUT_TOKENS = 8_192


# ============================================================================
# Pass 1 — Skeleton (Map)
# ============================================================================

class SkeletonClauseResult(BaseModel):
    """One clause's hierarchy position, no body content (Pass 1 output)."""

    model_config = ConfigDict(from_attributes=True)

    num: Optional[str] = None
    title: Optional[str] = None
    level: Optional[int] = None
    clause_path: Optional[str] = None


class SkeletonResult(BaseModel):
    """Return value of `extract_skeleton()`."""

    model_config = ConfigDict(from_attributes=True)

    clauses: list[SkeletonClauseResult] = Field(default_factory=list)
    provider: str = ""
    model: str = ""
    cost_vnd: float = 0.0
    truncated: bool = False  # finish_reason == MAX_TOKENS — should be near-impossible
    warnings: list[str] = Field(default_factory=list)


class _SkeletonClauseLLM(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    num: Optional[str] = Field(
        default=None, description='Số hiệu điều/khoản/mục, vd "Điều 8", "10.1", "Phụ lục 1". null nếu không có.'
    )
    title: Optional[str] = Field(
        default=None,
        description='Tiêu đề điều khoản NẾU tài liệu có ghi rõ. null nếu KHÔNG có tiêu đề riêng — '
        "TUYỆT ĐỐI KHÔNG bịa tiêu đề (D-06). Khoản/mục con thường không có tiêu đề riêng → null là bình thường.",
    )
    level: Optional[int] = Field(
        default=None, description="Cấp bậc: 1=Điều/Chương/Phụ lục, 2=Khoản/Mục, 3=Điểm/tiểu mục."
    )
    clause_path: Optional[str] = Field(
        default=None,
        description='Đường dẫn phân cấp, vd "10", "10.1", "PL-1", "PL-1.1". null nếu không đánh số theo cấp.',
    )


class _SkeletonExtractionLLM(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clauses: list[_SkeletonClauseLLM] = Field(default_factory=list)


_SKELETON_SPEC = """\
Đọc TOÀN BỘ văn bản hợp đồng tiếng Việt bên dưới (đã OCR) và trả về CẤU TRÚC PHÂN CẤP
của mọi điều/khoản/mục — KHÔNG trả về nội dung (content). Đây là bước xây khung
(skeleton) trước khi bóc nội dung từng phần riêng ở bước sau — bạn CHỈ cần num, title,
level, clause_path cho MỖI điều khoản, theo đúng thứ tự xuất hiện trong tài liệu.

🔴 QUY TẮC QUAN TRỌNG NHẤT — BẮT BUỘC TÁCH SUB-CLAUSES:
  Khi nội dung Điều X chứa các khoản đánh số X.1, X.2, X.3..., mỗi khoản PHẢI là một
  phần tử RIÊNG trong danh sách "clauses" — không được bỏ qua chỉ vì không cần content.

  VÍ DỤ — tài liệu viết:
    "Điều 10. CHUYỂN NHƯỢNG VÀ CHẤM DỨT
     10.1 Thỏa thuận Ký quỹ sẽ chấm dứt khi...
     10.2 Bên B không được chuyển nhượng..."

  ✅ ĐÚNG:
    [{"num":"Điều 10", "title":"CHUYỂN NHƯỢNG VÀ CHẤM DỨT", "level":1, "clause_path":"10"},
     {"num":"10.1", "title":null, "level":2, "clause_path":"10.1"},
     {"num":"10.2", "title":null, "level":2, "clause_path":"10.2"}]

⚠️ QUY TẮC PHỤ LỤC — sub-clauses trong Phụ lục dùng prefix "PL-":
  Nếu tài liệu có Phụ lục (Phụ lục 1, Phụ lục A...) nằm trong cùng file:
    level=1: num="Phụ lục 1", clause_path="PL-1"
    level=2: Khoản/mục thuộc Phụ lục 1 → clause_path="PL-1.1", "PL-1.2"...
    level=3: Điểm/tiểu mục → clause_path="PL-1.1.1"
  ❌ Sai: clause_path="1" cho Khoản thuộc Phụ lục (TRÙNG với Điều 1)
  ✅ Đúng: clause_path="PL-1.1" (unique, không collision với Điều 1)

⚠️ LETTERED ITEMS (a, b, c, ...) KHÔNG PHẢI ĐIỀU RIÊNG:
  a), b), c)... bên trong một Điều/Khoản là sub-items của CÙNG một clause — KHÔNG
  tạo phần tử riêng cho từng lettered item.

⚠️ KHÔNG FLAT: nếu tài liệu có sub-headings dạng X.Y, "clauses" PHẢI có level > 1.
  Nếu tất cả đều level=1 mà tài liệu rõ ràng có khoản con → bạn thiếu sub-clauses, tách lại.

⚠️ TIÊU ĐỀ: title = null khi khoản/mục KHÔNG có tiêu đề riêng trên tài liệu (rất phổ
  biến với Khoản con). KHÔNG bịa tiêu đề để lấp chỗ trống (D-06).

⚠️ KHÔNG TRẢ VỀ NỘI DUNG: đây CHỈ là bước xây khung. TUYỆT ĐỐI KHÔNG điền/tóm tắt nội
  dung điều khoản vào bất kỳ trường nào — nội dung sẽ được bóc riêng ở bước sau.

Bao gồm MỌI điều khoản theo đúng thứ tự xuất hiện. Không có điều khoản đánh số →
clauses = [].

VĂN BẢN (đã OCR):
__OCR_TEXT__

Trả về JSON đúng schema, không thêm văn bản ngoài JSON.
"""


def build_skeleton_instruction(ocr_text: str) -> str:
    """Pure prompt builder for Pass 1 (unit-testable without SDK/keys).

    Uses a placeholder + `.replace()` rather than `.format()` — the spec text
    contains literal `{...}` JSON examples that `.format()` would choke on.
    """
    return _SKELETON_SPEC.replace("__OCR_TEXT__", ocr_text)


def _to_skeleton_result(
    parsed: _SkeletonExtractionLLM, *, provider: str, cost: float, truncated: bool
) -> SkeletonResult:
    clauses = [
        SkeletonClauseResult(num=c.num, title=c.title, level=c.level, clause_path=c.clause_path)
        for c in parsed.clauses
    ]
    warnings = ["Skeleton output hit MAX_TOKENS — unexpected, doc may be extreme."] if truncated else []
    return SkeletonResult(
        clauses=clauses, provider=provider, model=_MODEL, cost_vnd=cost,
        truncated=truncated, warnings=warnings,
    )


async def extract_skeleton(ocr_text: str, *, api_key: str | None = None) -> SkeletonResult:
    """Pass 1: hierarchy-only skeleton from the full OCR text of a document."""
    if not ocr_text or not ocr_text.strip():
        return SkeletonResult(provider="none", warnings=["empty_ocr_text"])

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return SkeletonResult(provider=_MODEL, warnings=["google-genai SDK not installed"])

    client = genai.Client(
        api_key=api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    )
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_GUARDRAIL,
        response_mime_type="application/json",
        response_schema=_SkeletonExtractionLLM,
        temperature=0.0,
        max_output_tokens=_SKELETON_MAX_OUTPUT_TOKENS,
    )

    try:
        response = await client.aio.models.generate_content(
            model=_MODEL,
            contents=[types.Part.from_text(text=build_skeleton_instruction(ocr_text))],
            config=config,
        )
    except Exception as exc:  # noqa: BLE001 - report, never fabricate
        return SkeletonResult(provider=_MODEL, warnings=[f"skeleton call failed: {type(exc).__name__}: {exc}"])

    parsed = getattr(response, "parsed", None)
    fr = finish_reason(response)
    truncated = fr == "MAX_TOKENS"
    if not isinstance(parsed, _SkeletonExtractionLLM):
        return SkeletonResult(
            provider=_MODEL, truncated=truncated,
            warnings=[f"skeleton returned no structured output (finish_reason={fr})"],
        )

    meta = getattr(response, "usage_metadata", None)
    usage = TokenUsage(
        input_tokens=getattr(meta, "prompt_token_count", 0) or 0,
        output_tokens=getattr(meta, "candidates_token_count", 0) or 0,
    )
    cost = cost_vnd(usage, _IN_USD_PER_MTOK, _OUT_USD_PER_MTOK)
    result = _to_skeleton_result(parsed, provider=_MODEL, cost=cost, truncated=truncated)
    if fr not in (None, "STOP", "MAX_TOKENS"):
        result.warnings.append(f"unexpected finish_reason={fr} despite successful parse")
    return result


# ============================================================================
# Pass 2 — Content fill (Reduce), per section
# ============================================================================

class FillClauseResult(BaseModel):
    """One clause's verbatim content, matched back to its skeleton clause_path."""

    model_config = ConfigDict(from_attributes=True)

    clause_path: Optional[str] = None
    content: str = ""


class FillResult(BaseModel):
    """Return value of `fill_section()`."""

    model_config = ConfigDict(from_attributes=True)

    clauses: list[FillClauseResult] = Field(default_factory=list)
    provider: str = ""
    model: str = ""
    cost_vnd: float = 0.0
    truncated: bool = False  # finish_reason == MAX_TOKENS → Backend should retry via Pass 3
    warnings: list[str] = Field(default_factory=list)


class _FillClauseLLM(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clause_path: Optional[str] = Field(
        default=None, description='Phải khớp CHÍNH XÁC một clause_path trong danh sách khung đã cho, vd "10.1".'
    )
    content: str = Field(description="Toàn văn điều khoản, giữ nguyên tiếng Việt — KHÔNG dịch/tóm tắt/cắt ngắn.")


class _FillExtractionLLM(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clauses: list[_FillClauseLLM] = Field(default_factory=list)


def _clause_manifest(skeleton_clauses: list[SkeletonClauseResult]) -> str:
    """Render the section's skeleton (from Pass 1) as the manifest Pass 2 must fill —
    exactly these clause_paths, no more, no fewer.

    Clauses with clause_path=None (Pass 1 legitimately emits this for unrecognised
    numbering) are called out as unmatched rather than silently stringified to the
    literal text "None" (which the model could echo back as-is, corrupting a
    downstream exact-match lookup that expects real JSON null)."""
    lines = []
    for c in skeleton_clauses:
        label = " — ".join(p for p in (c.num, c.title) if p) or "(không số hiệu)"
        if c.clause_path:
            lines.append(f'- clause_path="{c.clause_path}": {label}')
        else:
            lines.append(f'- (KHÔNG có clause_path — để clause_path=null khi trả về): {label}')
    return "\n".join(lines)


_FILL_SPEC = """\
Dưới đây là TOÀN VĂN OCR của MỘT PHẦN (section) của một hợp đồng tiếng Việt, cùng với
danh sách KHUNG (skeleton) các điều/khoản đã xác định trước cho đúng phần này. Nhiệm vụ
của bạn: điền TOÀN VĂN nội dung (content) cho ĐÚNG và CHỈ những clause_path trong danh
sách khung dưới đây — KHÔNG thêm clause_path mới, KHÔNG bỏ sót.

DANH SÁCH KHUNG (PHẢI điền đủ, đúng clause_path):
__MANIFEST__

⚠️ TOÀN VĂN — BẮT BUỘC:
  content PHẢI là nội dung ĐẦY ĐỦ, NGUYÊN VĂN của điều khoản đó, bao gồm TẤT CẢ lettered
  items (a, b, c, d...) nếu có. KHÔNG cắt ngắn sau câu giới thiệu, KHÔNG tóm tắt.
  ❌ Sai: content="Trong Thỏa thuận này, các cụm từ dưới đây được hiểu như sau:"
  ✅ Đúng: content="Trong Thỏa thuận này...: a) \"Bên A\" là... b) \"Bên B\" là... c)...d)..."

⚠️ Điều/Khoản cha CHỈ chứa sub-clauses (không có nội dung riêng ngoài các khoản con) →
  content = "" (rỗng) cho clause_path của điều cha đó — nội dung đã nằm ở các khoản con.

⚠️ KHỚP clause_path: mỗi phần tử trả về PHẢI có clause_path khớp CHÍNH XÁC với danh sách
  khung ở trên (copy nguyên văn). KHÔNG bịa clause_path mới không có trong khung.

VĂN BẢN SECTION (đã OCR):
__SECTION_TEXT__

Trả về JSON đúng schema, không thêm văn bản ngoài JSON.
"""


def build_fill_instruction(section_text: str, skeleton_clauses: list[SkeletonClauseResult]) -> str:
    """Pure prompt builder for Pass 2 (unit-testable without SDK/keys)."""
    return (
        _FILL_SPEC.replace("__MANIFEST__", _clause_manifest(skeleton_clauses))
        .replace("__SECTION_TEXT__", section_text)
    )


def _to_fill_result(
    parsed: _FillExtractionLLM,
    skeleton_clauses: list[SkeletonClauseResult],
    *,
    provider: str,
    cost: float,
    truncated: bool,
) -> FillResult:
    """Normalize LLM output → FillResult, enforcing the manifest's own "KHÔNG bịa
    clause_path mới" rule in code (not just prompt text): any returned clause_path
    that isn't one of the section's known (non-null) skeleton paths — including the
    literal string "None"/"null" a model might echo for an unnumbered manifest entry
    — is dropped and counted in a warning rather than silently accepted as real data.
    """
    valid_paths = {c.clause_path for c in skeleton_clauses if c.clause_path}
    clauses: list[FillClauseResult] = []
    dropped = 0
    for c in parsed.clauses:
        if c.clause_path not in valid_paths:
            dropped += 1
            continue
        clauses.append(FillClauseResult(clause_path=c.clause_path, content=c.content))

    warnings: list[str] = []
    if truncated:
        warnings.append(
            "Fill output hit MAX_TOKENS — section likely has an oversized clause; retry via paragraph-split."
        )
    if dropped:
        warnings.append(
            f"Dropped {dropped} returned clause(s) with clause_path not in this section's skeleton "
            "(hallucinated, mismatched, or an unnumbered manifest entry echoed back verbatim)."
        )
    return FillResult(
        clauses=clauses, provider=provider, model=_MODEL, cost_vnd=cost,
        truncated=truncated, warnings=warnings,
    )


async def fill_section(
    section_text: str,
    skeleton_clauses: list[SkeletonClauseResult],
    *,
    api_key: str | None = None,
) -> FillResult:
    """Pass 2: verbatim content for one section's clauses (a Điều or a Phụ lục),
    bounded to that section's OCR text + skeleton manifest.

    `truncated=True` (finish_reason == MAX_TOKENS) signals Backend's WS2b runner to
    mark this section for the paragraph-split fallback (Pass 3) rather than retry
    the whole section — a single oversized clause is the usual culprit.
    """
    if not skeleton_clauses:
        return FillResult(provider="none", warnings=["empty_skeleton"])
    if not section_text or not section_text.strip():
        return FillResult(provider="none", warnings=["empty_section_text"])

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return FillResult(provider=_MODEL, warnings=["google-genai SDK not installed"])

    client = genai.Client(
        api_key=api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    )
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_GUARDRAIL,
        response_mime_type="application/json",
        response_schema=_FillExtractionLLM,
        temperature=0.0,
        max_output_tokens=_FILL_MAX_OUTPUT_TOKENS,
    )

    try:
        response = await client.aio.models.generate_content(
            model=_MODEL,
            contents=[types.Part.from_text(text=build_fill_instruction(section_text, skeleton_clauses))],
            config=config,
        )
    except Exception as exc:  # noqa: BLE001 - report, never fabricate
        return FillResult(provider=_MODEL, warnings=[f"fill call failed: {type(exc).__name__}: {exc}"])

    parsed = getattr(response, "parsed", None)
    fr = finish_reason(response)
    truncated = fr == "MAX_TOKENS"
    if not isinstance(parsed, _FillExtractionLLM):
        return FillResult(
            provider=_MODEL, truncated=truncated,
            warnings=[f"fill returned no structured output (finish_reason={fr})"],
        )

    meta = getattr(response, "usage_metadata", None)
    usage = TokenUsage(
        input_tokens=getattr(meta, "prompt_token_count", 0) or 0,
        output_tokens=getattr(meta, "candidates_token_count", 0) or 0,
    )
    cost = cost_vnd(usage, _IN_USD_PER_MTOK, _OUT_USD_PER_MTOK)
    result = _to_fill_result(parsed, skeleton_clauses, provider=_MODEL, cost=cost, truncated=truncated)
    # Parsed successfully but with an anomalous finish_reason (e.g. RECITATION/SAFETY
    # racing a partial parse) — surface it even though data came back, so a caller
    # doesn't mistake this for a clean completion (#456 review finding).
    if fr not in (None, "STOP", "MAX_TOKENS"):
        result.warnings.append(f"unexpected finish_reason={fr} despite successful parse")
    return result


# ============================================================================
# Pass 3 — Paragraph split (single oversized clause, incremental fallback)
# ============================================================================

class ParagraphFillResult(BaseModel):
    """Return value of `fill_paragraph()` — one chunk of a single oversized clause's
    verbatim content. Backend concatenates chunks in order to assemble the full
    clause content (content stays LLM-cleaned per section, not coordinate-sliced)."""

    model_config = ConfigDict(from_attributes=True)

    content: str = ""
    provider: str = ""
    model: str = ""
    cost_vnd: float = 0.0
    truncated: bool = False
    warnings: list[str] = Field(default_factory=list)


class _ParagraphFillLLM(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content: str = Field(description="Nội dung NGUYÊN VĂN của đoạn/trang này — KHÔNG dịch/tóm tắt/cắt ngắn.")


_PARAGRAPH_FILL_SPEC = """\
Điều khoản "__CLAUSE_LABEL__" của một hợp đồng tiếng Việt quá dài để bóc trong một lần —
bạn chỉ cần bóc TOÀN VĂN NGUYÊN VẸN của MỘT ĐOẠN (paragraph/trang) dưới đây, KHÔNG phải
toàn bộ điều khoản. Đoạn này sẽ được ghép nối với các đoạn khác theo đúng thứ tự để tạo
thành nội dung đầy đủ.

⚠️ TOÀN VĂN NGUYÊN VẸN: KHÔNG dịch, KHÔNG tóm tắt, KHÔNG cắt ngắn, KHÔNG thêm/bớt câu.
  Giữ nguyên mọi lettered items (a, b, c...), số liệu, bảng (markdown table nếu có).
⚠️ KHÔNG lặp lại tiêu đề điều khoản trong content — chỉ nội dung của đoạn này.
__CONTINUATION_NOTE__
ĐOẠN VĂN BẢN:
__CHUNK_TEXT__

Trả về JSON đúng schema, không thêm văn bản ngoài JSON.
"""

_CONTINUATION_NOTE = """\
⚠️ ĐOẠN NÀY LÀ PHẦN TIẾP THEO của đoạn trước — có thể bắt đầu/kết thúc giữa câu, giữa
  mục a)/b)/c), hoặc giữa hàng của bảng. TUYỆT ĐỐI KHÔNG tự thêm từ nối, KHÔNG hoàn
  chỉnh câu bị cắt, KHÔNG lặp lại phần đã có ở đoạn trước — chỉ bóc CHÍNH XÁC văn bản
  xuất hiện trong đoạn này, kể cả khi nó bắt đầu/kết thúc dở dang (D-06: không được
  sửa nội dung pháp lý để "làm mượt" chỗ cắt).
"""


def build_paragraph_fill_instruction(
    clause_num: Optional[str],
    clause_title: Optional[str],
    chunk_text: str,
    *,
    is_continuation: bool = False,
) -> str:
    """Pure prompt builder for Pass 3 (unit-testable without SDK/keys).

    `is_continuation`: set True when Backend's WS2b runner knows this chunk isn't the
    first for the clause (i.e. it may start/end mid-sentence). Warns the model against
    "smoothing over" the cut — a subtle D-06 content-alteration risk if left unstated
    (#456 review finding: chunk boundaries had no continuation marker)."""
    label = " — ".join(p for p in (clause_num, clause_title) if p) or "(không số hiệu)"
    note = _CONTINUATION_NOTE if is_continuation else ""
    return (
        _PARAGRAPH_FILL_SPEC.replace("__CLAUSE_LABEL__", label)
        .replace("__CONTINUATION_NOTE__", note)
        .replace("__CHUNK_TEXT__", chunk_text)
    )


async def fill_paragraph(
    clause_num: Optional[str],
    clause_title: Optional[str],
    chunk_text: str,
    *,
    is_continuation: bool = False,
    api_key: str | None = None,
) -> ParagraphFillResult:
    """Pass 3: fill one paragraph/page chunk of a single clause whose full verbatim
    body alone exceeds Pass 2's per-section budget. Called once per chunk; Backend's
    WS2b runner concatenates the ordered results into the clause's final content.

    Pass `is_continuation=True` for every chunk after the first for a given clause —
    see `build_paragraph_fill_instruction`."""
    if not chunk_text or not chunk_text.strip():
        return ParagraphFillResult(provider="none", warnings=["empty_chunk_text"])

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return ParagraphFillResult(provider=_MODEL, warnings=["google-genai SDK not installed"])

    client = genai.Client(
        api_key=api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    )
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_GUARDRAIL,
        response_mime_type="application/json",
        response_schema=_ParagraphFillLLM,
        temperature=0.0,
        max_output_tokens=_PARAGRAPH_MAX_OUTPUT_TOKENS,
    )

    try:
        response = await client.aio.models.generate_content(
            model=_MODEL,
            contents=[types.Part.from_text(
                text=build_paragraph_fill_instruction(
                    clause_num, clause_title, chunk_text, is_continuation=is_continuation
                )
            )],
            config=config,
        )
    except Exception as exc:  # noqa: BLE001 - report, never fabricate
        return ParagraphFillResult(provider=_MODEL, warnings=[f"paragraph fill call failed: {type(exc).__name__}: {exc}"])

    parsed = getattr(response, "parsed", None)
    fr = finish_reason(response)
    truncated = fr == "MAX_TOKENS"
    if not isinstance(parsed, _ParagraphFillLLM):
        return ParagraphFillResult(
            provider=_MODEL, truncated=truncated,
            warnings=[f"paragraph fill returned no structured output (finish_reason={fr})"],
        )

    meta = getattr(response, "usage_metadata", None)
    usage = TokenUsage(
        input_tokens=getattr(meta, "prompt_token_count", 0) or 0,
        output_tokens=getattr(meta, "candidates_token_count", 0) or 0,
    )
    cost = cost_vnd(usage, _IN_USD_PER_MTOK, _OUT_USD_PER_MTOK)
    warnings = (
        ["Paragraph fill hit MAX_TOKENS — chunk still too large, split further."] if truncated else []
    )
    if fr not in (None, "STOP", "MAX_TOKENS"):
        warnings.append(f"unexpected finish_reason={fr} despite successful parse")
    return ParagraphFillResult(
        content=parsed.content, provider=_MODEL, model=_MODEL, cost_vnd=cost,
        truncated=truncated, warnings=warnings,
    )
