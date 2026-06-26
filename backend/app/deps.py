from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db, get_master_db, MasterSessionLocal
from app.models.master import TenantUser

security = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_master_db),
) -> TenantUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    tenant_id: str = payload.get("tenant_id")
    username: str = payload.get("sub")
    if not tenant_id or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
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
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Attach tenant_id to request state for downstream use
    if request is not None:
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
