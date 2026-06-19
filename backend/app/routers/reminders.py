"""Dev trigger endpoints for the reminder service (#26 PR-B / #62).

Frozen contract #1 path:
  POST /reminders/test
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.deps import get_current_user
from app.models.master import TenantUser
from app.services.reminders import send_reminders_for_tenant

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("/test")
async def test_reminders(
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dev trigger: run the reminder batch for the current tenant right now.

    Returns counts of attempted/sent/skipped reminders.
    """
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev trigger is not allowed in production",
        )

    result = await send_reminders_for_tenant(
        db,
        user.tenant_id,
        settings.TELEGRAM_CHAT_ID,
    )
    return {"ok": True, **result}
