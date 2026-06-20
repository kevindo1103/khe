"""Extraction runner — background worker that turns a saved PDF into Terms.

This is PR-B of issue #25. It runs outside the request scope, so it opens its
own tenant session via `get_tenant_session(tenant_id)` and closes it when done.

NOTE: `run_extraction` is intentionally a **sync** function. FastAPI
BackgroundTasks runs sync callables in a threadpool, while the provider's
`extract()` is async. The one async call is bridged with `asyncio.run()`.
"""
import asyncio
import json
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_tenant_session
from app.models.tenant import Clause, Document, Event, Obligation, Term
from app.services.consent import check_extraction_consent, get_active_consent_reference
from app.services.obligation_engine import derive_obligations
from modules.extraction import ExtractionUnavailable, get_extraction_provider

logger = logging.getLogger(__name__)


def run_extraction(doc_id: int, tenant_id: str, doc_type: str | None = None) -> None:
    """Run extraction for a persisted Document.

    - Owns its own DB session because it runs in a BackgroundTask.
    - Re-checks consent defensively; if revoked, mark failed and return.
    - Uses `get_extraction_provider()` (factory from #53).
    - Persists Terms for every canonical field returned.
    - Sets Document.doc_type and Document.status = "extracted" or "failed".
    - Logs an extraction Event for NĐ 13/2023 audit.

    CAUTION: Re-extraction deletes all Terms for this doc and re-inserts them.
    If chain resolution (PR #50) has already run, this may invalidate
    `overrides_term_id` / `is_superseded` invariants across the document chain.
    Full re-resolution belongs in the obligation derivation cycle (#26).
    """
    db: Session = get_tenant_session(tenant_id)
    try:
        # 1. Defensive consent re-check (NĐ 13).
        if not check_extraction_consent(db, tenant_id):
            _mark_failed(db, doc_id, tenant_id, "Consent revoked since upload")
            return

        # 1b. Active consent reference for audit trail.
        consent_reference = get_active_consent_reference(db, tenant_id, "vision_extraction")

        # 2. Load document.
        doc = db.query(Document).filter(Document.id == doc_id, Document.tenant_id == tenant_id).first()
        if doc is None:
            logger.warning("Document %d not found for tenant %s", doc_id, tenant_id)
            return

        # 3. Read file bytes.
        file_path = settings.STORAGE_DIR / doc.file_path
        try:
            file_bytes = file_path.read_bytes()
        except Exception as exc:
            _mark_failed(db, doc_id, tenant_id, f"Failed to read file: {exc}")
            return

        # 4. Get provider.
        try:
            provider = get_extraction_provider()
        except ExtractionUnavailable as exc:
            # Preserve the factory's detail so the Event payload names exactly
            # which env vars were missing — turns #79-style mysteries into a
            # self-explaining audit row. The factory message itself never
            # contains a key value, only the env-var NAMES the caller must set.
            _mark_failed(db, doc_id, tenant_id, f"No vision-extraction provider configured: {exc}")
            return

        # 5. Extract. Provider is async; bridge inside this sync thread.
        extraction_doc_type = doc_type or doc.doc_type or "auto"
        try:
            result = asyncio.run(provider.extract(file_bytes, extraction_doc_type))
        except Exception as exc:
            _mark_failed(db, doc_id, tenant_id, f"Extraction exception: {exc}")
            return

        # 6. Hard extraction failure (D-08: never fabricate).
        if result.is_error:
            _mark_failed(
                db,
                doc_id,
                tenant_id,
                "Extraction provider returned error",
                payload={"warnings": result.warnings},
            )
            return

        # 7. Idempotency: replace existing terms.
        #    Kept in the same transaction as the inserts below; the final
        #    commit below persists all changes atomically.
        db.query(Term).filter(
            Term.document_id == doc_id,
            Term.tenant_id == tenant_id,
        ).delete()

        # 7b. Idempotency: replace existing clauses (DEC-026). Same transaction
        #     as the inserts below, committed atomically with everything else.
        db.query(Clause).filter(
            Clause.document_id == doc_id,
            Clause.tenant_id == tenant_id,
        ).delete()

        # 8. Persist terms — all fields returned by the provider (universal + type-specific).
        for field_name, field in result.fields.items():
            if field is None or field.value is None:
                continue
            term = Term(
                tenant_id=tenant_id,
                document_id=doc_id,
                field_name=field_name,
                field_value=field.value,
                confidence=field.confidence,
                needs_review=field.needs_review,
            )
            db.add(term)

        # 8b. Persist clauses (DEC-026). Gemini returns a full clause list; Claude
        #     fallback returns []. READ-ONLY verbatim text (D-06) — no page_num on
        #     ClauseItem yet, so it stays NULL.
        for clause_item in result.clauses:
            db.add(
                Clause(
                    tenant_id=tenant_id,
                    document_id=doc_id,
                    clause_num=clause_item.num,
                    title=clause_item.title,
                    content=clause_item.content,
                    page_num=None,
                )
            )

        # 9. Update document.
        doc.doc_type = result.doc_type.value
        doc.status = "extracted"

        # 10. Audit event.
        event = Event(
            tenant_id=tenant_id,
            event_type="extraction_performed",
            entity_type="document",
            entity_id=doc_id,
            actor="system",
            purpose="vision_extraction",
            payload=json.dumps(
                {
                    "provider": result.provider,
                    "model": result.model,
                    "cost_vnd": result.cost_vnd,
                    "latency_ms": result.latency_ms,
                    "consent_reference": consent_reference,
                }
            ),
        )
        db.add(event)

        # Single commit: DELETE + INSERTs + UPDATE + audit Event.
        db.commit()

        # Derive obligations from the freshly extracted terms (chain-aware).
        derive_obligations(db, tenant_id, doc_id)

        # 11. Persist payment obligations from payment_schedule (DEC-027 / #117).
        #     Runs AFTER derive_obligations so the chain-aware pending-obligation
        #     cleanup inside derive_obligations doesn't wipe these.
        for ps in result.payment_schedule:
            if not ps.due_date:
                continue
            db.add(Obligation(
                tenant_id=tenant_id,
                document_id=doc_id,
                description=ps.milestone or f"Thanh toán {ps.amount or ''}".strip(),
                obligation_type="once",
                due_date=ps.due_date,
                status="pending",
            ))
        db.commit()
    finally:
        db.close()


def _mark_failed(
    db: Session,
    doc_id: int,
    tenant_id: str,
    reason: str,
    payload: dict | None = None,
) -> None:
    """Mark a document as failed and log an extraction_failed event."""
    doc = db.query(Document).filter(Document.id == doc_id, Document.tenant_id == tenant_id).first()
    if doc:
        doc.status = "failed"
        db.commit()
    else:
        logger.warning("Cannot mark document %d failed: not found for tenant %s", doc_id, tenant_id)

    event = Event(
        tenant_id=tenant_id,
        event_type="extraction_failed",
        entity_type="document",
        entity_id=doc_id,
        actor="system",
        purpose="vision_extraction",
        payload=json.dumps({"reason": reason, **(payload or {})}),
    )
    db.add(event)
    db.commit()
