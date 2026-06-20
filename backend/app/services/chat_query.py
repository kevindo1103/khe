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

from app.models.tenant import ChatQueryLog, Clause, Document, Obligation, Term


logger = logging.getLogger(__name__)
_NOT_FOUND = "Không tìm thấy thông tin này trong hồ sơ của bạn."

# Canonical party field name.  `CANONICAL_FIELDS` in `modules/extraction/schemas.py`
# lists `doi_tac` as the single party/bên ký field, so no alias expansion is needed.
PARTY_FIELDS: tuple[str, ...] = ("doi_tac",)

# Max rows returned by search_terms before truncation.
_MAX_TERM_ROWS = 10

# D-08: detect LLM paraphrases of "not found" so we can force the exact string.
# Narrowed to avoid colliding with valid contract content (e.g. thoi_han_hd="không xác định thời hạn").
_NOT_FOUND_PATTERNS = re.compile(
    r"(không\s*tìm\s*thấy|không\s*có\s*thông\s*tin|chưa\s*có\s*dữ\s*liệu)",
    re.IGNORECASE | re.UNICODE,
)


def _is_negative_answer(answer: str) -> bool:
    """Return True if the LLM answer is a D-08 paraphrase (or empty)."""
    if not answer or not answer.strip():
        return True
    return bool(_NOT_FOUND_PATTERNS.search(answer))

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
                    "doc_type_filter": {
                        "type": ["string", "null"],
                        "description": (
                            "Lọc theo nhóm loại hợp đồng. "
                            "Giá trị: dan_su | thuong_mai | lao_dong | bat_dong_san | "
                            "van_tai_logistics | xay_dung | cong_nghe_ip | tai_chinh | bao_dam | hanh_chinh. "
                            "Dùng khi user hỏi về 'hợp đồng lao động', 'HĐ xây dựng', v.v. "
                            "Null nếu không lọc theo loại."
                        ),
                    },
                },
                "required": ["field_name", "doc_hint", "value_contains", "party_filter", "doc_type_filter"],
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
                    "due_from": {
                        "type": ["string", "null"],
                        "description": "Ngày bắt đầu khoảng tìm kiếm (ISO YYYY-MM-DD), inclusive. Dùng cho query theo lịch ('tháng này', 'quý 2').",
                    },
                    "due_to": {
                        "type": ["string", "null"],
                        "description": "Ngày kết thúc khoảng tìm kiếm (ISO YYYY-MM-DD), inclusive.",
                    },
                    "obligation_type": {
                        "type": ["string", "null"],
                        "description": "Loại nghĩa vụ: payment, delivery, handover, expiration, renewal, review, warranty, other. Null = tất cả.",
                    },
                    "direction": {
                        "type": ["string", "null"],
                        "description": "Hướng nghĩa vụ: nghĩa_vụ (bạn phải làm) hoặc quyền_lợi (đối tác phải làm cho bạn). Null = cả hai.",
                    },
                    "doc_type_filter": {
                        "type": ["string", "null"],
                        "description": (
                            "Lọc obligations theo nhóm loại HĐ. "
                            "Cùng giá trị với search_terms: dan_su | thuong_mai | lao_dong | bat_dong_san | "
                            "van_tai_logistics | xay_dung | cong_nghe_ip | tai_chinh | bao_dam | hanh_chinh. "
                            "Null nếu không lọc theo loại."
                        ),
                    },
                },
                "required": ["due_within_days", "status", "doc_hint", "due_from", "due_to", "obligation_type", "direction", "doc_type_filter"],
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
    doc_type_filter: str | None = None,
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

    if doc_type_filter:
        type_doc_ids = [
            row.document_id
            for row in db.query(Term.document_id)
            .filter(
                Term.tenant_id == tenant_id,
                Term.field_name == "doc_type_group",
                Term.field_value == doc_type_filter,
            )
            .distinct()
            .all()
        ]
        if not type_doc_ids:
            return []
        query = query.filter(Term.document_id.in_(type_doc_ids))

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
    due_from: str | None = None,
    due_to: str | None = None,
    obligation_type: str | None = None,
    direction: str | None = None,
    doc_type_filter: str | None = None,
) -> list[dict]:
    """Return obligation rows, optionally filtered by due window, status, doc hint, or date range."""
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

    if due_from:
        query = query.filter(Obligation.due_date >= due_from)
    if due_to:
        query = query.filter(Obligation.due_date <= due_to)

    if obligation_type:
        query = query.filter(Obligation.obligation_type == obligation_type)
    if direction:
        query = query.filter(Obligation.direction == direction)

    if doc_type_filter:
        type_doc_ids = [
            row.document_id
            for row in db.query(Term.document_id)
            .filter(
                Term.tenant_id == tenant_id,
                Term.field_name == "doc_type_group",
                Term.field_value == doc_type_filter,
            )
            .distinct()
            .all()
        ]
        if not type_doc_ids:
            return []
        query = query.filter(Obligation.document_id.in_(type_doc_ids))

    if due_within_days is not None:
        try:
            today_str = date.today().isoformat()
            cutoff = (date.today() + timedelta(days=int(due_within_days))).isoformat()
        except (ValueError, TypeError):
            cutoff = None
        if cutoff:
            query = query.filter(
                Obligation.due_date >= today_str,
                Obligation.due_date <= cutoff,
            )

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

def _build_router_system_prompt(today: date) -> str:
    """Build the system prompt for the LLM router, including the reference date."""
    today_str = today.isoformat()
    return (
        "Bạn là trợ lý hợp đồng. Dựa vào câu hỏi của người dùng, quyết định nên gọi "
        "công cụ nào để lấy dữ liệu từ hệ thống. Chỉ trả về JSON: "
        '{"tool_calls": [{"name": "tool_name", "args": {...}}]}. '
        "Không tự bịa dữ liệu.\n"
        "BẮT BUỘC — quy tắc tên công ty/đối tác:\n"
        "- party_filter PHẢI nhận tên công ty/đối tác/cá nhân (tiếng Việt có dấu được chấp nhận: 'Danh Việt', 'Hán Thị Nga').\n"
        "- doc_hint CHỈ nhận tên file hợp đồng (vd: 'Mau HDV FLC'), KHÔNG phải tên công ty.\n"
        "- Khi user hỏi 'field X của HĐ với công ty Y' → party_filter='Y', field_name='X'.\n"
        "Ví dụ mapping:\n"
        "- 'ngày hiệu lực HĐ với Danh Việt' → search_terms(field_name='ngay_hieu_luc', party_filter='Danh Việt')\n"
        "- 'giá trị HĐ với công ty Hán Thị Nga' → search_terms(field_name='gia_tri_hd', party_filter='Hán Thị Nga')\n"
        "- 'ngày hiệu lực HĐ với ALASKA' → search_terms(field_name='ngay_hieu_luc', party_filter='ALASKA')\n"
        "- 'HĐ với ALASKA năm 2021' → search_terms(field_name='ngay_hieu_luc', party_filter='ALASKA', value_contains='2021')\n"
        f"Hôm nay là {today_str}. "
        "Quy tắc chuyển cụm từ lịch tiếng Việt thành due_from/due_to ISO (YYYY-MM-DD):\n"
        "- 'tháng này' → due_from=ngày 1 tháng hiện tại, due_to=ngày cuối tháng hiện tại\n"
        "- 'tháng sau' → due_from=ngày 1 tháng kế tiếp, due_to=ngày cuối tháng kế tiếp\n"
        "- 'quý này' / 'quý sau' → ngày đầu và cuối của quý tương ứng\n"
        "- 'tuần này' / 'tuần tới' → từ thứ 2 đến chủ nhật của tuần (ISO week, Thứ 2 là đầu tuần)\n"
        "- 'X ngày tới' / 'sắp tới' → dùng due_within_days=X, KHÔNG dùng due_from/due_to\n"
        "- 'sắp hết hạn' / 'sắp đến hạn' / 'sắp đáo hạn' → search_obligations(due_within_days=30)\n"
        "  (chỉ trả từ hôm nay đến N ngày tới, KHÔNG bao gồm đã quá hạn)\n"
        "- 'đã quá hạn' / 'quá hạn' / 'trễ hạn' → search_obligations(status='overdue')\n"
        "  (KHÔNG dùng due_within_days)\n"
        "- 'lịch sử nghĩa vụ' / 'tất cả nghĩa vụ' → search_obligations(status=null)\n"
        "- 'nghĩa vụ phải trả' / 'tôi cần làm gì' → search_obligations(direction='nghĩa_vụ')\n"
        "- 'quyền lợi' / 'đối tác phải làm gì cho tôi' → search_obligations(direction='quyền_lợi')\n"
        "- 'thanh toán sắp tới' → search_obligations(obligation_type='payment', due_within_days=30)\n"
        "- 'HĐ lao động có bảo hiểm không?' → search_terms(field_name='chu_ky_dong_bao_hiem', doc_type_filter='lao_dong', doc_hint=null)\n"
        "- 'Obligations xây dựng tháng tới?' → search_obligations(due_within_days=30, doc_type_filter='xay_dung', obligation_type=null)\n"
        "- 'Tất cả HĐ thuê nhà?' → search_terms(field_name='ngay_het_han', doc_type_filter='bat_dong_san', doc_hint=null)\n"
    )


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

    system_prompt = _build_router_system_prompt(date.today())

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

def _log_chat_query(
    db: Session,
    tenant_id: str,
    question: str,
    tool_calls: list[dict],
    found: bool,
    result_count: int,
) -> None:
    """Write one chat_query_log row (DEC-028). Isolated in try/except —
    a logging failure must never break the chat response."""
    try:
        log = ChatQueryLog(
            tenant_id=tenant_id,
            question=question,
            tool_calls=json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None,
            found=found,
            result_count=result_count,
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()
        logger.warning("chat_query_log write failed for tenant=%s", tenant_id, exc_info=True)


def _safe_log_chat_query(db, tenant_id, question, tool_calls, found, result_count):
    """Wrapper that never raises — defense in depth for answer_question call sites."""
    try:
        _log_chat_query(db, tenant_id, question, tool_calls, found, result_count)
    except Exception:
        logger.warning("chat_query_log failed for tenant=%s", tenant_id, exc_info=True)


async def answer_question(db: Session, tenant_id: str, question: str) -> dict:
    """Answer a chat query within a tenant scope.

    Returns {"answer": str, "sources": list[dict], "found": bool}.
    """
    if not question or not question.strip():
        _safe_log_chat_query(db, tenant_id, question, [], False, 0)
        return {"answer": _NOT_FOUND, "sources": [], "found": False}

    # Step 1: let the LLM decide which tools to call.
    tool_calls = await _select_tools(db, tenant_id, question)

    # PII-safe routing log (NĐ 13/2023): log tool name + field_name + arg keys present,
    # NOT raw arg values (party_filter/value_contains may contain personal names).
    logger.info(
        "chat_query routed: tenant=%s tools=%s",
        tenant_id,
        [
            {
                "name": c["name"],
                "field_name": c["args"].get("field_name"),
                "args_present": sorted(k for k, v in c["args"].items() if v is not None),
            }
            for c in tool_calls
        ],
    )

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
                    args.get("doc_type_filter"),
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
                    args.get("due_from"),
                    args.get("due_to"),
                    args.get("obligation_type"),
                    args.get("direction"),
                    args.get("doc_type_filter"),
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
        _safe_log_chat_query(db, tenant_id, question, tool_calls, False, 0)
        return {"answer": _NOT_FOUND, "sources": [], "found": False}

    # Step 3: format answer from results (D-06: only use provided data).
    answer = await _format_answer(question, all_results)

    # D-08: detect LLM paraphrases of "not found" and force the exact string.
    # KHÔNG re-introduce paraphrase path (D-08) — any negative phrasing → exact triple.
    if _is_negative_answer(answer):
        _safe_log_chat_query(db, tenant_id, question, tool_calls, False, 0)
        return {"answer": _NOT_FOUND, "sources": [], "found": False}

    # Step 4: build provenance sources (exclude internal truncation hints from the response).
    sources = [
        {
            "type": r["type"],
            "document_id": r["document_id"],
            "file_name": r["file_name"],
            "field_name": r["field_name"],
            "value": r["value"],
            "status": r.get("status"),
            "clause_num": r.get("clause_num"),
            "clause_title": r.get("clause_title"),
        }
        for r in all_results
        if r["type"] != "truncation_hint"
    ]

    _safe_log_chat_query(db, tenant_id, question, tool_calls, True, len(sources))
    return {"answer": answer, "sources": sources, "found": True}
