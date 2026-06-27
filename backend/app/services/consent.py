"""
Consent service — NĐ 13/2023 compliance helpers (DEC-010).

All operations use the tenant-scoped session. Writes to the per-tenant
`events` table (append-only: revoke = new row, never UPDATE/DELETE).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.tenant import Event

# Closed purpose enum — do not extend without compliance review (§A.1)
# obligation_fulfillment: NĐ 13 audit log for evidence attachment (#302, DEC-048 P4). No consent gate.
VALID_PURPOSES = {"vision_extraction", "reminder_send", "firm_partner_access", "obligation_fulfillment"}


def _generate_consent_reference() -> str:
    return f"consent-{uuid.uuid4().hex[:16]}"


def check_consent(db: Session, tenant_id: str, purpose: str) -> bool:
    """Return True if the latest consent_logged for (tenant, purpose)
    is NOT later superseded by a consent_revoked."""
    if purpose not in VALID_PURPOSES:
        return False

    # Latest consent_logged
    logged = (
        db.query(Event)
        .filter(
            Event.tenant_id == tenant_id,
            Event.event_type == "consent_logged",
            Event.purpose == purpose,
        )
        .order_by(Event.created_at.desc(), Event.id.desc())
        .first()
    )
    if logged is None:
        return False

    # Any consent_revoked after it?
    revoked = (
        db.query(Event)
        .filter(
            Event.tenant_id == tenant_id,
            Event.event_type == "consent_revoked",
            Event.purpose == purpose,
        )
        .order_by(Event.created_at.desc(), Event.id.desc())
        .first()
    )
    if revoked is not None and revoked.created_at > logged.created_at:
        return False
    return True


def record_consent(
    db: Session,
    tenant_id: str,
    purpose: str,
    actor: str,
    consent_text_version: str = "nd13-v1",
    channel: str | None = None,
    channel_target_ref: str | None = None,
    entity_id: int = 0,
) -> Event:
    """Log a consent_logged Event. Returns the created Event."""
    if purpose not in VALID_PURPOSES:
        raise ValueError(f"Invalid purpose: {purpose}. Must be one of {VALID_PURPOSES}")

    event = Event(
        tenant_id=tenant_id,
        entity_type="consent",
        entity_id=entity_id,
        event_type="consent_logged",
        actor=actor,
        purpose=purpose,
        consent_reference=_generate_consent_reference(),
        consent_text_version=consent_text_version,
        channel=channel,
        channel_target_ref=channel_target_ref,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def revoke_consent(
    db: Session,
    tenant_id: str,
    purpose: str,
    actor: str,
    entity_id: int = 0,
) -> Event:
    """Log a consent_revoked Event (append-only). Returns the created Event."""
    if purpose not in VALID_PURPOSES:
        raise ValueError(f"Invalid purpose: {purpose}. Must be one of {VALID_PURPOSES}")

    event = Event(
        tenant_id=tenant_id,
        entity_type="consent",
        entity_id=entity_id,
        event_type="consent_revoked",
        actor=actor,
        purpose=purpose,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def check_extraction_consent(db: Session, tenant_id: str) -> bool:
    """Thin wrapper for the ingest endpoint (#25)."""
    return check_consent(db, tenant_id, "vision_extraction")


def get_active_consent_reference(db: Session, tenant_id: str, purpose: str) -> str | None:
    """Return the consent_reference of the latest active consent for (tenant, purpose).

    Returns None if no consent is logged or it has been revoked.
    """
    if purpose not in VALID_PURPOSES:
        return None

    logged = (
        db.query(Event)
        .filter(
            Event.tenant_id == tenant_id,
            Event.event_type == "consent_logged",
            Event.purpose == purpose,
        )
        .order_by(Event.created_at.desc(), Event.id.desc())
        .first()
    )
    if logged is None:
        return None

    revoked = (
        db.query(Event)
        .filter(
            Event.tenant_id == tenant_id,
            Event.event_type == "consent_revoked",
            Event.purpose == purpose,
        )
        .order_by(Event.created_at.desc(), Event.id.desc())
        .first()
    )
    if revoked is not None and revoked.created_at > logged.created_at:
        return None
    return logged.consent_reference


def get_active_consent_channel(db: Session, tenant_id: str, purpose: str) -> Event | None:
    """Return the latest active consent Event for (tenant, purpose).

    Returns None if no consent is logged or it has been revoked.
    Caller can read consent_reference / channel / channel_target_ref.
    """
    if purpose not in VALID_PURPOSES:
        return None

    logged = (
        db.query(Event)
        .filter(
            Event.tenant_id == tenant_id,
            Event.event_type == "consent_logged",
            Event.purpose == purpose,
        )
        .order_by(Event.created_at.desc(), Event.id.desc())
        .first()
    )
    if logged is None:
        return None

    revoked = (
        db.query(Event)
        .filter(
            Event.tenant_id == tenant_id,
            Event.event_type == "consent_revoked",
            Event.purpose == purpose,
        )
        .order_by(Event.created_at.desc(), Event.id.desc())
        .first()
    )
    if revoked is not None and revoked.created_at > logged.created_at:
        return None
    return logged
