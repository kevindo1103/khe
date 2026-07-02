"""
tenant_models.py — SQLAlchemy models for per-tenant databases.

Stored in tenants/<slug>.db (never in master.db).
"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.db.database import TenantBase


class Document(TenantBase):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    doc_type = Column(String, nullable=True)           # "lease" | "supply" | "labor" | ...
    status = Column(String, default="pending")         # "pending" | "processing" | "done" | "error"
    # User-explicit review confirm (#238, D-02). NULL = not yet confirmed → counts
    # toward the NEEDS_REVIEW gate; set on POST /documents/{id}/confirm.
    confirmed_by_user_at = Column(DateTime, nullable=True)
    # Evidence doc flag (#302, DEC-048 P2): biên bản bàn giao/nghiệm thu. Skips
    # full vision extraction (metadata + file link only). Conservative PII default.
    is_evidence = Column(Boolean, default=False)
    contains_personal_data = Column(Boolean, default=False)  # DEC-039 firm-gate guard
    # Extraction cost tracking (#255 pilot monitoring). NULL for pre-migration /
    # not-yet-extracted docs. Set on each successful extraction.
    extraction_provider = Column(String, nullable=True)    # "gemini_flash" | "claude_haiku" | "claude_sonnet"
    extraction_tokens_in = Column(Integer, nullable=True)
    extraction_tokens_out = Column(Integer, nullable=True)
    extraction_cost_vnd = Column(Float, nullable=True)
    # ── tenant_019: extraction metrics (#346) ──
    extraction_model = Column(String, nullable=True)       # "gemini-2.5-flash" / "claude-haiku-4.5"
    extraction_latency_ms = Column(Float, nullable=True)   # total extraction latency in ms
    extraction_warnings = Column(Text, nullable=True)      # JSON array of warning strings
    # ── tenant_020: extraction progress (#360) ──
    processing_stage = Column(String, nullable=True)       # queued|ocr|llm|saving|done|failed|retry_needed|two_pass_skeleton|two_pass_fill
    processing_progress = Column(Integer, nullable=True)   # 0-100
    # ── tenant_021: contract title + number (#363) ──
    title = Column(String, nullable=True)                  # extracted contract title (tieu_de_hd term)
    contract_number = Column(String, nullable=True)        # extracted contract number (so_hop_dong term)
    # ── tenant_024: date taxonomy (#369) ──
    signing_date = Column(String, nullable=True)           # ngay_ky term value (ISO date)
    commencement_date = Column(String, nullable=True)      # ngay_khai_truong term value (ISO date)
    # ── tenant_025: contract term + lifecycle status (#371) ──
    contract_term = Column(String, nullable=True)          # raw duration e.g. "12 tháng" / "vô thời hạn"
    lifecycle_status = Column(String, nullable=True)       # active|expiring|expired|settled|suspended
    # ── tenant_028: signature detection (#368, R5) ──
    has_signature = Column(Boolean, nullable=True)         # True if doc has physical/digital signature
    signature_pages = Column(Text, nullable=True)          # JSON list e.g. "[1, 3]"
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Term(TenantBase):
    __tablename__ = "terms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    field_name = Column(String, nullable=False)        # e.g. "effective_date", "expiry_date"
    field_value = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)          # AI confidence 0..1
    # ── tenant_002 chain / review ──
    needs_review = Column(Boolean, default=False)
    is_superseded = Column(Boolean, default=False)
    overrides_term_id = Column(Integer, ForeignKey("terms.id"), nullable=True)
    inherited_from_doc_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    # ── tenant_011: Stage 3 review ref-link trust gate (#217, FR-EX-05) ──
    # Per-field source anchor. NULL → FE renders plain text (graceful degrade,
    # no dead link). Populated by the VisionExtractionProvider (KHE_AI scope).
    ref = Column(Text, nullable=True)                  # display label, e.g. "Điều 8" / "tr.1 §A"
    page_num = Column(Integer, nullable=True)          # 1-based page for scroll-to
    bbox = Column(Text, nullable=True)                 # JSON [x0,y0,x1,y1] normalized 0..1
    # Provenance (#258): how this term's value originated.
    source = Column(String, nullable=True)             # "extracted" | "remap" | "manual" | NULL(legacy)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


OBLIGATION_STATUSES = [
    "pending", "in_progress", "partial", "done", "cancelled", "waiting_trigger",
    # #313 cascade-past: child due in past → awaiting SME confirm ("đã xong?", D-02)
    "awaiting_confirmation",
]


class Obligation(TenantBase):
    __tablename__ = "obligations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    description = Column(Text, nullable=False)
    recurrence = Column(String, default="once")          # cadence: "once" | "open_ended_review"
    obligation_type = Column(String, default="other")    # category (DEC-027): "payment" | "expiration" | "renewal" | "review" | "warranty" | "other"
    direction = Column(String, nullable=True)            # DEC-030: "nghĩa_vụ" | "quyền_lợi" | NULL (needs_review)
    obligor = Column(String, nullable=True)              # DEC-030: role_label from parties[]
    due_date = Column(String, nullable=True)
    status = Column(String, default="pending")          # "pending" | "done" | "overdue" | "cancelled"
    remind_before_days = Column(Integer, default=30)
    # ── tenant_002 chain resolution ──
    source_doc_chain = Column(Text, nullable=True)       # JSON list of doc IDs in chain order
    resolution_method = Column(String, nullable=True)    # e.g. "last_writer_wins"
    # ── tenant_006: DEC-030 Phase 2 — series + event-chain ──
    milestone_series_id = Column(Text, nullable=True)    # same series_id for all installments of one chain
    milestone_index = Column(Integer, nullable=True)     # 1-based; None if not a series
    milestone_total = Column(Integer, nullable=True)
    milestone_trigger = Column(String, default="date")   # "date" | "event"
    trigger_condition = Column(Text, nullable=True)      # verbatim from contract if trigger=event
    trigger_delay_days = Column(Integer, nullable=True)  # e.g. 30 for "30 ngày sau nghiệm thu"
    trigger_obligation_id = Column(Integer, nullable=True)  # self-ref to obligations.id
    amount_raw = Column(Text, nullable=True)             # raw string, not parsed
    # Snooze (#214): suppress this obligation's reminder until the given time;
    # NULL = not snoozed. Auto-expires (scheduler resumes once now() passes it) —
    # snooze never mutates status/due_date (D-07: obligation truth unchanged).
    snoozed_until = Column(DateTime, nullable=True)
    # Provenance (#301): how this obligation originated.
    source = Column(String, nullable=True)             # "ai_extracted" | "user_manual" | "ai_re_derived" | NULL(legacy)
    # Fulfillment capture (#302, DEC-048 G2/P3): user-entered completion evidence.
    fulfilled_at = Column(DateTime, nullable=True)     # authoritative completion date (T2)
    fulfilled_by = Column(String, nullable=True)       # username or "operator-for-<username>" (P3)
    evidence_doc_ids = Column(Text, nullable=True)     # JSON list[int] of evidence document IDs
    # Clause provenance (#303, DEC-048 §13): links obligation to the clause that drove it.
    source_clause_num = Column(String, nullable=True)  # FK-ish to Clause.clause_num in same doc
    derived_from = Column(String, nullable=True)       # "original" | "user_edit"
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Party(TenantBase):
    __tablename__ = "parties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=True, index=True)
    party_type = Column(String, nullable=True)         # "landlord" | "supplier" | "employee" | ...
    contact_info = Column(Text, nullable=True)
    # ── tenant_008: DEC-030 per-document parties + role_label (#155) ──
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    role_label = Column(Text, nullable=True)           # role as stated IN the contract
    created_at = Column(DateTime, server_default=func.now())
    # ── tenant_022: extended party details + self-mapping (#364) ──
    address = Column(Text, nullable=True)              # địa chỉ pháp lý
    contact = Column(String, nullable=True)            # SĐT / email liên hệ
    representative = Column(String, nullable=True)     # người đại diện (tên + chức vụ)
    tax_code = Column(String, nullable=True)           # mã số thuế (MST)
    is_self = Column(Boolean, default=False)           # auto-mapped from tenant_profile.legal_name
    aliases = Column(Text, nullable=True)              # JSON array of alternative names/abbreviations


class Event(TenantBase):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)        # "document" | "term" | "obligation" | "reminder" | "consent"
    entity_id = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)         # "created" | "updated" | "deleted" | "reminder_sent" | "consent_logged" | "consent_revoked" | "extraction_performed" | ...
    actor = Column(String, nullable=True)               # username or "system"
    payload = Column(Text, nullable=True)               # JSON blob
    # ── Consent group (tenant_002) ──
    purpose = Column(String, nullable=True)             # "vision_extraction" | "reminder_send" | "firm_partner_access"
    consent_reference = Column(String, nullable=True)
    consent_text_version = Column(String, nullable=True)  # e.g. "nd13-v1"
    channel = Column(String, nullable=True)             # "telegram" | "email" (reminder_send only)
    channel_target_ref = Column(String, nullable=True)   # telegram_chat_id or email address
    created_at = Column(DateTime, server_default=func.now())


class Branch(TenantBase):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class Employee(TenantBase):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    employee_code = Column(String, nullable=False, unique=True)
    full_name = Column(String, nullable=False)
    position = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class Clause(TenantBase):
    __tablename__ = "clauses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    clause_num = Column(String, nullable=True)        # e.g. "Điều 8", "Khoản 2.3"
    title = Column(String, nullable=True)             # e.g. "Chấm dứt hợp đồng"
    content = Column(Text, nullable=False)            # full clause text (user-editable, D-07)
    page_num = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    # ── Inline edit (#324, D-07) ──
    edited_by_user = Column(String, nullable=True)    # username who last edited
    edited_at = Column(DateTime, nullable=True)       # when last edited
    original_content = Column(Text, nullable=True)    # AI-extracted original (snapshot on first edit)
    # ── tenant_023: clause hierarchy (#365) ──
    parent_id = Column(Integer, nullable=True)  # self-ref to clauses.id; app-level (no FK — avoids delete-order issues)
    level = Column(Integer, nullable=True)            # 0=top, 1=sub, 2=sub-sub (derived, not user-editable)
    clause_path = Column(String, nullable=True)       # dotted path e.g. "2.1.1" (for hierarchy sort)
    # ── tenant_029: two-pass map-reduce content state (#449, mini-sprint #443) ──
    # NULL = single-call extraction (legacy path, content already present at insert).
    # "skeleton" = Pass 1 hierarchy only, content="" pending fill.
    # "filled" = Pass 2 verbatim content persisted.
    # "truncated" = Pass 2 hit MAX_TOKENS on this section; needs Pass 3 paragraph-split retry.
    content_status = Column(String, nullable=True)


class Definition(TenantBase):
    """Glossary term extracted from a document's Định nghĩa section (#372, R9)."""
    __tablename__ = "definitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    term = Column(String, nullable=False)               # e.g. "Năm Tài chính", "Khách sạn"
    definition = Column(Text, nullable=False)           # full definition text
    source_clause_num = Column(String, nullable=True)   # e.g. "Điều 1" or clause_path
    source_clause_id = Column(Integer, nullable=True)   # app-level ref to clauses.id (no FK constraint)
    # ── D-07 edit tracking ──
    edited_by_user = Column(String, nullable=True)
    edited_at = Column(DateTime, nullable=True)
    original_definition = Column(Text, nullable=True)   # AI-extracted snapshot on first edit
    original_term = Column(String, nullable=True)       # AI-extracted term snapshot on first edit
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ClauseCrossRef(TenantBase):
    """Intra-doc or cross-doc reference detected in clause content (#373, R10)."""
    __tablename__ = "clause_cross_refs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    source_clause_id = Column(Integer, nullable=False)     # app-level ref to clauses.id
    ref_text = Column(String, nullable=False)              # raw text, e.g. "theo Điều 5"
    ref_type = Column(String, nullable=False)              # "clause" | "appendix" | "document"
    target_clause_id = Column(Integer, nullable=True)      # resolved → clauses.id
    target_clause_path = Column(String, nullable=True)     # resolved → clause_path, e.g. "5"
    target_doc_id = Column(Integer, nullable=True)         # resolved → documents.id (appendix)
    is_orphan = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())


class DocumentRelationship(TenantBase):
    __tablename__ = "document_relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    from_doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    to_doc_id = Column(Integer, ForeignKey("documents.id"), nullable=True)   # null = orphan amendment (DEC-021)
    unresolved_ref = Column(String, nullable=True)                            # extracted hint when to_doc missing
    relationship_type = Column(String, nullable=False)                        # "amends" | "references_framework" (MVP)
    status = Column(String, default="pending")                               # "pending" | "confirmed"
    confirmed_by_sme = Column(Boolean, default=False)                          # D-02 gate
    confidence = Column(Float, nullable=True)                                  # AI suggestion score
    created_at = Column(DateTime, server_default=func.now())


class ChatQueryLog(TenantBase):
    """Per-tenant chat query log for DEC-028 learning loop.

    Raw PII (question + tool args) lives here — tenant-isolated, purgeable.
    NOT in the append-only events ledger (NĐ 13/2023 compliance debt).
    """
    __tablename__ = "chat_query_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    question = Column(Text, nullable=False)
    tool_calls = Column(Text, nullable=True)          # JSON: [{"name":..., "args":{...}}]
    found = Column(Boolean, nullable=False, server_default="0")
    result_count = Column(Integer, server_default="0")
    created_at = Column(DateTime, server_default=func.now())
    # Tokenomics (#164)
    input_tokens = Column(Integer, server_default="0")
    output_tokens = Column(Integer, server_default="0")
    cost_vnd = Column(Float, server_default="0.0")
    llm_calls = Column(Integer, server_default="0")


class ChatSession(TenantBase):
    """Result-seeded progressive chat state (DEC-031 v2, #201).

    One row per device/tab conversation thread. ``state_json`` holds POINTER IDs
    only (active_doc_ids / active_obligation_ids / working_set_label /
    last_tool_call) — never PII text — so it is a soft prior for the next query,
    not a memory of content. TTL 24h via ``expires_at`` + weekly cleanup job.
    """
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    session_id = Column(String, nullable=False, unique=True)  # UUID from FE localStorage
    state_json = Column(Text, nullable=False)                 # pointer IDs only, NO PII
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime, nullable=True)
