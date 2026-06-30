"""Clause hierarchy builder — infer parent/child structure from clause numbering.

Called from extraction_runner after clause rows are flushed (within the same
transaction). Operates in-place: sets parent_id, level, clause_path on each
Clause row. Synthesizes stub parent nodes for missing intermediate levels.

Vietnamese numbering conventions handled (1-indexed, matching prompt schema):
  Điều X           → top-level path "X"          (level 1)
  Khoản X.Y        → sub path "X.Y"              (level 2)
  Mục X.Y          → sub path "X.Y"              (level 2)
  X.Y              → sub path "X.Y"              (level 2)
  X.Y.Z            → sub-sub path "X.Y.Z"        (level 3)
  Phụ lục X        → appendix path "PL-X"        (level 1)

Clauses with unrecognised numbering (Roman numerals, letters, bare titles)
keep clause_path=None, parent_id=None, level=None.
"""
import logging
import re
from typing import Optional

from app.models.tenant import Clause

logger = logging.getLogger(__name__)

# Patterns ordered most-specific first.
_PHU_LUC_RE = re.compile(r"^(?:Ph[uụ]\s+l[uụ]c|PHỤ\s+LỤC)\s+([A-Za-z0-9]+)", re.IGNORECASE)
_DIEU_RE = re.compile(r"^(?:Đi[eề]u|DIEU)\s*(\d+)\s*[\.:\s]*$", re.IGNORECASE)
_KHOAN_MUC_RE = re.compile(r"^(?:Kho[aả]n|M[uụ]c|KHOAN|MUC)\s*(\d+(?:\.\d+)+)\s*[\.:\s]*$", re.IGNORECASE)
_DOTTED_RE = re.compile(r"^(\d+(?:\.\d+)+)\s*[\.:]?\s*")  # bare "2.1" or "2.1.1 ..."
_TOP_RE = re.compile(r"^(\d+)\s*[\.:]?\s*")                 # bare "2" or "2. Tên mục"


def _parse_path(clause_num: Optional[str]) -> Optional[str]:
    """Extract dotted numeric path from a clause_num string, or None."""
    if not clause_num:
        return None
    s = clause_num.strip()
    if s.startswith("PL-"):
        return s
    m = _PHU_LUC_RE.match(s)
    if m:
        return f"PL-{m.group(1).upper()}"
    m = _DIEU_RE.match(s)
    if m:
        return m.group(1)
    m = _KHOAN_MUC_RE.match(s)
    if m:
        return m.group(1)
    m = _DOTTED_RE.match(s)
    if m:
        return m.group(1)
    m = _TOP_RE.match(s)
    if m:
        return m.group(1)
    return None


def _level_from_path(path: str) -> int:
    """Return hierarchy depth (1-indexed, matching prompt schema):
    "2"→1, "2.1"→2, "2.1.1"→3."""
    return path.count(".") + 1


def _parent_path(path: str) -> Optional[str]:
    """Return the immediate parent path: "2.1.1"→"2.1", "2.1"→"2", "2"→None."""
    idx = path.rfind(".")
    return path[:idx] if idx != -1 else None


def _stub_num(path: str) -> str:
    """Generate a clause_num label for a synthesized parent stub."""
    if path.startswith("PL-"):
        suffix = path[3:]
        if "." not in suffix:
            return f"Phụ lục {suffix}"
        return path
    if "." not in path:
        return f"Điều {path}"
    return path


def build_clause_hierarchy(clauses: list, db) -> None:
    """Set parent_id, level, clause_path on each Clause. Synthesizes missing parents.

    `clauses` is the list of Clause ORM objects for one document, already added
    to `db` but not yet committed. `db` is the active session (same transaction
    as the extraction commit).

    Mutates the objects in place — no separate commit needed.
    """
    if not clauses:
        return

    # Step 1: parse paths for all existing clauses.
    # Always compute level from clause_path (source of truth) — LLM-provided
    # level is often wrong (e.g. path="1.1" but level=1 instead of 2).
    for clause in clauses:
        if clause.clause_path is not None:
            clause.level = _level_from_path(clause.clause_path)
        else:
            path = _parse_path(clause.clause_num)
            if path is not None:
                clause.clause_path = path
                clause.level = _level_from_path(path)

    # Step 2: build a path→clause lookup (existing rows only, first-wins on collision).
    path_map: dict[str, Clause] = {}
    for clause in clauses:
        if clause.clause_path is not None:
            if clause.clause_path in path_map:
                logger.warning(
                    "Duplicate clause_path %r in doc %d — keeping first, skipping %r",
                    clause.clause_path, clause.document_id, clause.clause_num,
                )
                continue
            path_map[clause.clause_path] = clause

    # Step 3: synthesize missing parent stubs bottom-up.
    # Iterate in depth-first order so we create the deepest missing ancestor first.
    tenant_id = clauses[0].tenant_id
    document_id = clauses[0].document_id
    stubs: list[Clause] = []

    def _ensure_ancestor(path: str) -> None:
        if path in path_map:
            return
        parent = _parent_path(path)
        if parent is not None:
            _ensure_ancestor(parent)
        stub = Clause(
            tenant_id=tenant_id,
            document_id=document_id,
            clause_num=_stub_num(path),
            title=None,
            content="(tổng hợp từ mục con)",
            clause_path=path,
            level=_level_from_path(path),
        )
        db.add(stub)
        path_map[path] = stub
        stubs.append(stub)

    for clause in list(clauses):  # iterate over original set only
        if clause.clause_path is not None:
            parent_p = _parent_path(clause.clause_path)
            if parent_p is not None:
                _ensure_ancestor(parent_p)

    # Flush stubs so they get IDs before we link parent_id.
    if stubs:
        db.flush()

    # Step 4: link parent_id for every clause that has a parent path.
    all_clauses = list(clauses) + stubs
    for clause in all_clauses:
        if clause.clause_path is not None:
            parent_p = _parent_path(clause.clause_path)
            if parent_p is not None:
                parent_clause = path_map.get(parent_p)
                if parent_clause is not None:
                    clause.parent_id = parent_clause.id
