"""Two-pass map-reduce extraction orchestrator (#449, WS2-Backend of mini-sprint #443).

Owns the state machine Backend is responsible for per #449's spec: persisting
`Clause.content_status` (skeleton/filled/truncated), grouping clauses into
sections (one Điều or one Phụ lục), iterating Pass 2 (`fill_section`) per
section with a commit after EACH section (durable checkpoint — killing the
process mid-run and re-running resumes from non-'filled' clauses only, no
re-billing already-filled sections), and falling back to Pass 3
(`fill_paragraph`) when a section's fill hits MAX_TOKENS.

KHE_AI's `modules.extraction.two_pass` owns the prompts/pass design (pure LLM
callers). This module owns everything DB-shaped: persistence, grouping,
resumability, and the paragraph-split fallback's chunk slicing.

Not wired into `extraction_runner.py`'s automatic MAX_TOKENS path in this PR —
that integration decision (auto-trigger on truncation vs. explicit opt-in) is
flagged back to #443/PM rather than assumed, since it changes production
extraction behavior and can't be verified end-to-end without live Gemini keys
in this environment. This module is a complete, independently callable,
resumable unit ready for that wiring once decided.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.tenant import Clause
from modules.extraction.two_pass import (
    FillResult,
    SkeletonClauseResult,
    SkeletonResult,
    fill_paragraph,
    fill_section,
)

logger = logging.getLogger(__name__)

# Paragraph-split fallback (Pass 3) chunk size — small enough that even a
# giant single clause's content splits into several sub-8,192-output-token
# calls. Not tied to a token count (chars, not tokens) — a conservative
# character budget that in practice keeps each chunk's *output* comfortably
# under Pass 3's cap even accounting for Vietnamese's higher chars/token ratio.
_PARAGRAPH_CHUNK_CHARS = 4_000


# ============================================================================
# Pass 1 persistence
# ============================================================================


def persist_skeleton(
    db: Session,
    tenant_id: str,
    doc_id: int,
    skeleton: SkeletonResult,
) -> list[Clause]:
    """Persist Pass 1's skeleton clauses with content_status='skeleton'.

    Idempotent like the single-call path: replaces any existing clauses for
    this doc first. Reuses `build_clause_hierarchy` for parent_id/level/stub
    synthesis — LLM-provided clause_path (already PL-aware per #439) wins over
    regex inference, same as the single-call runner.

    Commits as a checkpoint (Pass 1 is durable before Pass 2 begins) — the
    caller does not need to commit again for this step.
    """
    db.query(Clause).filter(
        Clause.document_id == doc_id, Clause.tenant_id == tenant_id,
    ).delete()

    clauses: list[Clause] = []
    for item in skeleton.clauses:
        clauses.append(Clause(
            tenant_id=tenant_id,
            document_id=doc_id,
            clause_num=item.num,
            title=item.title,
            content="",
            level=item.level,
            clause_path=item.clause_path,
            content_status="skeleton",
        ))
    db.add_all(clauses)
    db.flush()

    from app.services.clause_hierarchy import build_clause_hierarchy
    build_clause_hierarchy(clauses, db)
    db.commit()
    for c in clauses:
        db.refresh(c)
    return clauses


# ============================================================================
# Section grouping
# ============================================================================


def group_into_sections(clauses: list[Clause]) -> list[list[Clause]]:
    """Group clauses into sections — one Điều or one Phụ lục + its descendants.

    A section's anchor is any clause with level == 0 (or None, treated as its
    own singleton section — legacy/unrecognised numbering has no group to join).
    Descendants join their nearest level-0 ancestor's section via parent_id.
    Preserves document order (clauses are inserted/queried in appearance order).
    """
    by_id = {c.id: c for c in clauses}

    def _top_ancestor(c: Clause) -> Clause:
        seen = set()
        cur = c
        while cur.parent_id is not None and cur.parent_id in by_id and cur.id not in seen:
            seen.add(cur.id)
            cur = by_id[cur.parent_id]
        return cur

    sections: dict[int, list[Clause]] = {}
    order: list[int] = []
    for c in clauses:
        anchor = _top_ancestor(c)
        if anchor.id not in sections:
            sections[anchor.id] = []
            order.append(anchor.id)
        sections[anchor.id].append(c)

    return [sections[anchor_id] for anchor_id in order]


# ============================================================================
# Section OCR-text slicing
# ============================================================================


def _find_heading(ocr_text: str, clause_num: Optional[str], search_from: int) -> int:
    """Best-effort index of a clause's heading in the OCR text, or -1."""
    if not clause_num:
        return -1
    idx = ocr_text.find(clause_num, search_from)
    return idx


def slice_section_text(ocr_text: str, sections: list[list[Clause]]) -> list[str]:
    """Slice `ocr_text` into one substring per section, in document order.

    Heuristic: each section's OCR span starts at its top-level clause's
    heading text and ends where the next section's heading begins (or EOF for
    the last section). If a heading can't be located (OCR text differs from
    the clause_num string — punctuation, whitespace normalization), degrades
    gracefully to the remaining full text rather than fabricating or crashing
    (D-08) — Pass 2 still gets real document text, just a wider slice than
    ideal, and the manifest still constrains it to the section's own paths.
    """
    anchors = [sec[0] for sec in sections]
    starts: list[int] = []
    cursor = 0
    for anchor in anchors:
        idx = _find_heading(ocr_text, anchor.clause_num, cursor)
        if idx == -1:
            idx = cursor
        else:
            cursor = idx
        starts.append(idx)

    slices: list[str] = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(ocr_text)
        if end <= start:
            end = len(ocr_text)
        slices.append(ocr_text[start:end])
    return slices


def _paragraph_chunks(text: str, size: int = _PARAGRAPH_CHUNK_CHARS) -> list[str]:
    """Split text into chunks on paragraph boundaries (blank lines) where
    possible, hard-wrapping only if a single paragraph itself exceeds `size`.
    """
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return [text] if text.strip() else []

    chunks: list[str] = []
    current = ""
    for p in paragraphs:
        candidate = f"{current}\n\n{p}" if current else p
        if len(candidate) > size and current:
            chunks.append(current)
            current = p
        else:
            current = candidate
    if current:
        chunks.append(current)

    # A single paragraph larger than `size` on its own — hard-wrap it.
    final: list[str] = []
    for c in chunks:
        if len(c) <= size:
            final.append(c)
        else:
            for i in range(0, len(c), size):
                final.append(c[i:i + size])
    return final


# ============================================================================
# Pass 2 + Pass 3 orchestration (resumable)
# ============================================================================


async def run_content_fill(
    db: Session,
    tenant_id: str,
    doc_id: int,
    ocr_text: str,
    *,
    api_key: str | None = None,
) -> dict:
    """Resumable Pass 2 (+ Pass 3 fallback) orchestration.

    Iterates sections in hierarchy order; only sections with at least one
    non-'filled' clause are re-processed — a fresh call on an already-'filled'
    doc is a near-instant no-op. Commits after EACH section (or, on
    truncation, after each Pass-3-assembled clause) so a crash/timeout/deploy
    mid-run loses at most one section's work, and re-running this function
    picks up exactly where it left off.

    Returns a progress summary: {"total": N, "filled": N, "truncated": N}.
    """
    all_clauses = (
        db.query(Clause)
        .filter(Clause.document_id == doc_id, Clause.tenant_id == tenant_id)
        .order_by(Clause.id.asc())
        .all()
    )
    sections = group_into_sections(all_clauses)
    section_texts = slice_section_text(ocr_text, sections)

    for section, section_text in zip(sections, section_texts):
        if all(c.content_status == "filled" for c in section):
            continue  # already done — resume skips this section entirely

        skeleton_manifest = [
            SkeletonClauseResult(
                num=c.clause_num, title=c.title, level=c.level, clause_path=c.clause_path,
            )
            for c in section
        ]
        result: FillResult = await fill_section(section_text, skeleton_manifest, api_key=api_key)

        if result.truncated or not result.clauses:
            # Section-level fill didn't complete cleanly — fall back to
            # per-clause paragraph-split (Pass 3) for every clause in this
            # section rather than guessing which single clause overflowed.
            for clause, clause_text in zip(section, _split_section_by_clause(section_text, section)):
                await _fill_clause_via_paragraphs(
                    db, clause, clause_text, api_key=api_key,
                )
            continue

        by_path = {fc.clause_path: fc.content for fc in result.clauses}
        for clause in section:
            if clause.clause_path in by_path:
                clause.content = by_path[clause.clause_path]
                clause.content_status = "filled"
            elif clause.content_status != "filled":
                # Not returned by this call (e.g. empty-content parent clause
                # the model legitimately omitted) — leave for a future retry
                # rather than silently marking it done with stale/empty content.
                clause.content_status = "truncated"
        db.commit()  # per-section checkpoint

    all_clauses = (
        db.query(Clause)
        .filter(Clause.document_id == doc_id, Clause.tenant_id == tenant_id)
        .all()
    )
    filled = sum(1 for c in all_clauses if c.content_status == "filled")
    truncated = sum(1 for c in all_clauses if c.content_status == "truncated")
    return {"total": len(all_clauses), "filled": filled, "truncated": truncated}


def _split_section_by_clause(section_text: str, section: list[Clause]) -> list[str]:
    """Best-effort per-clause slice of a section's text, for Pass 3 fallback.

    Same heading-search heuristic as `slice_section_text`, one level down —
    each clause's span runs from its own heading to the next clause's heading
    within the section (or section end for the last clause).
    """
    starts: list[int] = []
    cursor = 0
    for clause in section:
        idx = _find_heading(section_text, clause.clause_num, cursor)
        if idx == -1:
            idx = cursor
        else:
            cursor = idx
        starts.append(idx)

    slices: list[str] = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(section_text)
        if end <= start:
            end = len(section_text)
        slices.append(section_text[start:end])
    return slices


async def _fill_clause_via_paragraphs(
    db: Session,
    clause: Clause,
    clause_text: str,
    *,
    api_key: str | None = None,
) -> None:
    """Pass 3: fill one clause incrementally by paragraph chunk, concatenating
    results in order. Commits once the clause is assembled (or marks
    'truncated' with a warning if even a single chunk can't complete — D-08:
    never fabricate a completion that didn't happen)."""
    chunks = _paragraph_chunks(clause_text)
    if not chunks:
        clause.content_status = "truncated"
        db.commit()
        return

    assembled: list[str] = []
    for i, chunk in enumerate(chunks):
        result = await fill_paragraph(
            clause.clause_num, clause.title, chunk,
            is_continuation=(i > 0), api_key=api_key,
        )
        if result.truncated or (not result.content and chunk.strip()):
            logger.warning(
                "Paragraph fill failed/truncated for clause %d chunk %d/%d: %s",
                clause.id, i + 1, len(chunks), "; ".join(result.warnings),
            )
            clause.content_status = "truncated"
            db.commit()
            return
        assembled.append(result.content)

    clause.content = "\n\n".join(assembled)
    clause.content_status = "filled"
    db.commit()  # per-clause checkpoint within Pass 3
