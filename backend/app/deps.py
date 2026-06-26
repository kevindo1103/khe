from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db, get_master_db, MasterSessionLocal
from app.models.master import TenantUser


def get_current_user(
    request: Request = None,
    db: Session = Depends(get_master_db),
) -> TenantUser:
    """Read JWT from khe_session HttpOnly cookie (not Authorization header)."""
    token = request.cookies.get("khe_session") if request is not None else None
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    tenant_id: str = payload.get("tenant_id")
    username: str = payload.get("sub")
    if not tenant_id or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = (
        db.query(TenantUser)
        .filter(TenantUser.tenant_id == tenant_id, TenantUser.username == username)
        .first()
    )
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Attach tenant_id to request state for downstream use (D-10 / #12 chain)
    request.state.tenant_id = tenant_id
    return user


def require_manager(user: TenantUser = Depends(get_current_user)) -> TenantUser:
    if user.role not in ("manager", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager access required")
    return user


def require_admin(user: TenantUser = Depends(get_current_user)) -> TenantUser:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
