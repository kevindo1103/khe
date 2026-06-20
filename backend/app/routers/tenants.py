"""Tenant profile endpoints (#155, DEC-030).

PATCH /tenants/me/legal_name — SME declares legal entity name for auto-match.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_master_db
from app.deps import get_current_user
from app.models.master import TenantProfile, TenantUser

router = APIRouter(prefix="/tenants", tags=["tenants"])


class LegalNameIn(BaseModel):
    legal_name: str


class LegalNameOut(BaseModel):
    ok: bool
    legal_name: str


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
