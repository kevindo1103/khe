"""Pure unit tests for two-pass map-reduce extraction (#448) — no API keys / SDKs
required. Covers prompt builders (pure functions) and no-op guards; the actual
Gemini calls are exercised by benchmark scripts on staging, not here (same split as
test_remap.py / test_rederive.py for the other extraction sub-modules).

Run: `python -m backend.modules.extraction.tests.test_two_pass` or `pytest`.
"""

from __future__ import annotations

import asyncio

from ..two_pass import (
    FillClauseResult,
    ParagraphFillResult,
    SkeletonClauseResult,
    SkeletonResult,
    _FillClauseLLM,
    _FillExtractionLLM,
    _SkeletonClauseLLM,
    _SkeletonExtractionLLM,
    _clause_manifest,
    _to_fill_result,
    _to_skeleton_result,
    build_fill_instruction,
    build_paragraph_fill_instruction,
    build_skeleton_instruction,
    extract_skeleton,
    fill_paragraph,
    fill_section,
)


# --- Pass 1: skeleton prompt -------------------------------------------------

def test_skeleton_instruction_embeds_ocr_text() -> None:
    instr = build_skeleton_instruction("Điều 1. ABC\n1.1 xyz")
    assert "Điều 1. ABC" in instr and "1.1 xyz" in instr


def test_skeleton_instruction_no_content_ask() -> None:
    instr = build_skeleton_instruction("bất kỳ")
    assert "KHÔNG trả về nội dung" in instr
    assert "KHÔNG TRẢ VỀ NỘI DUNG" in instr


def test_skeleton_instruction_covers_phu_luc_and_no_flat_rules() -> None:
    instr = build_skeleton_instruction("bất kỳ")
    assert "PL-" in instr and "Phụ lục" in instr
    assert "TÁCH SUB-CLAUSES" in instr


def test_skeleton_instruction_handles_literal_json_braces() -> None:
    """.replace()-based substitution must not choke on the literal {...} JSON
    examples embedded in the spec (the #445-style .format() bug this avoids)."""
    instr = build_skeleton_instruction('{"already": "json-like text"}')
    assert '{"already": "json-like text"}' in instr


def test_skeleton_result_normalizes_llm_output() -> None:
    parsed = _SkeletonExtractionLLM(
        clauses=[
            _SkeletonClauseLLM(num="Điều 10", title="CHUYỂN NHƯỢNG", level=1, clause_path="10"),
            _SkeletonClauseLLM(num="10.1", title=None, level=2, clause_path="10.1"),
        ]
    )
    result = _to_skeleton_result(parsed, provider="gemini-2.5-flash", cost=12.3, truncated=False)
    assert len(result.clauses) == 2
    assert result.clauses[0].clause_path == "10"
    assert result.clauses[1].title is None  # unnamed sub-clause stays null, not fabricated
    assert result.cost_vnd == 12.3
    assert not result.truncated and not result.warnings


def test_skeleton_result_truncated_carries_warning() -> None:
    parsed = _SkeletonExtractionLLM(clauses=[])
    result = _to_skeleton_result(parsed, provider="gemini-2.5-flash", cost=0.0, truncated=True)
    assert result.truncated and result.warnings


def test_extract_skeleton_empty_input_is_noop() -> None:
    result = asyncio.run(extract_skeleton(""))
    assert result.provider == "none"
    assert result.warnings == ["empty_ocr_text"]
    assert result.clauses == []


# --- Pass 2: content-fill prompt --------------------------------------------

def test_clause_manifest_lists_every_clause_path() -> None:
    clauses = [
        SkeletonClauseResult(num="Điều 1", title="ABC", level=1, clause_path="1"),
        SkeletonClauseResult(num="PL-1.1", title=None, level=2, clause_path="PL-1.1"),
    ]
    manifest = _clause_manifest(clauses)
    assert 'clause_path="1"' in manifest
    assert 'clause_path="PL-1.1"' in manifest
    assert "(không số hiệu)" not in manifest  # both entries have a num/title label


def test_clause_manifest_handles_missing_label() -> None:
    manifest = _clause_manifest([SkeletonClauseResult(num=None, title=None, clause_path="1")])
    assert "(không số hiệu)" in manifest


def test_fill_instruction_embeds_manifest_and_section_text() -> None:
    clauses = [SkeletonClauseResult(num="Điều 1", title="ABC", level=1, clause_path="1")]
    instr = build_fill_instruction("nội dung section...", clauses)
    assert 'clause_path="1"' in instr
    assert "nội dung section..." in instr
    assert "TOÀN VĂN" in instr


def test_fill_instruction_handles_literal_json_braces() -> None:
    clauses = [SkeletonClauseResult(clause_path="1")]
    instr = build_fill_instruction('text with {braces} in it', clauses)
    assert "text with {braces} in it" in instr


def test_fill_result_normalizes_llm_output() -> None:
    parsed = _FillExtractionLLM(
        clauses=[_FillClauseLLM(clause_path="1", content="Nội dung điều 1 đầy đủ.")]
    )
    result = _to_fill_result(parsed, provider="gemini-2.5-flash", cost=5.0, truncated=False)
    assert result.clauses[0].clause_path == "1"
    assert result.clauses[0].content == "Nội dung điều 1 đầy đủ."
    assert not result.truncated


def test_fill_result_truncated_signals_paragraph_split() -> None:
    parsed = _FillExtractionLLM(clauses=[])
    result = _to_fill_result(parsed, provider="gemini-2.5-flash", cost=0.0, truncated=True)
    assert result.truncated
    assert "paragraph-split" in result.warnings[0]


def test_fill_section_empty_skeleton_is_noop() -> None:
    result = asyncio.run(fill_section("text", []))
    assert result.provider == "none"
    assert result.warnings == ["empty_skeleton"]


def test_fill_section_empty_text_is_noop() -> None:
    result = asyncio.run(fill_section("", [SkeletonClauseResult(clause_path="1")]))
    assert result.provider == "none"
    assert result.warnings == ["empty_section_text"]


# --- Pass 3: paragraph-split prompt -----------------------------------------

def test_paragraph_fill_instruction_labels_clause() -> None:
    instr = build_paragraph_fill_instruction("Điều 5", "Bồi thường", "đoạn văn bản dài...")
    assert "Điều 5 — Bồi thường" in instr
    assert "đoạn văn bản dài..." in instr


def test_paragraph_fill_instruction_handles_missing_label() -> None:
    instr = build_paragraph_fill_instruction(None, None, "text")
    assert "(không số hiệu)" in instr


def test_paragraph_fill_instruction_handles_literal_json_braces() -> None:
    instr = build_paragraph_fill_instruction("Điều 1", None, '{"x": 1}')
    assert '{"x": 1}' in instr


def test_fill_paragraph_empty_chunk_is_noop() -> None:
    result = asyncio.run(fill_paragraph("Điều 1", None, ""))
    assert result.provider == "none"
    assert result.warnings == ["empty_chunk_text"]


def test_public_result_models_from_attributes() -> None:
    """Sanity check the public models Backend's WS2b runner will consume."""
    assert SkeletonResult().clauses == []
    assert FillClauseResult(clause_path="1", content="x").content == "x"
    assert ParagraphFillResult(content="y").content == "y"


def _run_all() -> None:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")


if __name__ == "__main__":
    _run_all()
