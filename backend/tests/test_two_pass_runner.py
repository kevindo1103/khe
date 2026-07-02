"""Tests for the two-pass map-reduce orchestrator state machine (#449, WS2-Backend,
mini-sprint #443). Mocks KHE_AI's `fill_section`/`fill_paragraph` — this module owns
persistence/grouping/resumability, not the LLM calls themselves.
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.models.tenant import Clause, Document
from app.services.two_pass_runner import (
    _find_heading,
    _paragraph_chunks,
    group_into_sections,
    persist_skeleton,
    run_content_fill,
    slice_section_text,
)
from modules.extraction.two_pass import (
    FillClauseResult,
    FillResult,
    ParagraphFillResult,
    SkeletonClauseResult,
    SkeletonResult,
)


def _make_doc(db, tenant_id):
    doc = Document(
        tenant_id=tenant_id,
        file_name="contract.pdf",
        file_path=f"{tenant_id}/contract.pdf",
        status="pending",
        is_evidence=False,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _skeleton(items):
    """items: list of (num, title, level, clause_path)."""
    return SkeletonResult(
        clauses=[SkeletonClauseResult(num=n, title=t, level=lv, clause_path=p) for n, t, lv, p in items],
        provider="test",
    )


# ── persist_skeleton ────────────────────────────────────────────────────────


def test_persist_skeleton_creates_clauses_with_skeleton_status(test_tenant, db):
    doc = _make_doc(db, test_tenant)
    skeleton = _skeleton([
        ("Điều 1", "Định nghĩa", 1, "1"),
        ("Điều 2", "Thanh toán", 1, "2"),
    ])

    clauses = persist_skeleton(db, test_tenant, doc.id, skeleton)

    assert len(clauses) == 2
    for c in clauses:
        assert c.content_status == "skeleton"
        assert c.content == ""


def test_persist_skeleton_builds_hierarchy(test_tenant, db):
    """PL- paths and parent linking apply during skeleton persist (reuses #439/#440)."""
    doc = _make_doc(db, test_tenant)
    skeleton = _skeleton([
        ("Phụ lục 1", None, 1, "PL-1"),
        ("Khoản 1", None, 2, "PL-1.1"),
    ])

    clauses = persist_skeleton(db, test_tenant, doc.id, skeleton)
    by_path = {c.clause_path: c for c in clauses}

    assert by_path["PL-1.1"].parent_id == by_path["PL-1"].id


def test_persist_skeleton_replaces_existing(test_tenant, db):
    """Re-running Pass 1 on the same doc replaces prior clauses (idempotent)."""
    doc = _make_doc(db, test_tenant)
    persist_skeleton(db, test_tenant, doc.id, _skeleton([("Điều 1", None, 1, "1")]))
    clauses2 = persist_skeleton(db, test_tenant, doc.id, _skeleton([
        ("Điều 1", None, 1, "1"), ("Điều 2", None, 1, "2"),
    ]))

    all_clauses = db.query(Clause).filter(Clause.document_id == doc.id).all()
    assert len(all_clauses) == 2
    assert len(clauses2) == 2


def test_persist_skeleton_noop_when_pass2_progress_exists(test_tenant, db):
    """persist_skeleton must NOT wipe already-filled clauses (#459 QC finding #1).

    A caller that re-invokes Pass 1 on a doc with existing Pass 2 progress
    (e.g. an unconditional retry entry point) must not lose that progress —
    this is the core resumable/no-re-billing guarantee of the module.
    """
    doc = _make_doc(db, test_tenant)
    clauses = persist_skeleton(db, test_tenant, doc.id, _skeleton([
        ("Điều 1", None, 1, "1"), ("Điều 2", None, 1, "2"),
    ]))
    c1 = next(c for c in clauses if c.clause_path == "1")
    c1.content = "Nội dung đã điền."
    c1.content_status = "filled"
    db.commit()

    # Re-invoking Pass 1 with a DIFFERENT skeleton (as if Gemini returned a
    # slightly different structure on retry) must still be a no-op.
    result = persist_skeleton(db, test_tenant, doc.id, _skeleton([("Điều 1", None, 1, "1")]))

    all_clauses = db.query(Clause).filter(Clause.document_id == doc.id).all()
    assert len(all_clauses) == 2  # unchanged — not wiped down to the 1-item skeleton
    filled = next(c for c in all_clauses if c.clause_path == "1")
    assert filled.content_status == "filled"
    assert filled.content == "Nội dung đã điền."
    assert len(result) == 2


def test_persist_skeleton_noop_when_any_clause_truncated(test_tenant, db):
    """A single 'truncated' clause also counts as Pass 2 progress — no wipe."""
    doc = _make_doc(db, test_tenant)
    clauses = persist_skeleton(db, test_tenant, doc.id, _skeleton([("Điều 1", None, 1, "1")]))
    clauses[0].content_status = "truncated"
    db.commit()

    persist_skeleton(db, test_tenant, doc.id, _skeleton([]))

    all_clauses = db.query(Clause).filter(Clause.document_id == doc.id).all()
    assert len(all_clauses) == 1
    assert all_clauses[0].content_status == "truncated"


def test_persist_skeleton_returns_stub_parents(test_tenant, db):
    """Synthesized stub parents (from build_clause_hierarchy) appear in the
    return value, not just in the DB (#459 QC finding #7)."""
    doc = _make_doc(db, test_tenant)
    # "3.2" with no parent "3" in the skeleton — a stub for "3" gets synthesized.
    clauses = persist_skeleton(db, test_tenant, doc.id, _skeleton([("Khoản 3.2", None, 2, "3.2")]))

    paths = {c.clause_path for c in clauses}
    assert "3" in paths  # the synthesized stub is present in the return value
    assert "3.2" in paths


# ── group_into_sections ─────────────────────────────────────────────────────


def test_group_into_sections_groups_by_top_level(test_tenant, db):
    doc = _make_doc(db, test_tenant)
    clauses = persist_skeleton(db, test_tenant, doc.id, _skeleton([
        ("Điều 1", None, 1, "1"),
        ("Khoản 1.1", None, 2, "1.1"),
        ("Điều 2", None, 1, "2"),
    ]))

    sections = group_into_sections(clauses)

    assert len(sections) == 2
    assert len(sections[0]) == 2  # Điều 1 + its sub-clause
    assert len(sections[1]) == 1  # Điều 2 alone


def test_group_into_sections_phu_luc_separate_from_dieu(test_tenant, db):
    doc = _make_doc(db, test_tenant)
    clauses = persist_skeleton(db, test_tenant, doc.id, _skeleton([
        ("Điều 1", None, 1, "1"),
        ("Phụ lục 1", None, 1, "PL-1"),
        ("Khoản 1", None, 2, "PL-1.1"),
    ]))

    sections = group_into_sections(clauses)

    assert len(sections) == 2
    pl_section = next(s for s in sections if s[0].clause_path == "PL-1")
    assert len(pl_section) == 2


# ── slice_section_text ───────────────────────────────────────────────────────


def test_slice_section_text_splits_by_heading():
    ocr = "Điều 1: Nội dung 1.\n\nĐiều 2: Nội dung 2."

    class _Fake:
        def __init__(self, num):
            self.clause_num = num

    sections = [[_Fake("Điều 1")], [_Fake("Điều 2")]]
    slices = slice_section_text(ocr, sections)

    assert len(slices) == 2
    assert slices[0].startswith("Điều 1")
    assert "Nội dung 1" in slices[0]
    assert "Nội dung 2" not in slices[0]
    assert slices[1].startswith("Điều 2")


def test_slice_section_text_falls_back_gracefully_on_missing_heading():
    """A heading that can't be located degrades to the remaining text, not a crash."""
    ocr = "Some OCR text without matching headings."

    class _Fake:
        def __init__(self, num):
            self.clause_num = num

    sections = [[_Fake("Điều 99")]]
    slices = slice_section_text(ocr, sections)

    assert len(slices) == 1
    assert slices[0] == ocr


# ── _find_heading ─────────────────────────────────────────────────────────────


def test_find_heading_prefers_line_start_over_mid_sentence_match():
    """A clause_num appearing mid-sentence (e.g. a cross-reference or table of
    contents entry) before the real line-start heading must not be picked —
    that would permanently shift the search cursor for all later sections
    (#459 QC review finding #4)."""
    ocr = "Xem thêm Điều 5 để biết chi tiết.\n\nĐiều 5: Nội dung thật của điều 5."
    idx = _find_heading(ocr, "Điều 5", 0)
    # Must land on the line-start occurrence, not the mid-sentence one.
    assert ocr[idx:idx + 6] == "Điều 5"
    assert idx == ocr.index("\n\n") + 2


def test_find_heading_falls_back_to_substring_when_no_line_start_match():
    """No line-start occurrence at all — degrades to a bare substring search
    rather than returning -1 and losing the document text (D-08)."""
    ocr = "some text Điều 5 embedded mid-sentence only, no other occurrence."
    idx = _find_heading(ocr, "Điều 5", 0)
    assert idx == ocr.index("Điều 5")


def test_find_heading_returns_minus_one_when_absent():
    assert _find_heading("no matching heading here", "Điều 9", 0) == -1


# ── _paragraph_chunks ────────────────────────────────────────────────────────


def test_paragraph_chunks_splits_on_blank_lines():
    text = "Đoạn 1.\n\nĐoạn 2.\n\nĐoạn 3."
    chunks = _paragraph_chunks(text, size=1000)
    assert len(chunks) == 1  # small enough to fit in one chunk


def test_paragraph_chunks_respects_size_budget():
    text = "\n\n".join(["A" * 100] * 50)  # ~5000 chars
    chunks = _paragraph_chunks(text, size=1000)
    assert len(chunks) > 1
    assert all(len(c) <= 1000 or "\n\n" not in c for c in chunks)


def test_paragraph_chunks_hard_wraps_oversized_single_paragraph():
    text = "A" * 3000  # one giant paragraph, no blank lines
    chunks = _paragraph_chunks(text, size=1000)
    assert len(chunks) == 3
    assert "".join(chunks) == text


# ── run_content_fill: happy path ──────────────────────────────────────────────


def test_run_content_fill_marks_filled(test_tenant, db):
    doc = _make_doc(db, test_tenant)
    persist_skeleton(db, test_tenant, doc.id, _skeleton([("Điều 1", None, 1, "1")]))
    ocr_text = "Điều 1: Nội dung điều khoản đầy đủ."

    fake_result = FillResult(
        clauses=[FillClauseResult(clause_path="1", content="Nội dung điều khoản đầy đủ.")],
        truncated=False,
    )

    with patch("app.services.two_pass_runner.fill_section", new=AsyncMock(return_value=fake_result)):
        summary = asyncio.run(run_content_fill(db, test_tenant, doc.id, ocr_text))

    assert summary == {"total": 1, "filled": 1, "truncated": 0}
    clause = db.query(Clause).filter(Clause.document_id == doc.id).first()
    assert clause.content_status == "filled"
    assert clause.content == "Nội dung điều khoản đầy đủ."


def test_run_content_fill_resume_skips_filled_sections(test_tenant, db):
    """Already-'filled' sections are never re-sent to fill_section on resume."""
    doc = _make_doc(db, test_tenant)
    clauses = persist_skeleton(db, test_tenant, doc.id, _skeleton([
        ("Điều 1", None, 1, "1"), ("Điều 2", None, 1, "2"),
    ]))
    # Simulate Điều 1 already filled from a prior (interrupted) run.
    c1 = next(c for c in clauses if c.clause_path == "1")
    c1.content = "Đã điền."
    c1.content_status = "filled"
    db.commit()

    fake_result = FillResult(
        clauses=[FillClauseResult(clause_path="2", content="Nội dung 2.")], truncated=False,
    )
    mock_fill = AsyncMock(return_value=fake_result)

    with patch("app.services.two_pass_runner.fill_section", new=mock_fill):
        summary = asyncio.run(run_content_fill(db, test_tenant, doc.id, "Điều 1...\n\nĐiều 2..."))

    mock_fill.assert_called_once()  # only Điều 2's section was sent
    assert summary["filled"] == 2


def test_run_content_fill_truncation_falls_back_to_paragraph_split(test_tenant, db):
    """A truncated section fill retries per-clause via Pass 3, assembling chunks."""
    doc = _make_doc(db, test_tenant)
    persist_skeleton(db, test_tenant, doc.id, _skeleton([("Điều 1", None, 1, "1")]))
    ocr_text = "Điều 1: " + ("A" * 5000)

    truncated_result = FillResult(clauses=[], truncated=True, warnings=["MAX_TOKENS"])
    paragraph_result = ParagraphFillResult(content="phần đã bóc", truncated=False)

    with patch("app.services.two_pass_runner.fill_section", new=AsyncMock(return_value=truncated_result)), \
         patch("app.services.two_pass_runner.fill_paragraph", new=AsyncMock(return_value=paragraph_result)):
        summary = asyncio.run(run_content_fill(db, test_tenant, doc.id, ocr_text))

    clause = db.query(Clause).filter(Clause.document_id == doc.id).first()
    assert clause.content_status == "filled"
    assert "phần đã bóc" in clause.content
    assert summary["filled"] == 1


def test_run_content_fill_paragraph_split_still_fails_marks_truncated(test_tenant, db):
    """If even Pass 3 can't complete a chunk, the clause stays 'truncated' — never
    silently marked 'filled' with partial/fabricated content (D-08)."""
    doc = _make_doc(db, test_tenant)
    persist_skeleton(db, test_tenant, doc.id, _skeleton([("Điều 1", None, 1, "1")]))
    ocr_text = "Điều 1: " + ("A" * 5000)

    truncated_result = FillResult(clauses=[], truncated=True, warnings=["MAX_TOKENS"])
    failed_paragraph = ParagraphFillResult(content="", truncated=True, warnings=["MAX_TOKENS"])

    with patch("app.services.two_pass_runner.fill_section", new=AsyncMock(return_value=truncated_result)), \
         patch("app.services.two_pass_runner.fill_paragraph", new=AsyncMock(return_value=failed_paragraph)):
        summary = asyncio.run(run_content_fill(db, test_tenant, doc.id, ocr_text))

    clause = db.query(Clause).filter(Clause.document_id == doc.id).first()
    assert clause.content_status == "truncated"
    assert summary["truncated"] == 1


# ── run_content_fill: partial-section resume + no-regression (QC review) ──────


def test_run_content_fill_partial_section_only_rebills_pending_clauses(test_tenant, db):
    """A section with 1 of 2 clauses already 'filled' only sends the pending
    clause's path in the manifest to fill_section — not the whole section
    (#459 QC review finding #3)."""
    doc = _make_doc(db, test_tenant)
    clauses = persist_skeleton(db, test_tenant, doc.id, _skeleton([
        ("Điều 1", None, 1, "1"), ("Khoản 1.1", None, 2, "1.1"),
    ]))
    c_top = next(c for c in clauses if c.clause_path == "1")
    c_top.content = "Đã điền rồi."
    c_top.content_status = "filled"
    db.commit()

    fake_result = FillResult(
        clauses=[FillClauseResult(clause_path="1.1", content="Nội dung 1.1.")], truncated=False,
    )
    mock_fill = AsyncMock(return_value=fake_result)

    with patch("app.services.two_pass_runner.fill_section", new=mock_fill):
        summary = asyncio.run(run_content_fill(db, test_tenant, doc.id, "Điều 1...\n\n1.1 ..."))

    mock_fill.assert_called_once()
    sent_manifest = mock_fill.call_args.args[1]
    sent_paths = {c.clause_path for c in sent_manifest}
    assert sent_paths == {"1.1"}  # only the pending clause, not "1" too

    db.expire_all()
    fresh_top = db.query(Clause).filter(Clause.id == c_top.id).first()
    assert fresh_top.content == "Đã điền rồi."  # untouched
    assert summary["filled"] == 2


def test_run_content_fill_previously_truncated_clause_skips_straight_to_pass3(test_tenant, db):
    """A clause already marked 'truncated' from a prior call routes directly to
    Pass 3 on the next call — never re-sent through fill_section again
    (#459 QC review finding #5: guarantees convergence instead of an
    indefinite skeleton/truncated retry loop)."""
    doc = _make_doc(db, test_tenant)
    clauses = persist_skeleton(db, test_tenant, doc.id, _skeleton([("Điều 1", None, 1, "1")]))
    clauses[0].content_status = "truncated"
    db.commit()

    mock_fill_section = AsyncMock()
    paragraph_result = ParagraphFillResult(content="nội dung bóc qua Pass 3", truncated=False)

    with patch("app.services.two_pass_runner.fill_section", new=mock_fill_section), \
         patch("app.services.two_pass_runner.fill_paragraph", new=AsyncMock(return_value=paragraph_result)):
        summary = asyncio.run(run_content_fill(db, test_tenant, doc.id, "Điều 1: nội dung..."))

    mock_fill_section.assert_not_called()  # went straight to Pass 3, no Pass 2 retry
    clause = db.query(Clause).filter(Clause.document_id == doc.id).first()
    assert clause.content_status == "filled"
    assert "nội dung bóc qua Pass 3" in clause.content
    assert summary["filled"] == 1


def test_run_content_fill_pass3_never_regresses_already_filled_clause(test_tenant, db):
    """If a section-level Pass 2 call fails for OTHER pending clauses, an
    already-'filled' clause in that same section must not be re-run through
    Pass 3 and potentially lose its content (#459 QC review finding #2)."""
    doc = _make_doc(db, test_tenant)
    clauses = persist_skeleton(db, test_tenant, doc.id, _skeleton([
        ("Điều 1", None, 1, "1"), ("Khoản 1.1", None, 2, "1.1"),
    ]))
    c_top = next(c for c in clauses if c.clause_path == "1")
    c_top.content = "Nội dung gốc — không được ghi đè."
    c_top.content_status = "filled"
    c_sub = next(c for c in clauses if c.clause_path == "1.1")
    c_sub.content_status = "truncated"  # pending, from a prior attempt
    db.commit()

    mock_fill_section = AsyncMock()  # should never be called — both clauses are non-fresh
    paragraph_result = ParagraphFillResult(content="1.1 filled via pass 3", truncated=False)
    mock_paragraph = AsyncMock(return_value=paragraph_result)

    with patch("app.services.two_pass_runner.fill_section", new=mock_fill_section), \
         patch("app.services.two_pass_runner.fill_paragraph", new=mock_paragraph):
        asyncio.run(run_content_fill(db, test_tenant, doc.id, "Điều 1...\n\n1.1 ..."))

    # fill_paragraph must only ever be invoked for the truncated clause (1.1),
    # never for the already-filled top-level clause (1).
    called_clause_nums = {call.args[0] for call in mock_paragraph.call_args_list}
    assert called_clause_nums == {"Khoản 1.1"}

    db.expire_all()
    fresh_top = db.query(Clause).filter(Clause.id == c_top.id).first()
    assert fresh_top.content == "Nội dung gốc — không được ghi đè."
    assert fresh_top.content_status == "filled"
