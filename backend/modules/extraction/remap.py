"""Clause remap — text-only re-extraction of type-specific fields into a corrected
`doc_type_group`, WITHOUT a new vision call (#258).

When Gemini misclassifies `doc_type_group` in the original vision call, the wrong
type-specific field set is extracted. Re-running vision costs ~177đ + a quota slot.
But the first call already captured the full document text as `clauses[]` (DEC-026),
so we can re-map into the correct schema from that text alone — a text-only LLM call
at ~2-3đ, no quota, <2s, no file needed.

This module owns the KHE_AI half of #258. Backend (`POST /documents/{id}/remap-type`)
fetches `clauses[]`, calls `remap_type()`, then does the atomic DB ops (whitelist
delete of old type-specific Terms, insert new with `source="remap"`, update the
`doc_type_group` Term, re-derive obligations, reset `confirmed_by_user_at`, Event log).

Guardrails (same as vision extraction):
- D-06 / D-08: read-only, `value=None` when the field isn't in the clauses — never guessed.
- Anchors (#230): text-only can't give `page_num`/`bbox`, but each clause carries its
  `clause_num`, so a remapped field CAN carry `ref` ("Điều 3"). `page_num` stays None
  (honest about the limitation — no fabricated page).

Interface locked by PM on #258:
    remap_type(clauses, target_type) -> RemapResult
      RemapResult.fields: dict[str, RemapFieldResult]   # ONLY keys of target_type
      RemapFieldResult: {value, ref, page_num=None, confidence, needs_review}
"""

from __future__ import annotations

import os
import time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .prompts import SYSTEM_GUARDRAIL, _TYPE_SPECIFIC_DESC
from .providers.base import cost_vnd
from .schemas import ClauseItem, TYPE_SPECIFIC_FIELDS, TokenUsage, _clamp_confidence

# Same model + pricing as GeminiFlashProvider, but text-only (no image part).
_REMAP_MODEL = "gemini-2.5-flash"
_IN_USD_PER_MTOK = 0.30   # verified 2026-06-11 ($0.30/$2.50 per 1M)
_OUT_USD_PER_MTOK = 2.50


# --- Output contract (PM-ratified #258) ------------------------------------
class RemapFieldResult(BaseModel):
    """One remapped type-specific field. `page_num` is always None (text-only); `ref`
    carries the source clause_num when the value was located in a numbered clause."""

    model_config = ConfigDict(from_attributes=True)

    value: Optional[str] = None
    ref: Optional[str] = None
    page_num: Optional[int] = None   # text-only → always None (honest, no fabricated page)
    confidence: float = 0.0
    needs_review: bool = True


class RemapResult(BaseModel):
    """Return value of `remap_type()`. Backend reads `.fields` (insert as Terms with
    source='remap'), `.provider`/`.cost_vnd` (cost tracking #255). `warnings` is
    non-empty on the no-op paths (empty clauses / target without type-specific fields)."""

    model_config = ConfigDict(from_attributes=True)

    fields: dict[str, RemapFieldResult] = Field(default_factory=dict)
    provider: str = ""
    cost_vnd: float = 0.0
    warnings: list[str] = Field(default_factory=list)


# --- LLM-facing structured-output schema (lean → Claude/Gemini both safe) ---
class _RemapFieldLLM(BaseModel):
    """One field the model returns. Lean (no page_num slot) — text-only never has a page,
    and a smaller schema keeps us well inside any grammar budget."""

    model_config = ConfigDict(from_attributes=True)

    key: str = Field(description="Canonical key của trường type-specific, vd 'dia_chi_tai_san'.")
    value: Optional[str] = Field(
        default=None, description="Giá trị NGUYÊN VĂN trên tài liệu, hoặc null nếu không có trong các điều khoản."
    )
    ref: Optional[str] = Field(
        default=None, description='Số hiệu điều/khoản chứa value (vd "Điều 3"), lấy từ clause_num. null nếu không rõ.'
    )
    confidence: float = Field(default=0.0, description="Độ tin cậy 0..1.")
    needs_review: bool = Field(default=True, description="True nếu cần người kiểm tra.")

    @field_validator("confidence")
    @classmethod
    def _clamp(cls, v: float) -> float:
        return _clamp_confidence(v)


class _RemapExtractionLLM(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fields: list[_RemapFieldLLM] = Field(default_factory=list)


# --- Prompt construction (pure, unit-testable) -----------------------------
def _clauses_to_text(clauses: list[ClauseItem]) -> str:
    """Render clauses[] as plain text for the prompt. Keeps clause_num so the model can
    cite it back as `ref`."""
    lines: list[str] = []
    for c in clauses:
        num = (c.num or "").strip()
        title = (c.title or "").strip()
        header = " — ".join(p for p in (num, title) if p) or "(không số hiệu)"
        lines.append(f"[{header}]\n{c.content}")
    return "\n\n".join(lines)


def build_remap_instruction(target_type: str, clauses_text: str) -> str:
    """Text-only remap instruction. Lists ONLY the target type's fields (authoritative
    from TYPE_SPECIFIC_FIELDS) + the human descriptions, then the clause text."""
    keys = TYPE_SPECIFIC_FIELDS.get(target_type, ())
    desc = _TYPE_SPECIFIC_DESC.get(target_type, "")
    key_lines = "\n".join(f"- {k}" for k in keys)
    return (
        "Dưới đây là TOÀN VĂN các điều khoản của một hợp đồng tiếng Việt đã được bóc tách "
        "từ trước. Hãy bóc các trường THEO LOẠI hợp đồng đã được người dùng xác nhận: "
        f"'{target_type}'.\n\n"
        f"CHỈ bóc đúng các trường sau (KHÔNG thêm trường ngoài danh sách):\n{key_lines}\n"
        f"\nMô tả các trường: {desc}\n\n"
        "Quy tắc (BẮT BUỘC):\n"
        "- value: giá trị NGUYÊN VĂN trên tài liệu. Nếu KHÔNG xuất hiện trong các điều khoản "
        "→ value = null, needs_review = true. TUYỆT ĐỐI không phỏng đoán (D-06/D-08).\n"
        '- ref: số hiệu điều/khoản chứa value (vd "Điều 3"), lấy đúng từ nhãn [..] của điều khoản. '
        "null nếu không xác định được.\n"
        "- confidence ∈ [0,1]; needs_review = true khi confidence < 0.9 hoặc không chắc chắn.\n"
        "- KHÔNG bịa trường, KHÔNG đổi tên key.\n\n"
        f"CÁC ĐIỀU KHOẢN:\n{clauses_text}\n\n"
        "Trả về JSON đúng schema, không thêm văn bản ngoài JSON."
    )


def _to_remap_result(
    parsed: _RemapExtractionLLM,
    target_type: str,
    *,
    provider: str,
    cost: float,
) -> RemapResult:
    """Normalize LLM output → RemapResult. Returns a row for EVERY target field (D-07:
    the review UI needs a row to fill even when the model found nothing), keyed to
    TYPE_SPECIFIC_FIELDS[target_type]; drops any key the model invented outside the set."""
    valid = TYPE_SPECIFIC_FIELDS.get(target_type, ())
    by_key = {f.key: f for f in parsed.fields if f.key in valid}

    fields: dict[str, RemapFieldResult] = {}
    for key in valid:
        f = by_key.get(key)
        if f is None:
            fields[key] = RemapFieldResult()  # not returned → null row, needs_review=True
        else:
            fields[key] = RemapFieldResult(
                value=f.value,
                ref=f.ref,
                page_num=None,  # text-only → always None
                confidence=f.confidence,
                needs_review=f.needs_review,
            )
    return RemapResult(fields=fields, provider=provider, cost_vnd=cost)


async def remap_type(
    clauses: list[ClauseItem],
    target_type: str,
    *,
    api_key: str | None = None,
) -> RemapResult:
    """Re-extract `target_type`'s type-specific fields from `clauses[]` (text-only).

    No-op guards (no LLM call, cost 0):
    - empty clauses → Backend should already 409; we mirror it so a bad caller can't
      burn tokens on empty input (and the model can't fabricate from nothing).
    - target_type has no type-specific fields (e.g. "other"/"dan_su") → nothing to
      extract; remap just clears the old type-specific Terms on the Backend side.
    """
    if not clauses:
        return RemapResult(provider="none", cost_vnd=0.0, warnings=["no_clauses"])
    if not TYPE_SPECIFIC_FIELDS.get(target_type):
        return RemapResult(
            provider="none", cost_vnd=0.0, warnings=["no_type_specific_fields_for_target"]
        )

    instruction = build_remap_instruction(target_type, _clauses_to_text(clauses))

    # Lazy import — keep the package importable without the SDK (CI `import` + tests).
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return RemapResult(
            provider="gemini_flash_text",
            cost_vnd=0.0,
            warnings=["google-genai SDK not installed"],
        )

    client = genai.Client(
        api_key=api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    )
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_GUARDRAIL,
        response_mime_type="application/json",
        response_schema=_RemapExtractionLLM,
        temperature=0.0,
    )

    started = time.perf_counter()
    try:
        response = await client.aio.models.generate_content(
            model=_REMAP_MODEL,
            contents=[types.Part.from_text(text=instruction)],
            config=config,
        )
    except Exception as exc:  # noqa: BLE001 - report, never fabricate
        return RemapResult(
            provider="gemini_flash_text",
            cost_vnd=0.0,
            warnings=[f"remap call failed: {type(exc).__name__}: {exc}"],
        )

    parsed = getattr(response, "parsed", None)
    if not isinstance(parsed, _RemapExtractionLLM):
        return RemapResult(
            provider="gemini_flash_text",
            cost_vnd=0.0,
            warnings=["remap returned no structured output"],
        )

    meta = getattr(response, "usage_metadata", None)
    usage = TokenUsage(
        input_tokens=getattr(meta, "prompt_token_count", 0) or 0,
        output_tokens=getattr(meta, "candidates_token_count", 0) or 0,
    )
    cost = cost_vnd(usage, _IN_USD_PER_MTOK, _OUT_USD_PER_MTOK)
    return _to_remap_result(parsed, target_type, provider="gemini_flash_text", cost=cost)
