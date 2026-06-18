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
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Obligation(TenantBase):
    __tablename__ = "obligations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    description = Column(Text, nullable=False)
    obligation_type = Column(String, default="once")  # "once" | "monthly" | "quarterly" | "yearly" | "open_ended_review"
    due_date = Column(String, nullable=True)
    status = Column(String, default="pending")          # "pending" | "done" | "overdue" | "cancelled"
    remind_before_days = Column(Integer, default=30)
    # ── tenant_002 chain resolution ──
    source_doc_chain = Column(Text, nullable=True)       # JSON list of doc IDs in chain order
    resolution_method = Column(String, nullable=True)    # e.g. "last_writer_wins"
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
    created_at = Column(DateTime, server_default=func.now())


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
