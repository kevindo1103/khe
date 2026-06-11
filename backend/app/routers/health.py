from fastapi import APIRouter

from app.schemas.health import HealthOut

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthOut)
def health_check():
    return {"status": "healthy"}
