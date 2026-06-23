"""
master_models.py — SQLAlchemy models for the master (tenant registry) database.

Stored in master.db (never in per-tenant DBs).
"""
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import MasterBase


class Tenant(MasterBase):
    """One row per store/tenant registered on the platform."""
    __tablename__ = "tenants"

    id = Column(String, primary_key=True)            # slug: "sme-abc"
    name = Column(String, nullable=False)              # display name
    db_path = Column(String, nullable=False)           # relative: "tenants/sme-abc.db"
    plan = Column(String, default="starter")           # "starter" | "pro" | "enterprise"
    is_active = Column(Boolean, default=True)
    # Onboarding journey state machine (#213) — monotonic forward-only:
    # NEW → EXTRACTING → NEEDS_REVIEW → CONFIRMED → ACTIVATED → STEADY.
    journey_stage = Column(String, nullable=False, server_default="NEW")
    # First-session nav-lock; cleared atomically when the stage reaches ACTIVATED.
    is_first_session = Column(Boolean, nullable=False, server_default="1")
    # Ingest quota (FR-TN-01 / D-11, #63) — prevents vision-extraction cost
    # runaway. doc_quota firm-configurable per SME; counter resets calendar 1st.
    doc_quota = Column(Integer, nullable=False, server_default="500")
    docs_used_month = Column(Integer, nullable=False, server_default="0")
    quota_reset_at = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")
    firm_access = relationship("FirmTenantAccess", back_populates="tenant", cascade="all, delete-orphan")


class TenantUser(MasterBase):
    """Users who can log in to a specific tenant's Khế portal."""
    __tablename__ = "tenant_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="staff")             # "staff" | "manager" | "admin"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    tenant = relationship("Tenant", back_populates="users")

    __table_args__ = (UniqueConstraint("tenant_id", "username", name="uq_tenant_username"),)


class FirmPartner(MasterBase):
    """Law firm / tax agent partner."""
    __tablename__ = "firm_partners"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    tenant_access = relationship("FirmTenantAccess", back_populates="firm", cascade="all, delete-orphan")


class FirmTenantAccess(MasterBase):
    """Consent-based cross-tenant access granted to a firm partner."""
    __tablename__ = "firm_tenant_access"

    id = Column(Integer, primary_key=True, autoincrement=True)
    firm_id = Column(Integer, ForeignKey("firm_partners.id"), nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False)
    consent_status = Column(String, default="pending")   # "pending" | "granted" | "revoked"
    granted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    firm = relationship("FirmPartner", back_populates="tenant_access")
    tenant = relationship("Tenant", back_populates="firm_access")

    __table_args__ = (UniqueConstraint("firm_id", "tenant_id", name="uq_firm_tenant"),)


class TenantProfile(MasterBase):
    """Operational profile for a tenant — legal name for auto-match (DEC-030)."""
    __tablename__ = "tenant_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), unique=True, nullable=False)
    legal_name = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
