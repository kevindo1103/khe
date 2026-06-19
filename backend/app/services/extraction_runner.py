"""Extraction runner — background worker that turns a saved PDF into Terms.

This is PR-B of issue #25. It runs outside the request scope, so it opens its
own tenant session via `get_tenant_session(tenant_id)` and closes it when done.
"""
import json

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_tenant_session
from app.models.tenant import Document, Event, Term
from app.services.consent import check_extraction_consent
from modules.extraction import CANONICAL_FIELDS, ExtractionUnavailable, get_extraction_provider


async def run_extraction(doc_id: int, tenant_id: str, doc_type: str | None = None) -> None:
    """Run extraction for a persisted Document.

    - Owns its own DB session because it runs in a BackgroundTask.
    - Re-checks consent defensively; if revoked, mark failed and return.
    - Uses `get_extraction_provider()` (factory from #53).
    - Persists Terms for every canonical field returned.
    - Sets Document.doc_type and Document.status = "extracted" or "failed".
    - Logs an extraction Event for NĐ 13/2023 audit.
    """
    db: Session = get_tenant_session(tenant_id)
    try:
        # 1. Defensive consent re-check (NĐ 13).
        if not check_extraction_consent(db, tenant_id):
            _mark_failed(db, doc_id, tenant_id, "Consent revoked since upload")
            return

        # 2. Load document.
        doc = db.query(Document).filter(Document.id == doc_id, Document.tenant_id == tenant_id).first()
        if doc is None:
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
        except ExtractionUnavailable:
            _mark_failed(db, doc_id, tenant_id, "No vision-extraction provider configured")
            return

        # 5. Extract.
        extraction_doc_type = doc_type or doc.doc_type or "auto"
        try:
            result = await provider.extract(file_bytes, extraction_doc_type)
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
        db.query(Term).filter(
            Term.document_id == doc_id,
            Term.tenant_id == tenant_id,
        ).delete()
        db.commit()

        # 8. Persist terms.
        for field_name in CANONICAL_FIELDS:
            field = result.fields.get(field_name)
            if field is None:
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

        # 9. Update document.
        doc.doc_type = result.doc_type.value
        doc.status = "extracted"
        db.commit()

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
                }
            ),
        )
        db.add(event)
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
