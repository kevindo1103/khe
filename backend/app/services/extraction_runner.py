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
import unicodedata

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_tenant_session
from app.models.tenant import Clause, Document, Event, Obligation, Party, Term
from app.services.consent import check_extraction_consent, get_active_consent_reference
from app.services.obligation_engine import derive_obligations, resolve_date_anchored_obligations
from app.services import quota, tenant_journey
from app.services.date_parse import parse_date as _parse_date
from modules.extraction import ExtractionUnavailable, get_extraction_provider

logger = logging.getLogger(__name__)


def _normalize_date_iso(raw: str | None) -> str | None:
    """Coerce a date string to ISO yyyy-mm-dd, or return None on parse failure."""
    if not raw:
        return None
    dt = _parse_date(raw)
    if dt is None:
        logger.warning("Unparseable date value %r — storing as None", raw)
        return None
    return dt.strftime("%Y-%m-%d")


def _norm(s: str) -> str:
    """Case-fold + strip diacritics + collapse whitespace for fuzzy comparison."""
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().split())


_VALID_OBLIGATION_TYPES = {"payment", "delivery", "handover", "expiration", "renewal", "review", "warranty", "other"}
_VALID_TRIGGERS = {"date", "event"}


_PROGRESS_CHECKPOINTS = {"ocr": 30, "llm": 60, "saving": 90, "done": 100}


def _update_progress(tenant_id: str, doc_id: int, stage: str, progress: int) -> None:
    """Write extraction progress checkpoint in a separate session.

    Must use a separate session from the main extraction `db` so that
    polling clients see updates before the final commit of the extraction
    transaction (SQLite WAL: separate readers see each mini-commit).

    Failures are swallowed (logged) — progress is UX sugar, not business-critical.
    """
    try:
        session = get_tenant_session(tenant_id)
        try:
            session.query(Document).filter(
                Document.id == doc_id,
                Document.tenant_id == tenant_id,
            ).update({"processing_stage": stage, "processing_progress": progress})
            session.commit()
        finally:
            session.close()
    except Exception:
        logger.warning("Progress update failed for doc %d (stage=%s)", doc_id, stage, exc_info=True)


def _get_tenant_legal_name(tenant_id: str) -> str | None:
    """Read tenant's legal_name from tenant_profiles (master.db)."""
    from app.db.database import MasterSessionLocal
    from app.models.master import TenantProfile
    db = MasterSessionLocal()
    try:
        profile = db.query(TenantProfile).filter(TenantProfile.tenant_id == tenant_id).first()
        return profile.legal_name if profile else None
    finally:
        db.close()


def _derive_direction(tenant_id: str, obligor: str | None, result, *, legal_name: str | None = None) -> str | None:
    """Derive obligation direction from SME's perspective (DEC-030).

    Returns 'nghĩa_vụ' if obligor matches tenant's self-party,
    'quyền_lợi' if obligor is the counterparty, None if can't determine.

    Matching is normalized (case-fold + diacritics-stripped + whitespace-collapsed)
    so Vietnamese diacritic variants and abbreviations in legal_name compare correctly
    against extracted party names (#282 B1 hardening).

    Obligor is matched against BOTH role_label AND party name of self-parties — LLMs
    sometimes emit the full company name as obligor rather than the role label.
    """
    if not obligor:
        return None
    if legal_name is None:
        legal_name = _get_tenant_legal_name(tenant_id)
    if not legal_name:
        return None
    parties = getattr(result, "parties", [])
    norm_ln = _norm(legal_name)
    # Build set of normalized identifiers (role_labels + names) for the self-party.
    self_identifiers: set[str] = set()
    for p in parties:
        norm_nm = _norm(getattr(p, "name", "") or "")
        if norm_nm and (norm_ln in norm_nm or norm_nm in norm_ln):
            role = getattr(p, "role_label", None)
            if role:
                self_identifiers.add(_norm(role))
            self_identifiers.add(norm_nm)
    if not self_identifiers:
        return None
    return "nghĩa_vụ" if _norm(obligor) in self_identifiers else "quyền_lợi"


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

        # 2b. P2 (#302): evidence docs skip full vision extraction — metadata + file
        #     link only. Server-side enforcement (bypass-proof, DEC-048 P2 AC).
        if getattr(doc, "is_evidence", False):
            doc.status = "done"
            db.commit()
            logger.info("Document %d is_evidence=True — skipping extraction", doc_id)
            return

        # 2c. Hoist tenant legal_name once (used by is_self mapping + direction derivation).
        _tenant_legal_name = _get_tenant_legal_name(tenant_id)

        # 3. Read file bytes.
        file_path = settings.STORAGE_DIR / doc.file_path
        try:
            file_bytes = file_path.read_bytes()
        except Exception as exc:
            _mark_failed(db, doc_id, tenant_id, f"Failed to read file: {exc}")
            return

        # 4. DEC-049: route scanned PDFs through hybrid_ocr (DocAI OCR + Gemini text),
        #    digital PDFs/images through gemini_flash (vision-only).
        prefer = "gemini_flash"
        if file_bytes[:4] == b"%PDF":
            from modules.extraction.scan_detect import is_scanned_pdf
            if is_scanned_pdf(file_bytes):
                prefer = "hybrid_ocr"

        try:
            provider = get_extraction_provider(prefer=prefer)
        except ExtractionUnavailable as exc:
            # Preserve the factory's detail so the Event payload names exactly
            # which env vars were missing — turns #79-style mysteries into a
            # self-explaining audit row. The factory message itself never
            # contains a key value, only the env-var NAMES the caller must set.
            _mark_failed(db, doc_id, tenant_id, f"No vision-extraction provider configured: {exc}")
            return

        # 5. Extract. Provider is async; bridge inside this sync thread.
        extraction_doc_type = doc_type or doc.doc_type or "auto"
        _update_progress(tenant_id, doc_id, "ocr", _PROGRESS_CHECKPOINTS["ocr"])
        try:
            result = asyncio.run(provider.extract(file_bytes, extraction_doc_type))
        except Exception as exc:
            _mark_failed(db, doc_id, tenant_id, f"Extraction exception: {exc}")
            return
        _update_progress(tenant_id, doc_id, "llm", _PROGRESS_CHECKPOINTS["llm"])

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

        _update_progress(tenant_id, doc_id, "saving", _PROGRESS_CHECKPOINTS["saving"])

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
        #     Keep NULL-value rows (field.value is None) — the admin review UI edits
        #     existing terms only, so a missing universal field must still have a row
        #     for the user to fill in (D-07 / FR-EX-05).
        for field_name, field in result.fields.items():
            if field is None:
                continue
            # Source anchor (#217): forward-compatible — persisted only when the
            # VisionExtractionProvider supplies it (getattr → None until KHE_AI
            # populates ExtractedField.{ref,page_num,bbox}). bbox stored as JSON.
            _bbox = getattr(field, "bbox", None)
            term = Term(
                tenant_id=tenant_id,
                document_id=doc_id,
                field_name=field_name,
                field_value=field.value,
                confidence=field.confidence,
                needs_review=field.needs_review,
                ref=getattr(field, "ref", None),
                page_num=getattr(field, "page_num", None),
                bbox=json.dumps(_bbox) if _bbox else None,
            )
            db.add(term)

        # 8b. Persist clauses (DEC-026). Gemini returns a full clause list; Claude
        #     fallback returns []. READ-ONLY verbatim text (D-06) — no page_num on
        #     ClauseItem yet, so it stays NULL.
        new_clauses: list[Clause] = []
        for clause_item in result.clauses:
            c = Clause(
                tenant_id=tenant_id,
                document_id=doc_id,
                clause_num=clause_item.num,
                title=clause_item.title,
                content=clause_item.content,
                page_num=None,
            )
            db.add(c)
            new_clauses.append(c)

        # 8b-ii. Build clause hierarchy (#365): flush clause rows to get IDs, then
        #        infer parent/child links from numbering patterns.
        if new_clauses:
            db.flush()
            from app.services.clause_hierarchy import build_clause_hierarchy
            build_clause_hierarchy(new_clauses, db)

        # 8b-iii. R9 (#372): definitions extraction — stub pending KHE_AI schema.
        # When Gemini schema adds definitions[] array, parse (term, definition) pairs
        # here, create Definition rows, link source_clause_id via clause_path matching.
        # No-op for now; CRUD + storage layer is ready.

        # 8b-iv. R10 (#373): cross-reference resolution between clauses.
        from app.services.cross_ref import resolve_cross_refs
        resolve_cross_refs(db, tenant_id, doc.id)

        # 8c. Persist parties (DEC-030, #155). Idempotent: delete existing
        #     per-doc Party rows first, then re-insert from result.parties[].
        db.query(Party).filter(
            Party.document_id == doc_id,
            Party.tenant_id == tenant_id,
        ).delete()
        for party_item in result.parties:
            _aliases_raw = getattr(party_item, "aliases", None)
            db.add(Party(
                tenant_id=tenant_id,
                document_id=doc_id,
                name=party_item.name,
                role_label=party_item.role_label,
                address=getattr(party_item, "address", None),
                contact=getattr(party_item, "contact", None),
                representative=getattr(party_item, "representative", None),
                tax_code=getattr(party_item, "tax_code", None),
                aliases=json.dumps(_aliases_raw) if _aliases_raw is not None else None,
            ))

        # R2 (#364): auto-map is_self from tenant_profile.legal_name (D-13 spirit).
        # Flush so the new Party rows get IDs, then update in the same transaction.
        legal_name = _tenant_legal_name
        if legal_name:
            ln = _norm(legal_name)
            db.flush()
            for party_row in db.query(Party).filter(
                Party.document_id == doc_id,
                Party.tenant_id == tenant_id,
            ).all():
                pn = _norm(party_row.name or "")
                if ln and pn and (ln in pn or pn in ln):
                    party_row.is_self = True

        # 9. Update document.
        doc.doc_type = result.doc_type.value
        doc.status = "extracted"
        # R1 (#363): denormalise title + contract_number from extracted Terms so
        # list/detail endpoints don't need a subquery per doc to display the heading.
        # Cascade: tieu_de_hd → so_hop_dong → None (FE falls back to file_name).
        _title_field = result.fields.get("tieu_de_hd")
        _number_field = result.fields.get("so_hop_dong")
        doc.title = (_title_field.value if _title_field and _title_field.value else None)
        if doc.title is None and _number_field and _number_field.value:
            doc.title = _number_field.value
        doc.contract_number = (_number_field.value if _number_field and _number_field.value else None)
        # R6 (#369): denormalise signing_date + commencement_date for direct column access.
        # _normalize_date_iso coerces LLM output (VN "15/03/2025", verbose, etc.) to ISO yyyy-mm-dd.
        _signing_field = result.fields.get("ngay_ky")
        _commence_field = result.fields.get("ngay_khai_truong")
        doc.signing_date = _normalize_date_iso(
            _signing_field.value if _signing_field and _signing_field.value else None
        )
        doc.commencement_date = _normalize_date_iso(
            _commence_field.value if _commence_field and _commence_field.value else None
        )
        # R8 (#371): contract_term + lifecycle_status derivation.
        _thoi_han = result.fields.get("thoi_han_hd")
        doc.contract_term = (_thoi_han.value if _thoi_han and _thoi_han.value else None)
        _het_han = result.fields.get("ngay_het_han")
        _het_han_val = (_het_han.value if _het_han and _het_han.value else None)
        from app.services.lifecycle import derive_lifecycle_status
        doc.lifecycle_status = derive_lifecycle_status(
            _het_han_val, doc.contract_term, doc.lifecycle_status,
        )
        # R5 (#368): signature detection persistence.
        doc.has_signature = result.has_signature
        doc.signature_pages = json.dumps(result.signature_pages) if result.signature_pages else None
        # Cost tracking (#255): persist provider + token usage + cost on the doc
        # (denormalised for the pilot cost report) in the same transaction.
        doc.extraction_provider = result.provider or None
        doc.extraction_tokens_in = result.usage.input_tokens
        doc.extraction_tokens_out = result.usage.output_tokens
        doc.extraction_cost_vnd = result.cost_vnd
        # Extraction metrics (#346): model, latency, warnings — forward-only.
        doc.extraction_model = result.model or None
        doc.extraction_latency_ms = result.latency_ms or None
        doc.extraction_warnings = json.dumps(result.warnings) if result.warnings else None
        # Extraction progress (#360): final state committed atomically with extraction.
        doc.processing_stage = "done"
        doc.processing_progress = _PROGRESS_CHECKPOINTS["done"]

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

        # Cost aggregate (#255): add this extraction's cost to the tenant's month +
        # lifetime totals on master.db. Done here (cost is known) — NOT in the
        # upload-time quota guard. Only successful extractions are billed.
        quota.add_extraction_cost_standalone(tenant_id, result.cost_vnd)

        # Journey (#213): extraction complete. Any flagged or sub-80%-confidence
        # field routes the tenant to NEEDS_REVIEW (human confirm, D-02); otherwise
        # CONFIRMED. Monotonic forward-only — a later doc never drags a tenant back.
        needs_review = any(
            f is not None and (f.needs_review or (f.confidence is not None and f.confidence < 0.80))
            for f in result.fields.values()
        )
        tenant_journey.advance_stage_standalone(
            tenant_id, "NEEDS_REVIEW" if needs_review else "CONFIRMED"
        )

        # Derive obligations from the freshly extracted terms (chain-aware).
        derive_obligations(db, tenant_id, doc_id)

        # 11. Persist obligations from obligation_schedule (DEC-030 Phase 2, #153 Part 2).
        #     Replaces the old payment_schedule block. Maps all 12 ObligationScheduleItem
        #     fields → Obligation columns. Event-triggered items (trigger="event") get
        #     status=waiting_trigger and due_date=None (D-08: no fabricated date).
        #     Runs AFTER derive_obligations so its chain-aware pending-obligation
        #     cleanup doesn't wipe these. Clear our own schedule-derived rows
        #     explicitly to stay idempotent on re-extraction. Schedule rows are
        #     identifiable by a NULL source_doc_chain (derived obligations always
        #     set it).
        db.query(Obligation).filter(
            Obligation.tenant_id == tenant_id,
            Obligation.document_id == doc_id,
            Obligation.status.in_(["pending", "waiting_trigger"]),
            Obligation.source_doc_chain.is_(None),
        ).delete(synchronize_session=False)
        created_items = []
        for item in result.obligation_schedule:
            # Coerce unknown LLM enum values to safe defaults (#163, D-08 spirit).
            obl_type = item.obligation_type if item.obligation_type in _VALID_OBLIGATION_TYPES else "other"
            trigger = item.trigger if item.trigger in _VALID_TRIGGERS else "date"
            # trigger=event rows have no fixed date until the event fires (D-08).
            due_date = None if trigger == "event" else item.due_date
            # B3 (#282): date-anchored obligations with no resolved due_date are
            # persisted as waiting_trigger so resolve_date_anchored_obligations()
            # can fill them in after extraction. D-08: no fabrication here.
            if trigger == "event" or not due_date:
                status = "waiting_trigger"
            else:
                status = "pending"
            # Dedup guard: skip if a done/cancelled row with same identity tuple
            # already exists (re-extraction after user marked obligation done).
            existing = db.query(Obligation).filter(
                Obligation.tenant_id == tenant_id,
                Obligation.document_id == doc_id,
                Obligation.description == item.description,
                Obligation.obligation_type == obl_type,
                Obligation.due_date == due_date,
                Obligation.status.in_(["done", "cancelled"]),
                Obligation.source_doc_chain.is_(None),
            ).first()
            if existing:
                continue
            direction = _derive_direction(tenant_id, item.obligor, result, legal_name=_tenant_legal_name) if item.obligor else None
            db.add(Obligation(
                tenant_id=tenant_id,
                document_id=doc_id,
                description=item.description,
                obligation_type=obl_type,
                recurrence=item.recurrence or "once",
                obligor=item.obligor,
                direction=direction,
                due_date=due_date,
                status=status,
                milestone_series_id=item.series_id,
                milestone_index=item.milestone_index,
                milestone_total=item.milestone_total,
                milestone_trigger=trigger,
                trigger_condition=item.trigger_condition,
                trigger_delay_days=item.trigger_delay_days,
                amount_raw=item.amount_raw,
                source_clause_num=item.source_clause_num,
                derived_from=item.derived_from,
            ))
            created_items.append({"description": item.description, "obligation_type": obl_type, "due_date": due_date, "trigger": trigger})
        if created_items:
            event = Event(
                tenant_id=tenant_id,
                event_type="obligation_schedule_derived",
                entity_type="document",
                entity_id=doc_id,
                actor="system",
                payload=json.dumps({
                    "count": len(created_items),
                    "items": created_items,
                }),
            )
            db.add(event)
        db.commit()

        # B3 (#282): resolve date-anchored obligations that were persisted as
        # waiting_trigger because their anchor date wasn't known at schedule time.
        resolve_date_anchored_obligations(db, tenant_id, doc_id)
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
        doc.processing_stage = "failed"
        doc.processing_progress = 0
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
