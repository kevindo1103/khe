"""Chat query endpoint (#27).

POST /chat/query — retrieve-only, tenant-scoped, D-08 / D-06 compliant.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db, get_master_db
from app.deps import get_current_user
from app.models.master import TenantUser
from app.models.tenant import ChatQueryLog
from app.schemas.chat import ChatQueryIn, ChatQueryOut, ChatSessionResetIn, ChatStatsOut
from app.services import tenant_journey
from app.services.chat_query import answer_question
from app.services.chat_session import delete_session
from sqlalchemy import func

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=ChatQueryOut)
async def query_chat(
    payload: ChatQueryIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    master_db: Session = Depends(get_master_db),
):
    """Answer a natural-language question using only extracted tenant data."""
    result = await answer_question(
        db,
        user.tenant_id,
        payload.question,
        user_id=user.id,
        session_id=payload.session_id,
    )
    # Journey (#213): first query after activation graduates ACTIVATED → STEADY
    # (gated, so it can only promote from ACTIVATED — never skips the spine).
    tenant_journey.advance_stage(
        master_db, user.tenant_id, "STEADY", require_current_at_least="ACTIVATED"
    )
    return result


@router.post("/sessions/reset")
def reset_chat_session(
    payload: ChatSessionResetIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reset the progressive chat state ("🔄 Hỏi mới") for a device/tab (#201).

    POST + JSON body (not a DELETE query param) so the session_id UUID is not
    logged in nginx access logs (#203 M1).
    """
    deleted = delete_session(db, user.tenant_id, user.id, payload.session_id)
    return {"ok": True, "deleted": deleted}


@router.get("/stats", response_model=ChatStatsOut)
def chat_stats(
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregate tokenomics stats for the authenticated tenant (JWT-scoped)."""
    q = db.query(ChatQueryLog).filter(ChatQueryLog.tenant_id == user.tenant_id)
    total_queries = q.count()
    total_cost = q.with_entities(func.sum(ChatQueryLog.cost_vnd)).scalar() or 0.0
    total_in = q.with_entities(func.sum(ChatQueryLog.input_tokens)).scalar() or 0
    total_out = q.with_entities(func.sum(ChatQueryLog.output_tokens)).scalar() or 0
    total_calls = q.with_entities(func.sum(ChatQueryLog.llm_calls)).scalar() or 0
    avg_tokens = (total_in + total_out) / total_queries if total_queries else 0.0
    return ChatStatsOut(
        total_queries=total_queries,
        total_cost_vnd=round(total_cost, 2),
        total_input_tokens=total_in,
        total_output_tokens=total_out,
        total_llm_calls=total_calls,
        avg_tokens_per_query=round(avg_tokens, 1),
    )
