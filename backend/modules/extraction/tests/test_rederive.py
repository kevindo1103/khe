"""Tests for clause-scoped obligation re-derive (#304) — text-only re-extraction
of obligations from specific clauses.

Cover the pure, key-free logic: prompt construction, output normalization,
derived_from stamping, and the no-op guard. The live Gemini text call is NOT
exercised here (no key in CI).
"""

from __future__ import annotations

import asyncio

import pytest

from modules.extraction.rederive import (
    RederiveResult,
    _RederiveExtractionLLM,
    _RederiveObligationLLM,
    _clauses_to_text,
    _to_rederive_result,
    build_rederive_instruction,
    rederive_obligations,
)
from modules.extraction.schemas import ClauseItem, ObligationScheduleItem

_CLAUSES = [
    ClauseItem(
        num="Điều 5",
        title="Thanh toán",
        content="Bên B thanh toán cho Bên A theo 3 đợt: Đợt 1 — 50% giá trị HĐ trong vòng "
        "05 ngày kể từ ngày ký; Đợt 2 — 30% sau khi bàn giao; Đợt 3 — 20% sau nghiệm thu.",
    ),
    ClauseItem(
        num="Điều 8",
        title="Bảo hành",
        content="Bên A bảo hành 12 tháng kể từ ngày nghiệm thu.",
    ),
]


def test_clauses_to_text_renders_headers():
    txt = _clauses_to_text(_CLAUSES)
    assert "[Điều 5 — Thanh toán]" in txt
    assert "[Điều 8 — Bảo hành]" in txt
    assert "50% giá trị HĐ" in txt
    assert "12 tháng" in txt


def test_clauses_to_text_handles_missing_num():
    txt = _clauses_to_text([ClauseItem(num=None, title=None, content="Nội dung.")])
    assert "(không số hiệu)" in txt


def test_build_instruction_contains_key_rules():
    ins = build_rederive_instruction(_clauses_to_text(_CLAUSES))
    assert "source_clause_num" in ins
    assert "D-06" in ins or "D-08" in ins
    assert "obligation_type" in ins
    assert "Điều 5" in ins
    assert "Điều 8" in ins


def test_to_rederive_result_stamps_derived_from_original():
    parsed = _RederiveExtractionLLM(
        obligations=[
            _RederiveObligationLLM(
                obligation_type="payment",
                description="Đợt 1 — 50%",
                due_date="2026-04-01",
                source_clause_num="Điều 5",
            ),
            _RederiveObligationLLM(
                obligation_type="warranty",
                description="Bảo hành 12 tháng",
                trigger="event",
                trigger_condition="sau khi nghiệm thu",
                source_clause_num="Điều 8",
            ),
        ]
    )
    res = _to_rederive_result(parsed, derived_from="original", provider="gemini_flash_text", cost=2.5)
    assert len(res.obligations) == 2
    assert all(o.derived_from == "original" for o in res.obligations)
    assert res.obligations[0].source_clause_num == "Điều 5"
    assert res.obligations[0].obligation_type == "payment"
    assert res.obligations[1].source_clause_num == "Điều 8"
    assert res.obligations[1].trigger == "event"
    assert res.provider == "gemini_flash_text"
    assert res.cost_vnd == 2.5


def test_to_rederive_result_stamps_derived_from_user_edit():
    parsed = _RederiveExtractionLLM(
        obligations=[
            _RederiveObligationLLM(
                obligation_type="payment",
                description="Đợt 1 — 60%",
                due_date="2026-05-01",
                source_clause_num="Điều 5",
            ),
        ]
    )
    res = _to_rederive_result(parsed, derived_from="user_edit", provider="gemini_flash_text", cost=1.0)
    assert len(res.obligations) == 1
    assert res.obligations[0].derived_from == "user_edit"
    assert res.obligations[0].description == "Đợt 1 — 60%"


def test_to_rederive_result_empty_obligations():
    parsed = _RederiveExtractionLLM(obligations=[])
    res = _to_rederive_result(parsed, derived_from="original", provider="gemini_flash_text", cost=0.5)
    assert res.obligations == []
    assert res.cost_vnd == 0.5


def test_to_rederive_result_coerces_unknown_obligation_type():
    parsed = _RederiveExtractionLLM(
        obligations=[
            _RederiveObligationLLM(
                obligation_type="INVENTED_TYPE",
                description="Some obligation",
                source_clause_num="Điều 1",
            ),
        ]
    )
    res = _to_rederive_result(parsed, derived_from="original", provider="p", cost=0.0)
    assert res.obligations[0].obligation_type == "other"


def test_rederive_empty_clauses_is_noop():
    res = asyncio.run(rederive_obligations([]))
    assert res.obligations == []
    assert res.warnings == ["no_clauses"]
    assert res.cost_vnd == 0.0
    assert res.provider == "none"


def test_rederive_result_shape():
    r = RederiveResult(
        obligations=[
            ObligationScheduleItem(
                obligation_type="payment",
                description="Test",
                source_clause_num="Điều 1",
                derived_from="original",
            )
        ],
        provider="gemini_flash_text",
        cost_vnd=2.0,
    )
    dumped = r.model_dump()
    assert set(dumped) == {"obligations", "provider", "cost_vnd", "warnings"}
    assert len(dumped["obligations"]) == 1
    assert dumped["obligations"][0]["source_clause_num"] == "Điều 1"
    assert dumped["obligations"][0]["derived_from"] == "original"


def test_obligation_schedule_item_has_new_fields():
    """Verify ObligationScheduleItem schema carries source_clause_num + derived_from."""
    item = ObligationScheduleItem(
        obligation_type="delivery",
        description="Giao hàng đợt 1",
        source_clause_num="Điều 3",
        derived_from="user_edit",
    )
    assert item.source_clause_num == "Điều 3"
    assert item.derived_from == "user_edit"
    dumped = item.model_dump()
    assert "source_clause_num" in dumped
    assert "derived_from" in dumped


def test_obligation_schedule_item_defaults():
    """source_clause_num defaults None, derived_from defaults 'original'."""
    item = ObligationScheduleItem(
        obligation_type="payment",
        description="Test",
    )
    assert item.source_clause_num is None
    assert item.derived_from == "original"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q"]))
