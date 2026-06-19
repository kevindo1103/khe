"""Chat query — LLM function-calling + retrieve-only answer engine (DEC-026).

- D-06: returns only extracted fields / clause text, never generates or interprets legal content.
- D-08: returns a fixed "not found" message when no tool returns data.
- Tenant-scoped: every tool query filters by tenant_id.
- Lazy LLM import: google-genai is imported only inside the async functions so that
  `import main` and CI tests work without an API key.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.tenant import Clause, Document, Obligation, Term


logger = logging.getLogger(__name__)
_NOT_FOUND = "Không tìm thấy thông tin này trong hồ sơ của bạn."

# Canonical party field name.  `CANONICAL_FIELDS` in `modules/extraction/schemas.py`
# lists `doi_tac` as the single party/bên ký field, so no alias expansion is needed.
PARTY_FIELDS: tuple[str, ...] = ("doi_tac",)

# Max rows returned by search_terms before truncation.
_MAX_TERM_ROWS = 10

# ---------------------------------------------------------------------------
# LIKE wildcard escaping
# ---------------------------------------------------------------------------

def _escape_like(value: str, escape_char: str = "\\") -> str:
    """Escape SQL LIKE wildcards (% _) and the escape character itself."""
    return value.replace(escape_char, escape_char + escape_char).replace("%", escape_char + "%").replace("_", escape_char + "_")


# ---------------------------------------------------------------------------
# LLM tool definitions (used by the router LLM)
# ---------------------------------------------------------------------------

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_terms",
            "description": "Tìm thông tin trích xuất từ hợp đồng (ngày hiệu lực, ngày hết hạn, đối tác, thời hạn, giá trị, điều khoản thanh toán/gia hạn).",
            "parameters": {
                "type": "object",
                "properties": {
                    "field_name": {
                        "type": "string",
                        "description": "Tên trường cần tìm: doi_tac, ngay_hieu_luc, ngay_het_han, gia_tri_hd, thoi_han_hd, dieu_khoan_gia_han, dieu_khoan_thanh_toan.",
                    },
                    "doc_hint": {
                        "type": ["string", "null"],
                        "description": "Tên/gợi ý HỢP ĐỒNG (filename keyword) nếu người dùng đề cập cụ thể, ví dụ: 'lease_2026', 'Mau HDV FLC'. KHÔNG phải tên công ty, đối tác, hay từ khóa trong câu hỏi. Null nếu không rõ.",
                    },
                    "value_contains": {
                        "type": ["string", "null"],
                        "description": "Từ khóa để tìm trong giá trị trường (field_value) — dùng khi người dùng tìm theo tên công ty/đối tác trong dữ liệu, ví dụ: 'ALASKA'. Không dùng cùng lúc với doc_hint.",
                    },
                    "party_filter": {
                        "type": ["string", "null"],
                        "description": (
                            "Lọc tài liệu theo đối tác/công ty — tìm docs có DOI_TAC chứa chuỗi này, "
                            "sau đó trả field_name trên những docs đó. "
                            "Dùng khi user hỏi về field của hợp đồng với công ty cụ thể. "
                            "Ví dụ: party_filter='ALASKA' để tìm ngày hiệu lực của HĐ với ALASKA. "
                            "Null nếu không lọc theo đối tác."
                        ),
                    },
                },
                "required": ["field_name", "doc_hint", "value_contains", "party_filter"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_obligations",
            "description": "Tìm nghĩa vụ / deadline trong hợp đồng (hết hạn, gia hạn, cần thực hiện).",
            "parameters": {
                "type": "object",
                "properties": {
                    "due_within_days": {
                        "type": ["integer", "null"],
                        "description": "Số ngày tới deadline tối đa. Ví dụ: 30 để tìm HĐ hết hạn trong 30 ngày.",
                    },
                    "status": {
                        "type": ["string", "null"],
                        "description": "Trạng thái nghĩa vụ: pending, overdue, done. Null = mọi trạng thái.",
                    },
                    "doc_hint": {
                        "type": ["string", "null"],
                        "description": "Tên/gợi ý hợp đồng nếu người dùng đề cập cụ thể.",
                    },
                },
                "required": ["due_within_days", "status", "doc_hint"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_clauses",
            "description": "Tìm nội dung điều khoản trong hợp đồng (ví dụ: phạt vi phạm, chấm dứt, bảo mật).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Từ khóa / chủ đề điều khoản cần tìm, bằng tiếng Việt.",
                    },
                    "doc_hint": {
                        "type": ["string", "null"],
                        "description": "Tên/gợi ý hợp đồng nếu người dùng đề cập cụ thể.",
                    },
                },
                "required": ["query", "doc_hint"],
            },
        },
    },
]

_TOOL_NAMES = {t["function"]["name"] for t in _TOOLS}


# ---------------------------------------------------------------------------
# Document resolution (regex fallback — kept for routing only)
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    return text.lower().strip()


def _extract_doc_hint(question: str) -> str | None:
    """Try to extract a document name/reference from the question.

    Handles: 'hợp đồng X', quoted strings, bare file-name tokens.
    Unicode-aware (re.UNICODE) so Vietnamese tokens like 'HĐMB' still match.
    """
    text = _normalize(question)

    # Quoted text
    quoted = re.findall(r'["“”]([^"“”]+)["“”]', question)
    if quoted:
        return quoted[0].strip()

    # "hợp đồng (số) X" / "hop dong X" / "hđ X"
    patterns = [
        r"(?:hợp đồng|hợp_đồng|hop dong|hop_dong|hđ|hd|hợpđồng)\s*(?:số|so)?\s*[:\-]?\s*([\w\-\._]+)",
        r"(?:hợp đồng|hợp_đồng|hop dong|hop_dong|hđ|hd|hợpđồng)\s*(?:tên|ten|file)?\s*[:\-]?\s*([\w\-\._]+)",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.UNICODE)
        if match:
            hint = match.group(1).strip()
            if len(hint) >= 2:
                return hint

    return None


def _find_document_by_hint(db: Session, tenant_id: str, hint: str) -> Document | None:
    """Search for a document whose file_name contains the hint."""
    if not hint or len(hint) < 2:
        return None

    doc = (
        db.query(Document)
        .filter(
            Document.tenant_id == tenant_id,
            Document.file_name.ilike(hint),
        )
        .order_by(Document.created_at.desc())
        .first()
    )
    if doc:
        return doc

    return (
        db.query(Document)
        .filter(
            Document.tenant_id == tenant_id,
            Document.file_name.ilike(f"%{hint}%"),
        )
        .order_by(Document.created_at.desc())
        .first()
    )


def _count_extracted_documents(db: Session, tenant_id: str) -> int:
    return (
        db.query(Document)
        .filter(
            Document.tenant_id == tenant_id,
            Document.status == "extracted",
        )
        .count()
    )


def _find_document_without_hint(db: Session, tenant_id: str) -> Document | None:
    """Fallback: only safe when the tenant has exactly one extracted document."""
    if _count_extracted_documents(db, tenant_id) != 1:
        return None

    return (
        db.query(Document)
        .filter(
            Document.tenant_id == tenant_id,
            Document.status == "extracted",
        )
        .order_by(Document.created_at.desc())
        .first()
    )


# ---------------------------------------------------------------------------
# Tool implementations — every query MUST filter by tenant_id
# ---------------------------------------------------------------------------

def _tool_search_terms(
    db: Session,
    tenant_id: str,
    field_name: str,
    doc_hint: str | None,
    value_contains: str | None = None,
    party_filter: str | None = None,
) -> list[dict]:
    """Return term rows for a canonical field, optionally scoped to a document hint, value substring, or party filter.

    All filters are composed with AND. `value_contains` is a substring filter on the
    requested field itself (field_name), while `party_filter` is a cross-field filter
    that restricts documents by their party field(s) before returning the requested field.
    """
    query = db.query(Term, Document).join(
        Document, Document.id == Term.document_id
    ).filter(
        Term.tenant_id == tenant_id,
        Term.field_name == field_name,
        Term.is_superseded == False,
        Term.field_value.isnot(None),
        Term.field_value != "",
    )

    if doc_hint:
        doc = _find_document_by_hint(db, tenant_id, doc_hint)
        if doc is None:
            return []
        query = query.filter(Term.document_id == doc.id)

    if value_contains:
        escaped = _escape_like(value_contains)
        query = query.filter(Term.field_value.ilike(f"%{escaped}%", escape="\\"))

    # Cross-field party filter: pre-filter documents by party fields, then return the requested field.
    if party_filter:
        safe_party = _escape_like(party_filter)
        party_doc_ids = [
            row.document_id
            for row in db.query(Term.document_id)
            .filter(
                Term.tenant_id == tenant_id,
                Term.field_name.in_(PARTY_FIELDS),
                Term.field_value.isnot(None),
                Term.field_value != "",
                Term.field_value.ilike(f"%{safe_party}%", escape="\\"),
            )
            .distinct()
            .all()
        ]
        if not party_doc_ids:
            return []
        query = query.filter(Term.document_id.in_(party_doc_ids))

    total = query.count()
    rows = query.order_by(Term.created_at.desc()).limit(_MAX_TERM_ROWS).all()
    if total > _MAX_TERM_ROWS:
        logger.info(f"chat_query search_terms truncated: tenant={tenant_id} field={field_name} total={total}")

    results = []
    for term, doc in rows:
        if not term.field_value:
            continue
        results.append(
            {
                "type": "term",
                "document_id": doc.id,
                "file_name": doc.file_name,
                "field_name": term.field_name,
                "value": term.field_value,
            }
        )

    if total > _MAX_TERM_ROWS:
        results.append(
            {
                "type": "truncation_hint",
                "document_id": None,
                "file_name": None,
                "field_name": field_name,
                "value": f"Tổng số: {total} kết quả, hiển thị {_MAX_TERM_ROWS} mới nhất.",
            }
        )
    return results


def _tool_search_obligations(
    db: Session,
    tenant_id: str,
    due_within_days: int | None,
    status: str | None,
    doc_hint: str | None,
) -> list[dict]:
    """Return obligation rows, optionally filtered by due window, status, or doc hint."""
    query = db.query(Obligation, Document).join(
        Document, Document.id == Obligation.document_id
    ).filter(
        Obligation.tenant_id == tenant_id,
    )
    if status:
        query = query.filter(Obligation.status == status)

    if doc_hint:
        doc = _find_document_by_hint(db, tenant_id, doc_hint)
        if doc is None:
            return []
        query = query.filter(Obligation.document_id == doc.id)

    if due_within_days is not None:
        try:
            cutoff = date.today() + timedelta(days=int(due_within_days))
        except (ValueError, TypeError):
            cutoff = None
        if cutoff:
            query = query.filter(Obligation.due_date <= cutoff.isoformat())

    rows = query.order_by(Obligation.due_date.asc()).all()
    results = []
    for ob, doc in rows:
        if not ob.due_date:
            continue
        results.append(
            {
                "type": "obligation",
                "document_id": doc.id,
                "file_name": doc.file_name,
                "field_name": "due_date",
                "value": ob.due_date,
                "status": ob.status,
            }
        )
    return results


def _tool_search_clauses(db: Session, tenant_id: str, query_text: str, doc_hint: str | None) -> list[dict]:
    """Return clause rows whose content matches the query text, optionally scoped to a doc hint."""
    query = db.query(Clause, Document).join(
        Document, Document.id == Clause.document_id
    ).filter(
        Clause.tenant_id == tenant_id,
    )
    if doc_hint:
        doc = _find_document_by_hint(db, tenant_id, doc_hint)
        if doc is None:
            return []
        query = query.filter(Clause.document_id == doc.id)

    # Substring match on clause content, title, or clause_num.
    pattern = f"%{query_text}%"
    query = query.filter(
        (Clause.content.ilike(pattern))
        | (Clause.title.ilike(pattern))
        | (Clause.clause_num.ilike(pattern))
    )

    rows = query.order_by(Clause.created_at.desc()).all()
    results = []
    for clause, doc in rows:
        results.append(
            {
                "type": "clause",
                "document_id": doc.id,
                "file_name": doc.file_name,
                "field_name": "clause",
                "value": clause.content,
                "clause_num": clause.clause_num,
                "clause_title": clause.title,
            }
        )
    return results


# ---------------------------------------------------------------------------
# LLM client (lazy import)
# ---------------------------------------------------------------------------

def _get_llm_client():
    """Lazy import google-genai so `import main` works without an API key.

    Returns None on any init failure so the chat path degrades gracefully to a
    deterministic fallback instead of surfacing a 500 to the PWA.
    """
    try:
        from google import genai
    except Exception:  # noqa: BLE001 - graceful degradation
        return None
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    try:
        return genai.Client(api_key=api_key)
    except Exception:  # noqa: BLE001 - missing key / invalid credentials
        return None


# ---------------------------------------------------------------------------
# LLM step 1: select tools
# ---------------------------------------------------------------------------

async def _select_tools(db: Session, tenant_id: str, question: str) -> list[dict]:
    """Ask the LLM which tools to call. Returns a list of {"name": ..., "args": ...}.

    Any failure (missing SDK, network, malformed JSON, invalid tool name) returns []
    so the caller falls back to D-08 instead of raising a 500.

    Deterministic tests can monkeypatch this function; no live call is required.
    """
    client = _get_llm_client()
    if client is None:
        return []

    try:
        from google.genai import types
    except Exception:  # noqa: BLE001
        return []

    system_prompt = (
        "Bạn là trợ lý hợp đồng. Dựa vào câu hỏi của người dùng, quyết định nên gọi "
        "công cụ nào để lấy dữ liệu từ hệ thống. Chỉ trả về JSON: "
        '{"tool_calls": [{"name": "tool_name", "args": {...}}]}. '
        "Quy tắc quan trọng: doc_hint PHẢI là tên/gợi ý filename của hợp đồng (ví dụ: 'Mau HDV FLC'), "
        "KHÔNG được là tên công ty, đối tác, hay từ khóa trong câu hỏi. "
        "Khi người dùng tìm theo tên công ty/đối tác, dùng value_contains trong search_terms, KHÔNG đưa tên công ty vào doc_hint. "
        "Khi user hỏi 'field X của hợp đồng với công ty Y', dùng party_filter=Y để lọc docs có đối tác Y, "
        "sau đó trả field X của những docs đó. "
        "Ví dụ: 'ngày hiệu lực HĐ với ALASKA' → search_terms(field_name='ngay_hieu_luc', party_filter='ALASKA'). "
        "Không tự bịa dữ liệu."
    )

    user_prompt = (
        f"Câu hỏi: {question}\n\n"
        "Các công cụ có sẵn:\n"
        + json.dumps(_TOOLS, ensure_ascii=False, indent=2)
        + "\n\nTrả về JSON với tool_calls."
    )

    try:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            temperature=0.0,
        )
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[types.Part.from_text(text=user_prompt)],
            config=config,
        )
        text = getattr(response, "text", "") or ""
    except Exception as exc:  # noqa: BLE001 - network/5xx/timeout/rate-limit
        logger.warning(f"_select_tools LLM error: {exc}")
        return []

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning(f"_select_tools LLM JSON decode error: {exc}")
        return []

    calls = parsed.get("tool_calls", []) if isinstance(parsed, dict) else []
    validated = []
    for call in calls:
        if not isinstance(call, dict):
            continue
        name = call.get("name")
        if name not in _TOOL_NAMES:
            continue
        args = call.get("args", {})
        if not isinstance(args, dict):
            args = {}
        validated.append({"name": name, "args": args})
    return validated


# ---------------------------------------------------------------------------
# LLM step 2: format answer from tool results
# ---------------------------------------------------------------------------

def _format_answer_deterministic(tool_results: list[dict]) -> str:
    """Fallback formatter used when the LLM formatting step fails.

    Returns a plain Vietnamese answer built only from the provided tool results.
    """
    parts = []
    for r in tool_results:
        if r["type"] == "truncation_hint":
            parts.append(r["value"])
            continue
        label = r.get("field_name", "")
        if r["type"] == "clause":
            label = f"{r.get('clause_num') or ''} {r.get('clause_title') or ''}".strip() or "điều khoản"
        parts.append(f"{label}: {r['value']}")
    return "\n".join(parts)


async def _format_answer(question: str, tool_results: list[dict]) -> str:
    """Ask the LLM to format a concise Vietnamese answer from the tool results.

    D-06/D-08: the LLM is instructed to only use the provided data and never
    fabricate legal interpretations. Falls back to a deterministic formatter on
    any failure so the endpoint never raises a 500.
    """
    client = _get_llm_client()
    if client is None:
        return _format_answer_deterministic(tool_results)

    try:
        from google.genai import types
    except Exception:  # noqa: BLE001
        return _format_answer_deterministic(tool_results)

    system_prompt = (
        "Bạn là trợ lý hợp đồng. Dựa vào dữ liệu công cụ được cung cấp, hãy trả lời "
        "câu hỏi bằng tiếng Việt một cách ngắn gọn. Chỉ được dùng dữ liệu đã cung cấp, "
        "không được tự bịa hoặc diễn giải pháp lý. "
        "Nếu dữ liệu có truncation_hint 'Tổng số: N kết quả, hiển thị 10 mới nhất', "
        "NÊU rõ tổng số và mời user thu hẹp, KHÔNG nói chắc chắn 'tất cả'."
    )
    user_prompt = (
        f"Câu hỏi: {question}\n\n"
        "Dữ liệu tìm được:\n"
        + json.dumps(tool_results, ensure_ascii=False, indent=2)
    )

    try:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="text/plain",
            temperature=0.0,
        )
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[types.Part.from_text(text=user_prompt)],
            config=config,
        )
        text = (getattr(response, "text", "") or "").strip()
    except Exception:  # noqa: BLE001 - network/5xx/timeout/rate-limit
        return _format_answer_deterministic(tool_results)

    return text or _format_answer_deterministic(tool_results)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def answer_question(db: Session, tenant_id: str, question: str) -> dict:
    """Answer a chat query within a tenant scope.

    Returns {"answer": str, "sources": list[dict], "found": bool}.
    """
    if not question or not question.strip():
        return {"answer": _NOT_FOUND, "sources": [], "found": False}

    # Step 1: let the LLM decide which tools to call.
    tool_calls = await _select_tools(db, tenant_id, question)

    # Step 2: execute tools.
    all_results: list[dict] = []
    for call in tool_calls:
        name = call["name"]
        args = call["args"]
        if name == "search_terms":
            all_results.extend(
                _tool_search_terms(
                    db,
                    tenant_id,
                    args.get("field_name", ""),
                    args.get("doc_hint"),
                    args.get("value_contains"),
                    args.get("party_filter"),
                )
            )
        elif name == "search_obligations":
            all_results.extend(
                _tool_search_obligations(
                    db,
                    tenant_id,
                    args.get("due_within_days"),
                    args.get("status"),
                    args.get("doc_hint"),
                )
            )
        elif name == "search_clauses":
            all_results.extend(
                _tool_search_clauses(
                    db,
                    tenant_id,
                    args.get("query", ""),
                    args.get("doc_hint"),
                )
            )

    # D-08 hard rule: if no tool returned data, return the exact not-found string.
    if not all_results:
        return {"answer": _NOT_FOUND, "sources": [], "found": False}

    # Step 3: format answer from results (D-06: only use provided data).
    answer = await _format_answer(question, all_results)
    if not answer:
        answer = _NOT_FOUND

    # Step 4: build provenance sources (exclude internal truncation hints from the response).
    sources = [
        {
            "type": r["type"],
            "document_id": r["document_id"],
            "file_name": r["file_name"],
            "field_name": r["field_name"],
            "value": r["value"],
            "clause_num": r.get("clause_num"),
            "clause_title": r.get("clause_title"),
        }
        for r in all_results
        if r["type"] != "truncation_hint"
    ]

    return {"answer": answer, "sources": sources, "found": True}
