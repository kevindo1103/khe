"""Clause hierarchy builder — infer parent/child structure from clause numbering.

Called from extraction_runner after clause rows are flushed (within the same
transaction). Operates in-place: sets parent_id, level, clause_path on each
Clause row. Synthesizes stub parent nodes for missing intermediate levels.

Vietnamese numbering conventions handled:
  Điều X           → top-level path "X"          (level 0)
  Khoản X.Y        → sub path "X.Y"              (level 1)
  Mục X.Y          → sub path "X.Y"              (level 1)
  X.Y              → sub path "X.Y"              (level 1)
  X.Y.Z            → sub-sub path "X.Y.Z"        (level 2)
  X.Y.Z.W and deeper → clamped to level 2, path preserved

Clauses with unrecognised numbering (Roman numerals, letters, bare titles)
keep clause_path=None, parent_id=None, level=None.
"""
import re
from typing import Optional

from app.models.tenant import Clause

# Patterns ordered most-specific first.
_DIEU_RE = re.compile(r"^(?:Đi[eề]u|DIEU)\s*(\d+)\s*$", re.IGNORECASE)
_KHOAN_MUC_RE = re.compile(r"^(?:Kho[aả]n|M[uụ]c|KHOAN|MUC)\s*(\d+(?:\.\d+)+)\s*$", re.IGNORECASE)
_DOTTED_RE = re.compile(r"^(\d+(?:\.\d+)+)\s*[\.:]?\s*")  # bare "2.1" or "2.1.1 ..."
_TOP_RE = re.compile(r"^(\d+)\s*[\.:]?\s*")                 # bare "2" or "2. Tên mục"


def _parse_path(clause_num: Optional[str]) -> Optional[str]:
    """Extract dotted numeric path from a clause_num string, or None."""
    if not clause_num:
        return None
    s = clause_num.strip()
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
    """Return hierarchy depth: "2"→0, "2.1"→1, "2.1.1"→2 (capped at 2)."""
    return min(path.count("."), 2)


def _parent_path(path: str) -> Optional[str]:
    """Return the immediate parent path: "2.1.1"→"2.1", "2.1"→"2", "2"→None."""
    idx = path.rfind(".")
    return path[:idx] if idx != -1 else None


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
    for clause in clauses:
        path = _parse_path(clause.clause_num)
        if path is not None:
            clause.clause_path = path
            clause.level = _level_from_path(path)
        # else: leave clause_path/level as None (unrecognised numbering)

    # Step 2: build a path→clause lookup (existing rows only).
    path_map: dict[str, Clause] = {}
    for clause in clauses:
        if clause.clause_path is not None:
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
            clause_num=f"Điều {path}" if "." not in path else path,
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
