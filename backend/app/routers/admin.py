"""Admin / ops endpoints — pilot cost monitoring (#255) + extraction metrics (#346).

Platform-wide (cross-tenant) reads for PM margin monitoring during pilot. Gated
on the existing tenant role="admin" per the #255 spec.

⚠️ D-10 note: this surfaces aggregate cost/doc-volume across ALL tenants to any
role="admin" tenant user. Acceptable for the 2-firm pilot (PM-operated via curl),
but BEFORE multi-tenant prod this should move behind a dedicated platform
superuser flag, not a per-tenant admin role.
"""
import json
import os
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_master_db, get_tenant_session
from app.deps import get_current_user
from app.models.master import Tenant, TenantUser
from app.models.tenant import Clause, Document, Obligation, Party, Term

router = APIRouter(prefix="/admin", tags=["admin"])

# Phase 1 flat rate per client/month (DEC-011). Hardcoded until billing lands.
REVENUE_VND_MONTH = 100_000

# Super-admin auth (PM option B, #346): allowlist from env var, no DB migration.
# Set SUPERADMIN_USERS=admin,pm_user in .env / deploy secrets.
_SUPERADMIN_USERS: set[str] = {
    u.strip()
    for u in os.getenv("SUPERADMIN_USERS", "").split(",")
    if u.strip()
}

_LOW_CONFIDENCE_THRESHOLD = 0.7


def require_admin(user: TenantUser = Depends(get_current_user)) -> TenantUser:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required.")
    return user


def require_superadmin(user: TenantUser = Depends(get_current_user)) -> TenantUser:
    """Super-admin guard (PM option B): username must be in SUPERADMIN_USERS env var.

    Falls back to role='admin' when SUPERADMIN_USERS is not set (dev/local convenience).
    In production, always set SUPERADMIN_USERS to prevent any tenant admin from
    accessing cross-tenant data.
    """
    if _SUPERADMIN_USERS and user.username not in _SUPERADMIN_USERS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super-admin access required.",
        )
    if not _SUPERADMIN_USERS and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )
    return user


# ── Existing cost-summary endpoint ──────────────────────────────────────────


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


# ── Extraction metrics (#346) ────────────────────────────────────────────────


class ExtractionMetricOut(BaseModel):
    document_id: int
    tenant_slug: str
    filename: str
    doc_type: str | None = None
    provider: str | None = None
    model: str | None = None
    cost_vnd: float | None = None
    latency_ms: float | None = None
    clause_count: int = 0
    party_count: int = 0
    obligation_count: int = 0
    field_count: int = 0
    low_confidence_count: int = 0
    warnings: list[str] = []
    created_at: str | None = None


class ExtractionMetricsOut(BaseModel):
    items: list[ExtractionMetricOut]
    total: int
    page: int
    page_size: int


class ExtractionMetricsSummaryOut(BaseModel):
    total_docs: int
    avg_cost_vnd: float | None = None
    avg_latency_ms: float | None = None
    total_cost_vnd: float = 0.0
    cost_by_provider: dict[str, float] = {}
    cost_by_tenant: dict[str, float] = {}


def _collect_metrics_for_tenant(
    tenant_id: str,
    tenant_name: str,
    provider_filter: str | None,
    date_from: str | None,
    date_to: str | None,
) -> list[dict[str, Any]]:
    """Open a tenant session and collect extraction metrics for extracted documents.

    Uses get_tenant_session() per CLAUDE.md mandate — never SessionLocal().
    Returns a list of metric dicts, one per extracted document.
    """
    db = get_tenant_session(tenant_id)
    try:
        query = db.query(Document).filter(
            Document.status == "extracted",
            Document.is_evidence == False,
        )
        if provider_filter:
            query = query.filter(Document.extraction_provider == provider_filter)
        if date_from:
            query = query.filter(Document.created_at >= date_from)
        if date_to:
            query = query.filter(Document.created_at <= date_to + "T23:59:59")

        docs = query.order_by(Document.created_at.desc()).all()
        rows = []
        for doc in docs:
            doc_id = doc.id

            clause_count = db.query(func.count(Clause.id)).filter(
                Clause.document_id == doc_id,
                Clause.tenant_id == tenant_id,
            ).scalar() or 0

            party_count = db.query(func.count(Party.id)).filter(
                Party.document_id == doc_id,
                Party.tenant_id == tenant_id,
            ).scalar() or 0

            obligation_count = db.query(func.count(Obligation.id)).filter(
                Obligation.document_id == doc_id,
                Obligation.tenant_id == tenant_id,
            ).scalar() or 0

            field_count = db.query(func.count(Term.id)).filter(
                Term.document_id == doc_id,
                Term.tenant_id == tenant_id,
                Term.field_value.isnot(None),
            ).scalar() or 0

            low_confidence_count = db.query(func.count(Term.id)).filter(
                Term.document_id == doc_id,
                Term.tenant_id == tenant_id,
                Term.confidence.isnot(None),
                Term.confidence < _LOW_CONFIDENCE_THRESHOLD,
            ).scalar() or 0

            warnings: list[str] = []
            if doc.extraction_warnings:
                try:
                    warnings = json.loads(doc.extraction_warnings)
                except (ValueError, TypeError):
                    warnings = []

            rows.append({
                "document_id": doc_id,
                "tenant_slug": tenant_id,
                "filename": doc.file_name,
                "doc_type": doc.doc_type,
                "provider": doc.extraction_provider,
                "model": getattr(doc, "extraction_model", None),
                "cost_vnd": doc.extraction_cost_vnd,
                "latency_ms": getattr(doc, "extraction_latency_ms", None),
                "clause_count": clause_count,
                "party_count": party_count,
                "obligation_count": obligation_count,
                "field_count": field_count,
                "low_confidence_count": low_confidence_count,
                "warnings": warnings,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
            })
        return rows
    finally:
        db.close()


@router.get("/extraction-metrics", response_model=ExtractionMetricsOut)
def extraction_metrics(
    tenant: str | None = Query(None, description="Filter by tenant_id"),
    provider: str | None = Query(None, description="Filter by extraction_provider"),
    date_from: str | None = Query(None, description="ISO date YYYY-MM-DD (inclusive)"),
    date_to: str | None = Query(None, description="ISO date YYYY-MM-DD (inclusive)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _super: TenantUser = Depends(require_superadmin),
    master_db: Session = Depends(get_master_db),
):
    """Cross-tenant extraction quality dashboard (#346).

    Loops over all tenants (or the specified tenant) and collects per-document
    extraction metrics. No PII — filename + counts + cost only.
    Gated on super-admin (SUPERADMIN_USERS env var, PM option B).
    """
    if tenant:
        t = master_db.query(Tenant).filter(Tenant.id == tenant).first()
        tenants = [t] if t else []
    else:
        tenants = master_db.query(Tenant).order_by(Tenant.id).all()

    all_rows: list[dict] = []
    for t in tenants:
        try:
            rows = _collect_metrics_for_tenant(t.id, t.name, provider, date_from, date_to)
            all_rows.extend(rows)
        except Exception:
            # Skip tenants whose DB is unavailable (e.g. not yet provisioned).
            continue

    total = len(all_rows)
    offset = (page - 1) * page_size
    page_rows = all_rows[offset: offset + page_size]

    return ExtractionMetricsOut(
        items=[ExtractionMetricOut(**r) for r in page_rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/extraction-metrics/summary", response_model=ExtractionMetricsSummaryOut)
def extraction_metrics_summary(
    tenant: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    _super: TenantUser = Depends(require_superadmin),
    master_db: Session = Depends(get_master_db),
):
    """Aggregate extraction metrics across all tenants (#346 nice-to-have).

    Returns total_docs, avg cost/latency, cost breakdowns by provider and tenant.
    """
    if tenant:
        t = master_db.query(Tenant).filter(Tenant.id == tenant).first()
        tenants = [t] if t else []
    else:
        tenants = master_db.query(Tenant).order_by(Tenant.id).all()

    all_rows: list[dict] = []
    for t in tenants:
        try:
            rows = _collect_metrics_for_tenant(t.id, t.name, None, date_from, date_to)
            all_rows.extend(rows)
        except Exception:
            continue

    total = len(all_rows)
    costs = [r["cost_vnd"] for r in all_rows if r["cost_vnd"] is not None]
    latencies = [r["latency_ms"] for r in all_rows if r["latency_ms"] is not None]

    cost_by_provider: dict[str, float] = {}
    cost_by_tenant: dict[str, float] = {}
    for r in all_rows:
        if r["cost_vnd"] is not None:
            p = r["provider"] or "unknown"
            cost_by_provider[p] = round(cost_by_provider.get(p, 0.0) + r["cost_vnd"], 2)
            slug = r["tenant_slug"]
            cost_by_tenant[slug] = round(cost_by_tenant.get(slug, 0.0) + r["cost_vnd"], 2)

    return ExtractionMetricsSummaryOut(
        total_docs=total,
        avg_cost_vnd=round(sum(costs) / len(costs), 2) if costs else None,
        avg_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else None,
        total_cost_vnd=round(sum(costs), 2),
        cost_by_provider=cost_by_provider,
        cost_by_tenant=cost_by_tenant,
    )
