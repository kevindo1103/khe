"""Cross-reference detection + resolution within a document's clauses (#373, R10)."""
import re
import logging

from sqlalchemy.orm import Session

from app.models.tenant import Clause, ClauseCrossRef, DocumentRelationship

logger = logging.getLogger(__name__)

# Patterns — ordered most-specific first, Unicode-aware (diacritics included)
#
# Vietnamese legal hierarchy: Điều (article) > Khoản (section) > Mục (sub-section).
# Compound refs like "Khoản 2 Điều 5" mean section 2 OF article 5 → clause_path "5.2".
# Standalone "Điều 5" → clause_path "5".
# Standalone "Khoản 2" is ambiguous (sub-section 2 of which article?) — kept as
# ref_type "sub_clause" so the resolver can attempt path lookup but won't wrongly
# match a top-level Điều.

# Compound: "Khoản X Điều Y" or "Khoản X, Điều Y" → clause_path "Y.X"
_COMPOUND_KHOAN_DIEU = re.compile(
    r"(?:theo|tại|quy\s+định\s+tại|căn\s+cứ)?\s*"
    r"(?:Kho[aả]n|KHOẢN|khoan)\s+(\d+(?:\.\d+)*)"
    r"(?:\s*,?\s*)"
    r"(?:Đi[eề]u|ĐIỀU|dieu)\s+(\d+(?:\.\d+)*)",
    re.IGNORECASE,
)
# Compound: "Mục X Điều Y" → clause_path "Y.X"
_COMPOUND_MUC_DIEU = re.compile(
    r"(?:theo|tại|quy\s+định\s+tại|căn\s+cứ)?\s*"
    r"(?:M[uụ]c|MỤC|muc)\s+(\d+(?:\.\d+)*)"
    r"(?:\s*,?\s*)"
    r"(?:Đi[eề]u|ĐIỀU|dieu)\s+(\d+(?:\.\d+)*)",
    re.IGNORECASE,
)

_DIEU_REF = re.compile(
    r"(?:theo|tại|quy\s+định\s+tại|căn\s+cứ)?\s*"
    r"(?:Đi[eề]u|ĐIỀU|dieu)\s+(\d+(?:\.\d+)*)",
    re.IGNORECASE,
)
_KHOAN_REF = re.compile(
    r"(?:theo|tại)?\s*(?:Kho[aả]n|KHOẢN|khoan)\s+(\d+(?:\.\d+)*)",
    re.IGNORECASE,
)
_MUC_REF = re.compile(
    r"(?:theo|tại)?\s*(?:M[uụ]c|MỤC|muc)\s+(\d+(?:\.\d+)*)",
    re.IGNORECASE,
)
_PHU_LUC_REF = re.compile(
    r"(?:theo|tại|quy\s+định\s+tại)?\s*"
    r"(?:Ph[uụ]\s+l[uụ]c|PHỤ\s+LỤC|phu\s+luc)\s+([A-Za-z0-9]+)",
    re.IGNORECASE,
)


def _detect_refs(content: str) -> list[tuple[str, str, str]]:
    """Return list of (ref_text, ref_type, target_key) tuples from clause content.

    target_key is a clause_path (e.g. "5", "5.2") for clause refs,
    or an appendix identifier (e.g. "A", "1") for appendix refs.

    Compound Vietnamese legal refs are resolved hierarchically:
    - "Khoản 2 Điều 5" → clause_path "5.2" (section 2 of article 5)
    - "Mục 3 Điều 7" → clause_path "7.3"
    Standalone Khoản/Mục are typed "sub_clause" to avoid wrongly matching
    a top-level Điều with the same number.
    """
    refs: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    consumed_spans: list[tuple[int, int]] = []

    def _overlaps(start: int, end: int) -> bool:
        return any(s < end and start < e for s, e in consumed_spans)

    # 1. Compound patterns first — "Khoản X Điều Y" → "Y.X"
    for pattern in [_COMPOUND_KHOAN_DIEU, _COMPOUND_MUC_DIEU]:
        for m in pattern.finditer(content):
            sub_num = m.group(1)
            dieu_num = m.group(2)
            target_key = f"{dieu_num}.{sub_num}"
            key = ("clause", target_key)
            if key not in seen:
                seen.add(key)
                refs.append((m.group(0).strip(), "clause", target_key))
            consumed_spans.append((m.start(), m.end()))

    # 2. Standalone Điều → clause_path at article level
    for m in _DIEU_REF.finditer(content):
        if _overlaps(m.start(), m.end()):
            continue
        key = ("clause", m.group(1))
        if key not in seen:
            seen.add(key)
            refs.append((m.group(0).strip(), "clause", m.group(1)))
        consumed_spans.append((m.start(), m.end()))

    # 3. Standalone Khoản/Mục — ambiguous without parent Điều context.
    #    Typed "sub_clause" so resolver doesn't confuse with top-level Điều numbers.
    for pattern in [_KHOAN_REF, _MUC_REF]:
        for m in pattern.finditer(content):
            if _overlaps(m.start(), m.end()):
                continue
            key = ("sub_clause", m.group(1))
            if key not in seen:
                seen.add(key)
                refs.append((m.group(0).strip(), "sub_clause", m.group(1)))

    # 4. Phụ lục (appendix) refs
    for m in _PHU_LUC_REF.finditer(content):
        if _overlaps(m.start(), m.end()):
            continue
        key = ("appendix", m.group(1))
        if key not in seen:
            seen.add(key)
            refs.append((m.group(0).strip(), "appendix", m.group(1)))

    return refs


def resolve_cross_refs(db: Session, tenant_id: str, document_id: int) -> dict:
    """Scan all clauses in a document, detect references, resolve targets.

    Idempotent: deletes existing cross-refs for the document before re-inserting.
    Returns {"total_refs": int, "resolved": int, "orphans": int}.
    """
    clauses = (
        db.query(Clause)
        .filter(Clause.document_id == document_id, Clause.tenant_id == tenant_id)
        .all()
    )

    # clause_path → Clause for intra-doc resolution
    path_map: dict[str, Clause] = {}
    for c in clauses:
        if c.clause_path:
            path_map[c.clause_path] = c

    # Build appendix identifier → doc_id map from annex relationships.
    # Convention: from_doc_id = annex document, to_doc_id = parent document.
    annex_docs: dict[str, int] = {}
    annex_rels = (
        db.query(DocumentRelationship)
        .filter(
            DocumentRelationship.tenant_id == tenant_id,
            DocumentRelationship.to_doc_id == document_id,
            DocumentRelationship.relationship_type == "annex",
        )
        .all()
    )
    for rel in annex_rels:
        if rel.unresolved_ref:
            annex_docs[rel.unresolved_ref.upper()] = rel.from_doc_id

    # Idempotent delete
    db.query(ClauseCrossRef).filter(
        ClauseCrossRef.document_id == document_id,
        ClauseCrossRef.tenant_id == tenant_id,
    ).delete()

    total = 0
    resolved = 0
    orphans = 0

    for clause in clauses:
        if not clause.content:
            continue
        for ref_text, ref_type, target_key in _detect_refs(clause.content):
            target_clause_id = None
            target_clause_path = None
            target_doc_id = None
            is_orphan = True

            if ref_type in ("clause", "sub_clause"):
                target = path_map.get(target_key)
                if target and target.id != clause.id:
                    target_clause_id = target.id
                    target_clause_path = target_key
                    is_orphan = False
            elif ref_type == "appendix":
                doc_id = annex_docs.get(target_key.upper())
                if doc_id:
                    target_doc_id = doc_id
                    is_orphan = False
                else:
                    intra = path_map.get(f"PL-{target_key.upper()}")
                    if intra and intra.id != clause.id:
                        target_clause_id = intra.id
                        target_clause_path = f"PL-{target_key.upper()}"
                        is_orphan = False

            db.add(ClauseCrossRef(
                tenant_id=tenant_id,
                document_id=document_id,
                source_clause_id=clause.id,
                ref_text=ref_text,
                ref_type=ref_type,
                target_clause_id=target_clause_id,
                target_clause_path=target_clause_path,
                target_doc_id=target_doc_id,
                is_orphan=is_orphan,
            ))
            total += 1
            if is_orphan:
                orphans += 1
            else:
                resolved += 1

    db.flush()
    return {"total_refs": total, "resolved": resolved, "orphans": orphans}
