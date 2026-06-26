from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.db.database import get_master_db
from app.deps import get_current_user
from app.models.master import TenantUser
from app.schemas.auth import LoginIn, LoginOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


# Cookie config: secure=False in development (local HTTP), True on staging/prod
_SECURE_COOKIE = settings.ENVIRONMENT != "development"
_MAX_AGE_SECONDS = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_master_db)):
    user = (
        db.query(TenantUser)
        .filter(TenantUser.tenant_id == payload.tenant_id, TenantUser.username == payload.username)
        .first()
    )
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect tenant, username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
        )

    access_token = create_access_token(
        data={"sub": user.username, "tenant_id": user.tenant_id, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    response.set_cookie(
        "khe_session",
        access_token,
        httponly=True,
        secure=_SECURE_COOKIE,
        samesite="strict",
        path="/",
        max_age=_MAX_AGE_SECONDS,
    )

    return {
        "user": {"username": user.username, "role": user.role},
        "tenant_id": user.tenant_id,
    }


@router.get("/me", response_model=UserOut)
def me(user: TenantUser = Depends(get_current_user)):
    return {
        "user_id": user.id,
        "username": user.username,
        "tenant_id": user.tenant_id,
        "role": user.role,
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        "khe_session",
        path="/",
        samesite="strict",
        secure=_SECURE_COOKIE,
    )
    return {"ok": True}
