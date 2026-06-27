"""Clause-scoped obligation re-derive — text-only re-extraction of obligations
from specific clauses, WITHOUT a new vision call (#304 / DEC-048 §13).

When a user edits a clause and triggers "Khế đọc lại", we need to re-derive
obligations ONLY from the edited clause(s), not from the entire document.
This avoids churn on untouched obligations (§G1) and respects manual-source
precedence (§G2).

Architecture mirrors `remap.py`: text-only Gemini Flash call (~2-3đ), no quota,
no file needed. Input = clause(s) text; output = `ObligationScheduleItem[]` with
`source_clause_num` provenance and `derived_from` flag.

Guardrails (same as remap + vision extraction):
- D-06 / D-08: read-only, never fabricate obligations or dates.
- §G4 provenance: every obligation carries `source_clause_num` + `derived_from`
  ("original" vs "user_edit") so audit trail is honest about origin.

Interface locked by PM on #300/#304:
    rederive_obligations(clauses, *, derived_from="original") -> RederiveResult
      RederiveResult.obligations: list[ObligationScheduleItem]
      RederiveResult.provider, .cost_vnd, .warnings
"""

from __future__ import annotations

import os
import time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .prompts import SYSTEM_GUARDRAIL
from .providers.base import cost_vnd
from .schemas import ClauseItem, ObligationScheduleItem, TokenUsage, _clamp_confidence

_REDERIVE_MODEL = "gemini-2.5-flash"
_IN_USD_PER_MTOK = 0.30
_OUT_USD_PER_MTOK = 2.50


# --- Output contract (#304) --------------------------------------------------
class RederiveResult(BaseModel):
    """Return value of `rederive_obligations()`. Backend reads `.obligations`
    (insert/diff against existing), `.provider`/`.cost_vnd` (cost tracking)."""

    model_config = ConfigDict(from_attributes=True)

    obligations: list[ObligationScheduleItem] = Field(default_factory=list)
    provider: str = ""
    cost_vnd: float = 0.0
    warnings: list[str] = Field(default_factory=list)


# --- LLM-facing structured-output schema (lean) ------------------------------
class _RederiveObligationLLM(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    obligation_type: str = Field(
        description="Loại: payment | delivery | handover | expiration | renewal | review | warranty | other."
    )
    description: str = Field(
        description='Diễn giải nghĩa vụ, nguyên văn — vd "Đợt 2 — giao 40% hàng".'
    )
    amount_raw: Optional[str] = Field(
        default=None,
        description='Số tiền/giá trị NGUYÊN VĂN, KHÔNG parse — vd "40%", "150.000.000 VND". null nếu không có.',
    )
    due_date: Optional[str] = Field(
        default=None,
        description="Ngày đến hạn — ISO yyyy-mm-dd nếu rõ. null nếu trigger=event (D-08).",
    )
    recurrence: Optional[str] = Field(
        default=None,
        description='"monthly" | "quarterly" | "yearly" | null.',
    )
    obligor: Optional[str] = Field(
        default=None,
        description='Bên THỰC HIỆN nghĩa vụ — tên hoặc vai trò (vd "Bên B"). null nếu không rõ.',
    )
    series_id: Optional[str] = Field(default=None, description="Cùng chuỗi đợt → cùng series_id.")
    milestone_index: Optional[int] = Field(default=None, description="Số thứ tự đợt (1-based).")
    milestone_total: Optional[int] = Field(default=None, description="Tổng số đợt.")
    trigger: str = Field(default="date", description='"date" hoặc "event".')
    trigger_condition: Optional[str] = Field(
        default=None, description="Điều kiện kích hoạt NGUYÊN VĂN nếu trigger=event."
    )
    trigger_delay_days: Optional[int] = Field(
        default=None, description="Số ngày trễ sau sự kiện."
    )
    source_clause_num: Optional[str] = Field(
        default=None,
        description='Số hiệu điều/khoản sinh nghĩa vụ, vd "Điều 5". null nếu không xác định.',
    )

    @field_validator("obligation_type")
    @classmethod
    def _coerce_type(cls, v: str) -> str:
        valid = {"payment", "delivery", "handover", "expiration", "renewal", "review", "warranty", "other"}
        return v if v in valid else "other"


class _RederiveExtractionLLM(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    obligations: list[_RederiveObligationLLM] = Field(default_factory=list)


# --- Prompt construction (pure, unit-testable) --------------------------------
def _clauses_to_text(clauses: list[ClauseItem]) -> str:
    lines: list[str] = []
    for c in clauses:
        num = (c.num or "").strip()
        title = (c.title or "").strip()
        header = " — ".join(p for p in (num, title) if p) or "(không số hiệu)"
        lines.append(f"[{header}]\n{c.content}")
    return "\n\n".join(lines)


def build_rederive_instruction(clauses_text: str) -> str:
    """Text-only instruction: extract all obligations from the given clause(s)."""
    return (
        "Dưới đây là MỘT HOẶC NHIỀU điều khoản từ một hợp đồng tiếng Việt. "
        "Hãy bóc tách MỌI nghĩa vụ có lịch/đợt từ các điều khoản này.\n\n"
        "CHỈ bóc nghĩa vụ RÕ RÀNG trong các điều khoản được cung cấp. "
        "KHÔNG suy luận từ ngữ cảnh bên ngoài. KHÔNG bịa lịch/ngày (D-06/D-08).\n\n"
        "Mỗi nghĩa vụ cần đầy đủ:\n"
        "- obligation_type: payment | delivery | handover | expiration | renewal | review | warranty | other\n"
        '- description: diễn giải NGUYÊN VĂN (vd "Đợt 1 — 50% giá trị HĐ")\n'
        "- amount_raw: số tiền/giá trị NGUYÊN VĂN, KHÔNG parse. null nếu không có\n"
        "- due_date: yyyy-mm-dd nếu có ngày rõ. null nếu trigger=event\n"
        "- obligor: bên THỰC HIỆN, tên hoặc vai trò như văn bản. null nếu không rõ\n"
        '- trigger: "date" hoặc "event"\n'
        "- trigger_condition: điều kiện NGUYÊN VĂN nếu trigger=event\n"
        "- trigger_delay_days: số ngày trễ sau sự kiện nếu nêu rõ\n"
        "- series_id, milestone_index, milestone_total: cho chuỗi nhiều đợt\n"
        "- recurrence: chu kỳ lặp nếu có\n"
        "- source_clause_num: số hiệu điều/khoản SINH nghĩa vụ — lấy đúng từ nhãn [..] "
        'ở đầu điều khoản (vd "Điều 5", "Khoản 3.2"). BẮT BUỘC khi có.\n\n'
        "Nếu KHÔNG CÓ nghĩa vụ nào trong các điều khoản → obligations = [].\n\n"
        f"CÁC ĐIỀU KHOẢN:\n{clauses_text}\n\n"
        "Trả về JSON đúng schema, không thêm văn bản ngoài JSON."
    )


def _to_rederive_result(
    parsed: _RederiveExtractionLLM,
    *,
    derived_from: str,
    provider: str,
    cost: float,
) -> RederiveResult:
    """Normalize LLM output → RederiveResult. Stamps `derived_from` on every item."""
    items: list[ObligationScheduleItem] = []
    for o in parsed.obligations:
        items.append(ObligationScheduleItem(
            obligation_type=o.obligation_type,
            description=o.description,
            amount_raw=o.amount_raw,
            due_date=o.due_date,
            recurrence=o.recurrence,
            obligor=o.obligor,
            series_id=o.series_id,
            milestone_index=o.milestone_index,
            milestone_total=o.milestone_total,
            trigger=o.trigger,
            trigger_condition=o.trigger_condition,
            trigger_delay_days=o.trigger_delay_days,
            source_clause_num=o.source_clause_num,
            derived_from=derived_from,
        ))
    return RederiveResult(obligations=items, provider=provider, cost_vnd=cost)


async def rederive_obligations(
    clauses: list[ClauseItem],
    *,
    derived_from: str = "original",
    api_key: str | None = None,
) -> RederiveResult:
    """Re-derive obligations from clause(s) text-only (~2-3đ, no vision).

    `derived_from` stamps every output obligation:
    - "original" — clauses are from the original PDF extraction
    - "user_edit" — clauses contain user-edited content (§G4 provenance)

    No-op guard: empty clauses → no LLM call (same as remap_type).
    """
    if not clauses:
        return RederiveResult(provider="none", cost_vnd=0.0, warnings=["no_clauses"])

    instruction = build_rederive_instruction(_clauses_to_text(clauses))

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return RederiveResult(
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
        response_schema=_RederiveExtractionLLM,
        temperature=0.0,
    )

    try:
        response = await client.aio.models.generate_content(
            model=_REDERIVE_MODEL,
            contents=[types.Part.from_text(text=instruction)],
            config=config,
        )
    except Exception as exc:  # noqa: BLE001
        return RederiveResult(
            provider="gemini_flash_text",
            cost_vnd=0.0,
            warnings=[f"rederive call failed: {type(exc).__name__}: {exc}"],
        )

    parsed = getattr(response, "parsed", None)
    if not isinstance(parsed, _RederiveExtractionLLM):
        return RederiveResult(
            provider="gemini_flash_text",
            cost_vnd=0.0,
            warnings=["rederive returned no structured output"],
        )

    meta = getattr(response, "usage_metadata", None)
    usage = TokenUsage(
        input_tokens=getattr(meta, "prompt_token_count", 0) or 0,
        output_tokens=getattr(meta, "candidates_token_count", 0) or 0,
    )
    cost = cost_vnd(usage, _IN_USD_PER_MTOK, _OUT_USD_PER_MTOK)
    return _to_rederive_result(
        parsed, derived_from=derived_from, provider="gemini_flash_text", cost=cost,
    )
