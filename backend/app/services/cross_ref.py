"""Cross-reference detection + resolution within a document's clauses (#373, R10)."""
import re
import logging

from sqlalchemy.orm import Session

from app.models.tenant import Clause, ClauseCrossRef, DocumentRelationship

logger = logging.getLogger(__name__)

# Patterns — ordered most-specific first, Unicode-aware (diacritics included)
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

    target_key is a clause_path (e.g. "5", "2.1") for clause refs,
    or an appendix identifier (e.g. "A", "1") for appendix refs.
    """
    refs: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()

    for pattern, ref_type in [
        (_DIEU_REF, "clause"),
        (_KHOAN_REF, "clause"),
        (_MUC_REF, "clause"),
        (_PHU_LUC_REF, "appendix"),
    ]:
        for m in pattern.finditer(content):
            key = (ref_type, m.group(1))
            if key not in seen:
                seen.add(key)
                refs.append((m.group(0).strip(), ref_type, m.group(1)))
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

    # Build appendix identifier → doc_id map from annex relationships
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

            if ref_type == "clause":
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

    db.commit()
    return {"total_refs": total, "resolved": resolved, "orphans": orphans}
