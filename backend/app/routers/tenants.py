"""Tenant profile endpoints (#155, DEC-030; #213 journey).

PATCH /tenants/me/legal_name — SME declares legal entity name for auto-match.
GET   /tenants/me           — tenant summary incl. onboarding journey state.
PATCH /tenants/me/journey   — FE advances journey_stage (forward-only).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_master_db
from app.deps import get_current_user
from app.models.master import Tenant, TenantProfile, TenantUser
from app.schemas.tenants import ComplianceProfileIn, ComplianceProfileOut
from app.services import tenant_journey

router = APIRouter(prefix="/tenants", tags=["tenants"])


class LegalNameIn(BaseModel):
    legal_name: str


class LegalNameOut(BaseModel):
    ok: bool
    legal_name: str | None


class TenantMeOut(BaseModel):
    id: str
    name: str
    plan: str
    is_active: bool
    journey_stage: str
    is_first_session: bool


class JourneyAdvanceIn(BaseModel):
    journey_stage: str


class JourneyOut(BaseModel):
    journey_stage: str
    is_first_session: bool


@router.get("/me", response_model=TenantMeOut)
def get_tenant_me(
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_master_db),
):
    """Tenant summary for the authenticated user, incl. journey state (#213)."""
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.")
    return TenantMeOut(
        id=tenant.id,
        name=tenant.name,
        plan=tenant.plan,
        is_active=tenant.is_active,
        journey_stage=tenant.journey_stage or "NEW",
        is_first_session=bool(tenant.is_first_session),
    )


@router.patch("/me/journey", response_model=JourneyOut)
def advance_journey(
    body: JourneyAdvanceIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_master_db),
):
    """Advance the onboarding journey_stage. Forward-only — backward = 409 (#213)."""
    target = body.journey_stage
    if not tenant_journey.is_valid_stage(target):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid journey_stage. Must be one of: {tenant_journey.JOURNEY_STAGES}",
        )
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.")

    current = tenant.journey_stage or "NEW"
    if target != current and not tenant_journey.is_forward(current, target):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Backward journey transition not allowed ({current} → {target}).",
        )
    tenant_journey.advance_stage(db, user.tenant_id, target)
    db.refresh(tenant)
    return JourneyOut(
        journey_stage=tenant.journey_stage or "NEW",
        is_first_session=bool(tenant.is_first_session),
    )


@router.get("/me/legal_name", response_model=LegalNameOut)
def get_legal_name(
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_master_db),
):
    """Read current legal_name (null if not set yet)."""
    profile = (
        db.query(TenantProfile)
        .filter(TenantProfile.tenant_id == user.tenant_id)
        .first()
    )
    return {"ok": True, "legal_name": profile.legal_name if profile else None}


@router.patch("/me/legal_name", response_model=LegalNameOut)
def update_legal_name(
    body: LegalNameIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_master_db),
):
    """SME declares legal entity name → upsert tenant_profiles."""
    profile = (
        db.query(TenantProfile)
        .filter(TenantProfile.tenant_id == user.tenant_id)
        .first()
    )
    if profile:
        profile.legal_name = body.legal_name
    else:
        db.add(TenantProfile(tenant_id=user.tenant_id, legal_name=body.legal_name))
    db.commit()
    return {"ok": True, "legal_name": body.legal_name}


@router.get("/me/compliance-profile", response_model=ComplianceProfileOut)
def get_compliance_profile(
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_master_db),
):
    """Read the compliance profile for the current tenant (#495, #529 upsert)."""
    profile = db.query(TenantProfile).filter_by(tenant_id=user.tenant_id).first()
    if profile is None:
        return ComplianceProfileOut()
    return profile


@router.put("/me/compliance-profile", response_model=ComplianceProfileOut)
def update_compliance_profile(
    body: ComplianceProfileIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_master_db),
):
    """Update the compliance profile for the current tenant (#495, #529 upsert)."""
    profile = db.query(TenantProfile).filter_by(tenant_id=user.tenant_id).first()
    if profile is None:
        profile = TenantProfile(tenant_id=user.tenant_id)
        db.add(profile)
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(profile, field, val)
    db.commit()
    db.refresh(profile)
    return profile
