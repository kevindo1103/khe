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
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Obligation(TenantBase):
    __tablename__ = "obligations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    description = Column(Text, nullable=False)
    obligation_type = Column(String, default="once")  # "once" | "monthly" | "quarterly" | "yearly"
    due_date = Column(String, nullable=True)
    status = Column(String, default="pending")          # "pending" | "done" | "overdue" | "cancelled"
    remind_before_days = Column(Integer, default=30)
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
    entity_type = Column(String, nullable=False)        # "document" | "term" | "obligation" | "reminder"
    entity_id = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)         # "created" | "updated" | "deleted" | "reminder_sent" | ...
    actor = Column(String, nullable=True)               # username or "system"
    payload = Column(Text, nullable=True)               # JSON blob
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
