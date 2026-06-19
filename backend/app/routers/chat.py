"""Chat query endpoint (#27).

POST /chat/query — retrieve-only, tenant-scoped, D-08 / D-06 compliant.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.deps import get_current_user
from app.models.master import TenantUser
from app.schemas.chat import ChatQueryIn, ChatQueryOut
from app.services.chat_query import answer_question

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=ChatQueryOut)
def query_chat(
    payload: ChatQueryIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Answer a natural-language question using only extracted tenant data."""
    return answer_question(db, user.tenant_id, payload.question)
