"""Tests for clause remap (#258) — text-only re-extraction of type-specific fields.

Cover the pure, key-free logic: prompt construction, output normalization, and the
two no-op guards. The live Gemini text call is NOT exercised here (no key in CI) — it
mirrors the vision providers, validated separately by an isolated probe / smoke.
"""

from __future__ import annotations

import asyncio

import pytest

from modules.extraction.remap import (
    RemapFieldResult,
    RemapResult,
    _RemapExtractionLLM,
    _RemapFieldLLM,
    _clauses_to_text,
    _to_remap_result,
    build_remap_instruction,
    remap_type,
)
from modules.extraction.schemas import TYPE_SPECIFIC_FIELDS, ClauseItem

_CLAUSES = [
    ClauseItem(
        num="Điều 1",
        title="Đối tượng hợp đồng",
        content="Bên A cho Bên B thuê văn phòng tại 12 Lý Tự Trọng, Q1, diện tích 120 m2.",
    ),
    ClauseItem(num="Điều 3", title="Giá thuê", content="Giá thuê 25.000.000 VND/tháng."),
]


def test_clauses_to_text_keeps_num_and_content():
    txt = _clauses_to_text(_CLAUSES)
    assert "Điều 1" in txt
    assert "Đối tượng hợp đồng" in txt
    assert "120 m2" in txt
    assert "25.000.000 VND" in txt


def test_clauses_to_text_handles_missing_num_title():
    txt = _clauses_to_text([ClauseItem(num=None, title=None, content="Nội dung không số hiệu.")])
    assert "(không số hiệu)" in txt
    assert "Nội dung không số hiệu." in txt


def test_build_instruction_lists_only_target_keys():
    ins = build_remap_instruction("bat_dong_san", _clauses_to_text(_CLAUSES))
    for k in TYPE_SPECIFIC_FIELDS["bat_dong_san"]:
        assert k in ins
    # A different type's field must NOT leak into the prompt.
    assert "luong_co_ban" not in ins
    # D-06/D-08 guardrail surfaced in the prompt.
    assert "null" in ins and "D-06" in ins


def test_to_remap_result_returns_row_for_every_target_key():
    # Model returned only one of three fields → the other two get null rows (D-07: the
    # review UI still needs a row to fill).
    parsed = _RemapExtractionLLM(
        fields=[
            _RemapFieldLLM(
                key="dia_chi_tai_san",
                value="12 Lý Tự Trọng, Q1",
                ref="Điều 1",
                confidence=0.95,
                needs_review=False,
            )
        ]
    )
    res = _to_remap_result(parsed, "bat_dong_san", provider="gemini_flash_text", cost=2.5)
    assert set(res.fields) == set(TYPE_SPECIFIC_FIELDS["bat_dong_san"])
    got = res.fields["dia_chi_tai_san"]
    assert got.value == "12 Lý Tự Trọng, Q1"
    assert got.ref == "Điều 1"
    assert got.page_num is None  # text-only → never a page
    assert got.needs_review is False
    # Unreturned fields → null row, flagged for review.
    assert res.fields["dien_tich"].value is None
    assert res.fields["dien_tich"].needs_review is True
    assert res.provider == "gemini_flash_text"
    assert res.cost_vnd == 2.5


def test_to_remap_result_drops_invented_keys():
    parsed = _RemapExtractionLLM(
        fields=[
            _RemapFieldLLM(key="dien_tich", value="120", confidence=0.9, needs_review=False),
            _RemapFieldLLM(key="HACKED_KEY", value="x", confidence=1.0),  # not in schema
        ]
    )
    res = _to_remap_result(parsed, "bat_dong_san", provider="gemini_flash_text", cost=1.0)
    assert "HACKED_KEY" not in res.fields
    assert res.fields["dien_tich"].value == "120"


def test_to_remap_result_page_num_always_none_even_if_model_sends_value():
    # Confidence clamping also exercised here (LLM may return >1.0).
    parsed = _RemapExtractionLLM(
        fields=[_RemapFieldLLM(key="dien_tich", value="120", confidence=1.7, needs_review=False)]
    )
    res = _to_remap_result(parsed, "bat_dong_san", provider="p", cost=0.0)
    assert res.fields["dien_tich"].page_num is None
    assert res.fields["dien_tich"].confidence == 1.0  # clamped


def test_remap_empty_clauses_is_noop_no_llm():
    res = asyncio.run(remap_type([], "bat_dong_san"))
    assert res.fields == {}
    assert res.warnings == ["no_clauses"]
    assert res.cost_vnd == 0.0
    assert res.provider == "none"


def test_remap_target_without_type_specific_fields_is_noop():
    # "other" / "dan_su" have no type-specific fields → remap just clears, no LLM call.
    for target in ("other", "dan_su"):
        res = asyncio.run(remap_type(_CLAUSES, target))
        assert res.fields == {}
        assert res.warnings == ["no_type_specific_fields_for_target"]
        assert res.cost_vnd == 0.0


def test_remap_result_shape_matches_pm_contract():
    # RemapResult.fields[k] must expose exactly the PM-ratified keys.
    f = RemapFieldResult(value="x", ref="Điều 2", confidence=0.5, needs_review=True)
    dumped = f.model_dump()
    assert set(dumped) == {"value", "ref", "page_num", "confidence", "needs_review"}
    assert dumped["page_num"] is None
    r = RemapResult(fields={"k": f}, provider="gemini_flash_text", cost_vnd=2.5)
    assert set(r.model_dump()) == {"fields", "provider", "cost_vnd", "warnings"}


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-q"]))
