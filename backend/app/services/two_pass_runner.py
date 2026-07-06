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

HARD PRECONDITION FOR THAT FUTURE WIRING (#459 QC review finding #6): neither
`persist_skeleton` nor `run_content_fill` takes out any lock or in-progress
marker on `doc_id`. Two concurrent invocations for the same doc (a double-click
retry, or a retry endpoint racing a scheduled sweep) will double-bill the LLM
and race each other's `db.commit()` calls. The eventual caller MUST serialize
invocations per doc_id — e.g. a `processing_stage` guard checked-and-set before
enqueueing, or a proper job queue with per-doc uniqueness — before this can be
triggered from more than one call site at a time. Not solved here: building a
locking mechanism without knowing the real invocation context (single worker
vs. multi-worker, sync vs. background task) risks building the wrong one.
"""
from __future__ import annotations

import logging
import re
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

    Idempotent-by-deletion ONLY when no Pass 2 progress exists yet. If any
    clause for this doc already has content_status in ('filled', 'truncated'),
    this is a no-op that returns the existing clauses unchanged — deleting and
    re-inserting would wipe already-filled content on every re-entry (e.g. a
    caller that unconditionally calls persist_skeleton before run_content_fill
    on retry), directly defeating this module's resumable/no-re-billing
    purpose (#459 QC review finding #1). Callers resuming an in-progress doc
    should call `run_content_fill` directly, not re-run Pass 1.

    On a genuinely fresh doc (no clauses, or only pre-existing 'skeleton' rows
    from an interrupted Pass 1 that never reached Pass 2), replaces any
    existing clauses — reuses `build_clause_hierarchy` for parent_id/level/
    stub synthesis (LLM-provided clause_path, already PL-aware per #439, wins
    over regex inference, same as the single-call runner) and commits as a
    checkpoint before Pass 2 begins.
    """
    existing = (
        db.query(Clause)
        .filter(Clause.document_id == doc_id, Clause.tenant_id == tenant_id)
        .all()
    )
    if existing and any(c.content_status in ("filled", "truncated") for c in existing):
        logger.info(
            "persist_skeleton: doc %d already has Pass 2 progress — skipping re-persist",
            doc_id,
        )
        return existing

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

    # Re-query rather than returning `clauses` directly — build_clause_hierarchy
    # may append synthesized stub-parent Clause rows to its own local list, not
    # back to this one (#459 QC review finding #7); a fresh query is the only
    # way to guarantee the return value reflects everything actually persisted.
    return (
        db.query(Clause)
        .filter(Clause.document_id == doc_id, Clause.tenant_id == tenant_id)
        .order_by(Clause.id.asc())
        .all()
    )


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
    """Best-effort index of a clause's heading in the OCR text, or -1.

    Prefers a match at the start of a line (where headings normally sit) over
    a bare substring match — reduces false positives from a clause_num string
    appearing mid-sentence (a table of contents entry, or a cross-reference
    inside another clause's body) before the real heading, which would
    otherwise permanently shift `search_from` for every later call and
    corrupt the rest of the document's section slicing (#459 QC review
    finding #4). Falls back to a bare substring search if no line-start match
    exists, rather than failing outright (D-08: degrade gracefully).
    """
    if not clause_num:
        return -1
    pattern = re.compile(r"(?:^|\n)[ \t]*" + re.escape(clause_num), re.MULTILINE)
    m = pattern.search(ocr_text, search_from)
    if m:
        return m.end() - len(clause_num)
    return ocr_text.find(clause_num, search_from)


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

    Iterates sections in hierarchy order; only clauses with content_status !=
    'filled' are ever re-sent to an LLM call — a fresh call on an
    already-'filled' doc is a near-instant no-op, and a *partially*-filled
    section only re-bills its remaining clauses, not the whole section
    (#459 QC review finding #3: manifests sent to `fill_section` are built
    from pending clauses only, even though `section_text` still carries full
    section context so the model isn't missing surrounding clauses).

    A clause already marked 'truncated' from a prior call routes straight to
    Pass 3 (per-clause paragraph fill) instead of another Pass 2 attempt —
    guarantees convergence within one more retry instead of an indefinite
    skeleton/truncated cycle for content the LLM keeps omitting for reasons
    other than MAX_TOKENS (#459 QC review finding #5). Every write path
    checks `content_status == "filled"` before touching a clause, so
    already-good content is never regressed by a later retry (#459 QC review
    finding #2).

    Commits after EACH section's Pass 2 call (or, on Pass 3, after each
    assembled clause) so a crash/timeout/deploy mid-run loses at most one
    section's un-checkpointed work, and re-running this function picks up
    exactly where it left off.

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
        pending = [c for c in section if c.content_status != "filled"]
        if not pending:
            continue  # already done — resume skips this section entirely

        clause_text_by_id = dict(zip(
            (c.id for c in section), _split_section_by_clause(section_text, section),
        ))

        needs_pass3 = [c for c in pending if c.content_status == "truncated"]
        fresh = [c for c in pending if c.content_status != "truncated"]

        if fresh:
            skeleton_manifest = [
                SkeletonClauseResult(
                    num=c.clause_num, title=c.title, level=c.level, clause_path=c.clause_path,
                )
                for c in fresh
            ]
            result: FillResult = await fill_section(section_text, skeleton_manifest, api_key=api_key)

            if result.truncated or not result.clauses:
                # Section-level fill didn't complete cleanly for any of the
                # pending clauses — fall back to per-clause paragraph-split
                # (Pass 3) rather than guessing which single clause overflowed.
                needs_pass3.extend(fresh)
            else:
                by_path = {fc.clause_path: fc.content for fc in result.clauses}
                for clause in fresh:
                    if clause.clause_path in by_path:
                        clause.content = by_path[clause.clause_path]
                        clause.content_status = "filled"
                    else:
                        # Not returned by this call (e.g. empty-content parent
                        # clause the model legitimately omitted, or a genuine
                        # partial truncation) — route to Pass 3 next rather
                        # than silently marking it done or re-cycling forever.
                        clause.content_status = "truncated"
                        needs_pass3.append(clause)
                db.commit()  # per-section checkpoint

        for clause in needs_pass3:
            if clause.content_status == "filled":
                continue  # never regress content a concurrent/earlier pass already filled
            await _fill_clause_via_paragraphs(
                db, clause, clause_text_by_id[clause.id], api_key=api_key,
            )

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
