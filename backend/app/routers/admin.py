"""Admin / ops endpoints — pilot cost monitoring (#255).

Platform-wide (cross-tenant) reads for PM margin monitoring during pilot. Gated
on the existing tenant role="admin" per the #255 spec.

⚠️ D-10 note: this surfaces aggregate cost/doc-volume across ALL tenants to any
role="admin" tenant user. Acceptable for the 2-firm pilot (PM-operated via curl),
but BEFORE multi-tenant prod this should move behind a dedicated platform
superuser flag, not a per-tenant admin role.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_master_db
from app.deps import get_current_user
from app.models.master import Tenant, TenantUser

router = APIRouter(prefix="/admin", tags=["admin"])

# Phase 1 flat rate per client/month (DEC-011). Hardcoded until billing lands.
REVENUE_VND_MONTH = 100_000


def require_admin(user: TenantUser = Depends(get_current_user)) -> TenantUser:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required.")
    return user


@router.get("/tenants/cost-summary")
def tenants_cost_summary(
    _admin: TenantUser = Depends(require_admin),
    master_db: Session = Depends(get_master_db),
):
    """Per-tenant extraction cost + gross-margin snapshot for pilot monitoring (#255).

    NULL cost columns (pre-migration / un-extracted tenants) sum as 0.
    """
    tenants = master_db.query(Tenant).order_by(Tenant.id).all()
    rows = []
    tot_docs = 0
    tot_month = 0.0
    tot_total = 0.0
    for t in tenants:
        cost_month = t.cost_vnd_month or 0.0
        cost_total = t.cost_vnd_total or 0.0
        docs_month = t.docs_used_month or 0
        gm_pct = (
            round((REVENUE_VND_MONTH - cost_month) / REVENUE_VND_MONTH * 100, 1)
            if REVENUE_VND_MONTH else 0.0
        )
        rows.append({
            "tenant_id": t.id,
            "tenant_name": t.name,
            "docs_month": docs_month,
            "cost_vnd_month": round(cost_month, 2),
            "cost_vnd_total": round(cost_total, 2),
            "revenue_vnd_month": REVENUE_VND_MONTH,
            "gm_pct": gm_pct,
        })
        tot_docs += docs_month
        tot_month += cost_month
        tot_total += cost_total

    return {
        "period": date.today().strftime("%Y-%m"),
        "tenants": rows,
        "totals": {
            "docs_month": tot_docs,
            "cost_vnd_month": round(tot_month, 2),
            "cost_vnd_total": round(tot_total, 2),
        },
    }
