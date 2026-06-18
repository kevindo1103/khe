"""Consent endpoints — NĐ 13/2023 (DEC-010)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.deps import get_current_user
from app.models.master import TenantUser
from app.schemas.auth import UserOut
from app.services.consent import (
    check_consent,
    record_consent,
    revoke_consent,
    VALID_PURPOSES,
)

router = APIRouter(prefix="/consent", tags=["consent"])


@router.post("", status_code=status.HTTP_201_CREATED)
def post_consent(
    payload: dict,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a consent_logged Event."""
    purpose = payload.get("purpose")
    if purpose not in VALID_PURPOSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid purpose. Must be one of: {VALID_PURPOSES}",
        )

    event = record_consent(
        db=db,
        tenant_id=user.tenant_id,
        purpose=purpose,
        actor=user.username,
        consent_text_version=payload.get("consent_text_version", "nd13-v1"),
        channel=payload.get("channel"),
        channel_target_ref=payload.get("channel_target_ref"),
        entity_id=user.id,
    )

    return {
        "purpose": purpose,
        "status": "granted",
        "consent_reference": event.consent_reference,
        "consent_text_version": event.consent_text_version,
        "at": event.created_at.isoformat(),
    }


@router.post("/revoke")
def post_revoke(
    payload: dict,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a consent_revoked Event (append-only)."""
    purpose = payload.get("purpose")
    if purpose not in VALID_PURPOSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid purpose. Must be one of: {VALID_PURPOSES}",
        )

    event = revoke_consent(
        db=db,
        tenant_id=user.tenant_id,
        purpose=purpose,
        actor=user.username,
        entity_id=user.id,
    )

    return {
        "purpose": purpose,
        "status": "revoked",
        "at": event.created_at.isoformat(),
    }


@router.get("")
def get_consents(
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the latest status for each closed-purpose enum value."""
    results = []
    for purpose in VALID_PURPOSES:
        is_granted = check_consent(db, user.tenant_id, purpose)
        # Get the latest event for this purpose to show metadata
        from app.models.tenant import Event
        latest = (
            db.query(Event)
            .filter(
                Event.tenant_id == user.tenant_id,
                Event.purpose == purpose,
            )
            .order_by(Event.created_at.desc(), Event.id.desc())
            .first()
        )
        entry = {
            "purpose": purpose,
            "status": "granted" if is_granted else "none",
        }
        if latest:
            entry["consent_reference"] = latest.consent_reference
            entry["consent_text_version"] = latest.consent_text_version
            entry["channel"] = latest.channel
            entry["channel_target_ref"] = latest.channel_target_ref
            entry["at"] = latest.created_at.isoformat()
        results.append(entry)

    return results
