"""Ingest + Document routers — upload, storage, CRUD, consent-gate-first (#25 PR-A).

Frozen contract #1 paths:
  /ingest/upload          (single upload)
  /ingest/bulk            (batch upload)
  /documents              (list)
  /documents/{id}         (detail)
  /documents/{id}/file    (download)
  /documents/{id}/terms/{term_id} (PATCH)
"""
import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db, get_master_db
from app.deps import get_current_user
from app.models.master import Tenant, TenantProfile, TenantUser
from app.models.tenant import Clause, Document, Event, Obligation, Party, Term
from app.schemas.documents import (
    BulkUploadOut,
    ConfirmDocumentOut,
    RemapTypeIn,
    RemapTypeOut,
    DocumentDetailOut,
    DocumentListItem,
    DocumentListOut,
    SelfPartyIn,
    SelfPartyOut,
    TermOut,
    TermPatchIn,
    UploadOut,
)
from app.schemas.obligations import ObligationOut
from app.services.consent import check_extraction_consent
from app.services.extraction_runner import run_extraction
from app.services.obligation_engine import derive_obligations
from app.services import directions, quota, tenant_journey
from modules.extraction import ALL_TYPE_SPECIFIC_FIELDS, ClauseItem, DOC_TYPE_GROUPS, remap_type

# Split routers to match frozen contract #1.
ingest_router = APIRouter(prefix="/ingest", tags=["ingest"])
docs_router = APIRouter(prefix="/documents", tags=["documents"])


def _tenant_storage_dir(tenant_id: str) -> Path:
    path = settings.STORAGE_DIR / tenant_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _is_pdf(file: UploadFile) -> bool:
    """Validate PDF magic bytes (%PDF)."""
    header = file.file.read(4)
    file.file.seek(0)
    return header == b"%PDF"


def _safe_filename(name: str | None) -> str:
    """Sanitise filename for filesystem storage."""
    if not name:
        return "unnamed.pdf"
    cleaned = "".join(c for c in name if c.isalnum() or c in "._-").rstrip()
    return cleaned if cleaned else "unnamed.pdf"


def _log_event(
    db: Session,
    tenant_id: str,
    event_type: str,
    entity_type: str,
    entity_id: int,
    actor: str,
    payload: dict | None = None,
) -> None:
    event = Event(
        tenant_id=tenant_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
        payload=json.dumps(payload) if payload else None,
    )
    db.add(event)
    db.commit()


def _latest_event_payload(
    db: Session, tenant_id: str, doc_id: int, event_type: str
) -> dict | None:
    """Parsed payload of the most recent Event of `event_type` for a document, or None."""
    ev = (
        db.query(Event)
        .filter(
            Event.tenant_id == tenant_id,
            Event.entity_type == "document",
            Event.entity_id == doc_id,
            Event.event_type == event_type,
        )
        .order_by(Event.created_at.desc(), Event.id.desc())
        .first()
    )
    if ev and ev.payload:
        try:
            return json.loads(ev.payload)
        except (ValueError, TypeError):
            return None
    return None


def _enqueue_extraction(
    background_tasks: BackgroundTasks,
    doc_id: int,
    tenant_id: str,
    doc_type: str | None,
) -> None:
    """Schedule the extraction worker in the background."""
    background_tasks.add_task(run_extraction, doc_id, tenant_id, doc_type)


_UPLOAD_CHUNK_BYTES = 64 * 1024


def _stream_to_disk_capped(file: UploadFile, dest: Path, max_bytes: int) -> int:
    """Stream the upload to disk in chunks; reject with 413 if cap exceeded (#56).

    Avoids `file.file.read()` which loads the whole upload into memory. On
    overrun the partial file is deleted before raising so the storage dir stays
    clean. Returns the bytes written.
    """
    written = 0
    try:
        with open(dest, "wb") as out:
            while True:
                chunk = file.file.read(_UPLOAD_CHUNK_BYTES)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    out.close()
                    dest.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large. Maximum {max_bytes // (1024 * 1024)}MB.",
                    )
                out.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file.",
        ) from exc
    return written


def _persist_upload(
    db: Session,
    tenant_id: str,
    username: str,
    file: UploadFile,
    doc_type: str | None,
    background_tasks: BackgroundTasks,
) -> UploadOut:
    """Shared upload logic — atomic Document insert + audit Event (#56).

    Steps:
      1. PDF magic-byte check (422 on miss).
      2. Stream the upload to a temp file with a hard byte cap (413 on overrun)
         instead of loading the whole body into memory.
      3. INSERT the Document and flush() to get its autoincrement id — no commit
         yet, so a later failure rolls back the row.
      4. Rename the temp file to its final ``{id}_{name}`` path.
      5. Update ``doc.file_path`` AND add the ``document_uploaded`` Event in one
         transaction → single commit. If anything in (3–5) fails the row is
         rolled back and the on-disk file is cleaned up; no orphan + no missing
         audit row.
      6. Enqueue the extraction worker as a BackgroundTask.
    """
    # 1. PDF validation
    if not _is_pdf(file):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF files are accepted.",
        )

    # 2. Save file to per-tenant storage first (with a stable temp name)
    tenant_dir = _tenant_storage_dir(tenant_id)
    safe_name = _safe_filename(file.filename)
    temp_id = uuid.uuid4().hex[:12]
    temp_disk_name = f"temp_{temp_id}_{safe_name}"
    temp_disk_path = tenant_dir / temp_disk_name

    _stream_to_disk_capped(file, temp_disk_path, settings.MAX_UPLOAD_MB * 1024 * 1024)

    # 3. INSERT Document + flush() to get the autoincrement id (no commit yet)
    doc = Document(
        tenant_id=tenant_id,
        file_name=file.filename or "unnamed.pdf",
        file_path="",  # placeholder; set after the rename
        doc_type=doc_type,
        status="processing",
    )
    db.add(doc)
    try:
        db.flush()
    except Exception:
        db.rollback()
        temp_disk_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist document metadata.",
        )

    # 4. Rename to final path using the now-known doc.id
    final_disk_name = f"{doc.id}_{safe_name}"
    final_disk_path = tenant_dir / final_disk_name
    try:
        temp_disk_path.rename(final_disk_path)
    except Exception:
        db.rollback()
        temp_disk_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to finalise uploaded file.",
        )

    # 5. Atomic commit: final file_path + audit Event in one transaction.
    try:
        doc.file_path = str(Path(tenant_id) / final_disk_name)
        db.add(
            Event(
                tenant_id=tenant_id,
                event_type="document_uploaded",
                entity_type="document",
                entity_id=doc.id,
                actor=username,
            )
        )
        db.commit()
        db.refresh(doc)
    except Exception:
        db.rollback()
        final_disk_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to commit document.",
        )

    # 6. Enqueue extraction worker (PR-B)
    _enqueue_extraction(background_tasks, doc.id, tenant_id, doc_type)

    return UploadOut(doc_id=doc.id, file_name=doc.file_name, status=doc.status)


# ── Upload (ingest) ──

@ingest_router.post("/upload", response_model=UploadOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: str | None = None,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    master_db: Session = Depends(get_master_db),
):
    """Upload a single PDF. Consent gate FIRST; 403 if SME has not consented."""
    if not check_extraction_consent(db, user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SME consent for AI extraction not recorded. Log consent first.",
        )

    # Quota gate (D-11 / #63): atomic consume BEFORE persist + extraction (no LLM
    # call once over quota). The conditional UPDATE is the TOCTOU-safe gate.
    if not quota.try_consume_quota(master_db, user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Quota exceeded. Contact your firm partner to adjust limit.",
        )

    result = _persist_upload(db, user.tenant_id, user.username, file, doc_type, background_tasks)
    # Journey (#213): first upload moves NEW → EXTRACTING (monotonic no-op after).
    tenant_journey.advance_stage(master_db, user.tenant_id, "EXTRACTING")
    return result


@ingest_router.post("/bulk", response_model=BulkUploadOut, status_code=status.HTTP_201_CREATED)
def upload_bulk(
    request: Request,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    doc_type: str | None = None,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    master_db: Session = Depends(get_master_db),
):
    """Upload up to 20 PDFs in one batch."""
    if len(files) > 20:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Maximum 20 files per bulk upload.",
        )

    # Consent gate is checked once at the batch level.
    if not check_extraction_consent(db, user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SME consent for AI extraction not recorded. Log consent first.",
        )

    # Quota gate per-file (D-11 / #63, PM Q4): a near-limit batch accepts files
    # until the quota is hit, then marks the rest quota_exceeded — never fails the
    # whole batch (DEC-012 concierge onboarding). Slot consumed atomically per file.
    results: list[UploadOut] = []
    accepted = 0
    for file in files:
        if not quota.try_consume_quota(master_db, user.tenant_id):
            results.append(UploadOut(doc_id=None, file_name=file.filename or "", status="quota_exceeded"))
            continue
        results.append(
            _persist_upload(db, user.tenant_id, user.username, file, doc_type, background_tasks)
        )
        accepted += 1

    # Journey (#213): first accepted upload moves NEW → EXTRACTING (no-op after).
    if accepted:
        tenant_journey.advance_stage(master_db, user.tenant_id, "EXTRACTING")

    return BulkUploadOut(count=accepted, documents=results)


# ── List (documents) ──

@docs_router.get("/", response_model=DocumentListOut)
def list_documents(
    status_filter: str | None = Query(None, alias="status"),
    needs_review: bool | None = Query(None),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    master_db: Session = Depends(get_master_db),
):
    """List documents for the tenant with pagination and filters.

    needs_review=True filters to documents with at least one term flagged for review.
    needs_review=False filters to documents with no terms flagged for review.
    """
    # Single-query rollups: term count + any needs_review; obligation count.
    term_subq = (
        db.query(
            Term.document_id.label("doc_id"),
            func.count(Term.id).label("term_count"),
            func.max(Term.needs_review).label("has_needs_review"),
        )
        .group_by(Term.document_id)
        .subquery()
    )

    obligation_subq = (
        db.query(
            Obligation.document_id.label("doc_id"),
            func.count(Obligation.id).label("obligation_count"),
        )
        .group_by(Obligation.document_id)
        .subquery()
    )

    clause_subq = (
        db.query(
            Clause.document_id.label("doc_id"),
            func.count(Clause.id).label("clause_count"),
        )
        .group_by(Clause.document_id)
        .subquery()
    )

    # Direction rollup (#279): active obligations only (status NOT IN done/cancelled).
    # standing obligations (due_date NULL) count in direction tallies but not next_due_date.
    _ACTIVE = Obligation.status.notin_(("done", "cancelled"))
    dir_subq = (
        db.query(
            Obligation.document_id.label("doc_id"),
            func.sum(
                case((Obligation.direction == "nghĩa_vụ", 1), else_=0)
            ).label("nghia_vu_count"),
            func.sum(
                case((Obligation.direction == "quyền_lợi", 1), else_=0)
            ).label("quyen_loi_count"),
            func.sum(
                case((Obligation.direction.is_(None), 1), else_=0)
            ).label("direction_null_count"),
            func.min(
                case((Obligation.due_date.isnot(None), Obligation.due_date))
            ).label("next_due_date"),
        )
        .filter(_ACTIVE)
        .group_by(Obligation.document_id)
        .subquery()
    )

    query = (
        db.query(
            Document,
            term_subq.c.term_count,
            term_subq.c.has_needs_review,
            obligation_subq.c.obligation_count,
            clause_subq.c.clause_count,
            dir_subq.c.nghia_vu_count,
            dir_subq.c.quyen_loi_count,
            dir_subq.c.direction_null_count,
            dir_subq.c.next_due_date,
        )
        .outerjoin(term_subq, term_subq.c.doc_id == Document.id)
        .outerjoin(obligation_subq, obligation_subq.c.doc_id == Document.id)
        .outerjoin(clause_subq, clause_subq.c.doc_id == Document.id)
        .outerjoin(dir_subq, dir_subq.c.doc_id == Document.id)
        .filter(Document.tenant_id == user.tenant_id)
    )

    if status_filter:
        query = query.filter(Document.status == status_filter)
    if q:
        like = f"%{q}%"
        party_match = (
            db.query(Party.id)
            .filter(Party.document_id == Document.id, Party.name.ilike(like))
            .exists()
        )
        query = query.filter(or_(Document.file_name.ilike(like), party_match))
    if needs_review is not None:
        if needs_review:
            query = query.filter(term_subq.c.has_needs_review == True)
        else:
            query = query.filter(
                (term_subq.c.has_needs_review == False) | (term_subq.c.has_needs_review.is_(None))
            )

    total = query.count()
    rows = (
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # primary_party: fetch tenant legal_name once, then one bounded query for all page docs.
    # ≤1 extra query per page — not N+1.
    profile = (
        master_db.query(TenantProfile)
        .filter(TenantProfile.tenant_id == user.tenant_id)
        .first()
    )
    legal_name = (profile.legal_name or "").lower() if profile and profile.legal_name else ""

    page_doc_ids = [row[0].id for row in rows]
    # Fetch all parties for this page in one query, ordered by id ASC (deterministic).
    page_parties = (
        db.query(Party)
        .filter(Party.tenant_id == user.tenant_id, Party.document_id.in_(page_doc_ids))
        .order_by(Party.document_id, Party.id)
        .all()
    ) if page_doc_ids else []

    # Build doc_id → first non-self party name map.
    primary_party_map: dict[int, str | None] = {}
    for p in page_parties:
        if p.document_id in primary_party_map:
            continue
        nm = (p.name or "").lower()
        is_self = bool(legal_name and nm and (legal_name in nm or nm in legal_name))
        if not is_self:
            primary_party_map[p.document_id] = p.name

    items: list[DocumentListItem] = []
    for doc, term_count, has_needs_review, obligation_count, clause_count, nghia_vu, quyen_loi, dir_null, next_due in rows:
        items.append(
            DocumentListItem(
                id=doc.id,
                file_name=doc.file_name,
                doc_type=doc.doc_type,
                status=doc.status,
                needs_review=bool(has_needs_review),
                term_count=term_count or 0,
                obligation_count=obligation_count or 0,
                clause_count=clause_count or 0,
                confirmed_by_user_at=doc.confirmed_by_user_at,
                created_at=doc.created_at,
                primary_party=primary_party_map.get(doc.id),
                next_due_date=next_due,
                nghia_vu_count=nghia_vu or 0,
                quyen_loi_count=quyen_loi or 0,
                direction_null_count=dir_null or 0,
                may_have_unextracted_obligations=None,  # TODO(#276): map doc.may_have_unextracted_obligations once column exists
            )
        )

    return DocumentListOut(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


# ── Detail (documents) ──

@docs_router.get("/{doc_id}", response_model=DocumentDetailOut)
def get_document(
    doc_id: int,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single document with its terms."""
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.tenant_id == user.tenant_id)
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    terms = (
        db.query(Term)
        .filter(Term.document_id == doc_id, Term.tenant_id == user.tenant_id)
        .all()
    )

    obligations = (
        db.query(Obligation)
        .filter(Obligation.document_id == doc_id, Obligation.tenant_id == user.tenant_id)
        .all()
    )

    parties = (
        db.query(Party)
        .filter(Party.document_id == doc_id, Party.tenant_id == user.tenant_id)
        .all()
    )

    clause_count = (
        db.query(Clause)
        .filter(Clause.document_id == doc_id, Clause.tenant_id == user.tenant_id)
        .count()
    )

    # When the doc failed extraction, surface the reason from the latest
    # extraction_failed Event (#79 follow-up — UAT self-diagnosis).
    failure_reason: str | None = None
    if doc.status == "failed":
        fail_payload = _latest_event_payload(db, user.tenant_id, doc.id, "extraction_failed")
        failure_reason = fail_payload.get("reason") if fail_payload else None

    # Last extraction provider/model from the extraction_performed Event (#233) —
    # lets the smoke gate tell gemini_flash (anchors required) from claude fallback.
    extract_payload = _latest_event_payload(db, user.tenant_id, doc.id, "extraction_performed")
    provider = extract_payload.get("provider") if extract_payload else None
    model = extract_payload.get("model") if extract_payload else None

    return DocumentDetailOut(
        id=doc.id,
        file_name=doc.file_name,
        doc_type=doc.doc_type,
        status=doc.status,
        created_at=doc.created_at,
        file_url=f"/documents/{doc.id}/file",
        terms=[TermOut.model_validate(t) for t in terms],
        obligations=[ObligationOut.model_validate(o) for o in obligations],
        clause_count=clause_count,
        parties=[{"name": p.name, "role_label": p.role_label} for p in parties],
        failure_reason=failure_reason,
        provider=provider,
        model=model,
        confirmed_by_user_at=doc.confirmed_by_user_at,
    )


# ── File download (documents) ──

@docs_router.get("/{doc_id}/file")
def download_file(
    doc_id: int,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download the original PDF."""
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.tenant_id == user.tenant_id)
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    file_path = settings.STORAGE_DIR / doc.file_path
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    return FileResponse(
        path=str(file_path),
        filename=doc.file_name,
        media_type="application/pdf",
    )


# ── Patch term (D-07) ──

@docs_router.patch("/{doc_id}/terms/{term_id}")
def patch_term(
    doc_id: int,
    term_id: int,
    payload: TermPatchIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a term's field_value, clear needs_review, log Event."""
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.tenant_id == user.tenant_id)
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    term = (
        db.query(Term)
        .filter(Term.id == term_id, Term.document_id == doc_id, Term.tenant_id == user.tenant_id)
        .first()
    )
    if term is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Term not found")

    old_value = term.field_value
    term.field_value = payload.field_value
    term.needs_review = False
    db.commit()
    db.refresh(term)

    _log_event(
        db,
        user.tenant_id,
        event_type="updated",
        entity_type="term",
        entity_id=term.id,
        actor=user.username,
        payload={"old": old_value, "new": payload.field_value, "doc_id": doc_id},
    )

    return {"ok": True, "term_id": term.id, "field_value": term.field_value}


# ── Self-party confirmation (DEC-030, #155) ──


@docs_router.post("/{doc_id}/confirm_self_party", response_model=SelfPartyOut)
def confirm_self_party(
    doc_id: int,
    body: SelfPartyIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """User selects which role_label is 'me' → re-derive direction for all obligations.

    D-02: this is a user-confirm action — direction is set from human choice, not auto.
    """
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.tenant_id == user.tenant_id)
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    obligations = (
        db.query(Obligation)
        .filter(Obligation.document_id == doc_id, Obligation.tenant_id == user.tenant_id)
        .all()
    )
    updated = 0
    for obl in obligations:
        if obl.obligor:
            new_direction = "nghĩa_vụ" if obl.obligor == body.role_label else "quyền_lợi"
            if obl.direction != new_direction:
                obl.direction = new_direction
                updated += 1
        # obligor is None → direction stays null (D-08)

    db.commit()

    _log_event(
        db,
        user.tenant_id,
        event_type="self_party_confirmed",
        entity_type="document",
        entity_id=doc_id,
        actor=user.username,
        payload={"role_label": body.role_label, "updated": updated},
    )

    return {"ok": True, "updated": updated}


@docs_router.post("/{doc_id}/confirm", response_model=ConfirmDocumentOut)
def confirm_document(
    doc_id: int,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    master_db: Session = Depends(get_master_db),
):
    """User confirms they've reviewed this document (#238, D-02).

    Self-party is auto-derived from the tenant's ``legal_name`` Setting (not a
    manual pick, per PM ratify): direction is recomputed for the doc's
    obligations. The FIRST confirmed doc advances the journey NEEDS_REVIEW →
    CONFIRMED (#250/#249 — all-docs-confirmed was pilot-blocking friction), so
    the FE sidebar nav unlocks.
    """
    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.tenant_id == user.tenant_id)
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Self-party auto-mapping from Settings (DEC-030 / D-13) — no per-doc pick.
    profile = (
        master_db.query(TenantProfile)
        .filter(TenantProfile.tenant_id == user.tenant_id)
        .first()
    )
    legal_name = profile.legal_name if profile else None
    recomputed = directions.rederive_document_directions(db, user.tenant_id, doc_id, legal_name)

    confirmed_at = datetime.utcnow()
    doc.confirmed_by_user_at = confirmed_at
    _log_event(
        db,
        user.tenant_id,
        event_type="document_confirmed_by_user",
        entity_type="document",
        entity_id=doc_id,
        actor=user.username,
        payload={"directions_recomputed": recomputed, "legal_name_set": bool(legal_name)},
    )
    db.commit()

    # Gate (#250/#249): the FIRST confirm advances NEEDS_REVIEW → CONFIRMED. The
    # just-confirmed doc guarantees confirmed_count >= 1; advance is monotonic, so
    # repeat confirms on an already-CONFIRMED tenant are journey no-ops (idempotent).
    journey_advanced = False
    tenant = master_db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    new_stage = tenant.journey_stage if tenant else None
    if tenant is not None:
        before = tenant.journey_stage
        after = tenant_journey.advance_stage(master_db, user.tenant_id, "CONFIRMED")
        new_stage = after or before
        journey_advanced = bool(after and after != before)

    return ConfirmDocumentOut(
        doc_id=doc_id,
        confirmed_at=confirmed_at,
        directions_recomputed=recomputed,
        journey_advanced=journey_advanced,
        new_journey_stage=new_stage,
    )


@docs_router.post("/{doc_id}/remap-type", response_model=RemapTypeOut)
async def remap_document_type(
    doc_id: int,
    body: RemapTypeIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    master_db: Session = Depends(get_master_db),
):
    """Correct a misclassified ``doc_type_group`` by re-mapping the type-specific
    fields from the already-extracted ``clauses[]`` — text-only, no vision call
    (#258). ~2-3đ vs ~177đ re-extract; no quota slot.

    Atomic: delete old type-specific Terms → insert new (source="remap") → update
    the doc_type_group Term → re-derive obligations → reset confirmed_by_user_at
    (back to NEEDS_REVIEW for re-confirm, D-02) → doc_type_corrected Event (D-07).
    """
    target = body.doc_type_group
    if target not in DOC_TYPE_GROUPS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid doc_type_group. Must be one of: {list(DOC_TYPE_GROUPS)}",
        )

    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.tenant_id == user.tenant_id)
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # clauses[] is the text source. Empty → Claude-fallback doc with no clause text:
    # can't remap without re-vision (KHE_AI mirrors this with a no-op guard).
    clause_rows = (
        db.query(Clause)
        .filter(Clause.document_id == doc_id, Clause.tenant_id == user.tenant_id)
        .order_by(Clause.id)
        .all()
    )
    if not clause_rows:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "no_clauses", "message": "Tài liệu chưa có clause text. Cần re-extract để remap."},
        )
    clauses = [ClauseItem(num=c.clause_num, title=c.title, content=c.content or "") for c in clause_rows]

    dtg_term = (
        db.query(Term)
        .filter(Term.document_id == doc_id, Term.tenant_id == user.tenant_id, Term.field_name == "doc_type_group")
        .first()
    )
    old_type = dtg_term.field_value if dtg_term else None

    # KHE_AI text-only remap (D-06/D-08 — null when not in clauses).
    result = await remap_type(clauses, target)

    # ── atomic DB ops ──
    # 1. Clear ALL type-specific Terms (whole union — safer than just the old type's).
    db.query(Term).filter(
        Term.document_id == doc_id,
        Term.tenant_id == user.tenant_id,
        Term.field_name.in_(list(ALL_TYPE_SPECIFIC_FIELDS)),
    ).delete(synchronize_session=False)

    # 2. Insert remapped Terms (a row per target key, D-07 — null-value rows included).
    remapped = 0
    nulls = 0
    for key, f in result.fields.items():
        db.add(Term(
            tenant_id=user.tenant_id, document_id=doc_id, field_name=key,
            field_value=f.value, ref=f.ref, page_num=None,
            confidence=f.confidence, needs_review=f.needs_review, source="remap",
        ))
        if f.value is None:
            nulls += 1
        else:
            remapped += 1

    # 3. Update (or create) the doc_type_group Term.
    if dtg_term is not None:
        dtg_term.field_value = target
    else:
        db.add(Term(tenant_id=user.tenant_id, document_id=doc_id,
                    field_name="doc_type_group", field_value=target, source="remap"))

    # 4. Back to NEEDS_REVIEW — user must re-confirm the new schema (D-02).
    doc.confirmed_by_user_at = None
    # 5. Cost on the doc (#255) — remap spend tracked like extraction.
    doc.extraction_cost_vnd = (doc.extraction_cost_vnd or 0.0) + result.cost_vnd

    # 6. Old obligations may carry the wrong obligation_type → rebuild (PM Q4).
    db.query(Obligation).filter(
        Obligation.document_id == doc_id, Obligation.tenant_id == user.tenant_id
    ).delete(synchronize_session=False)

    # 7. Audit (D-07) — commits the whole transaction above.
    _log_event(
        db, user.tenant_id,
        event_type="doc_type_corrected",
        entity_type="document",
        entity_id=doc_id,
        actor=user.username,
        payload={"from": old_type, "to": target, "provider": result.provider,
                 "remap_cost_vnd": result.cost_vnd,
                 "fields_remapped": remapped, "fields_null": nulls,
                 "warnings": result.warnings},
    )

    # 8. Re-derive date-based obligations from the (now-current) Terms.
    derive_obligations(db, user.tenant_id, doc_id)
    # 9. Tenant cost aggregate (#255) — master.db, only on a real remap spend.
    quota.add_extraction_cost_standalone(user.tenant_id, result.cost_vnd)

    return RemapTypeOut(
        success=True, fields_remapped=remapped, fields_null=nulls, cost_vnd=result.cost_vnd,
    )


# ── Re-extract (admin-only, #97) ──


@docs_router.post("/{doc_id}/re-extract", status_code=status.HTTP_202_ACCEPTED)
def re_extract_document(
    doc_id: int,
    background_tasks: BackgroundTasks,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-trigger extraction on a document — admin only.

    Used to unstick docs whose extraction crashed mid-flight (status='processing'
    after a worker restart) or to pull in a schema upgrade (e.g. #162 added
    `obligation_schedule`). The extraction runner is idempotent: it replaces
    Terms / Clauses / Parties / schedule-derived Obligations for this doc in
    a single transaction.

    CAUTION: chain-resolved Obligations (with non-null source_doc_chain) survive
    re-extraction; if the underlying terms changed materially, run obligation
    derivation afterwards — out of scope here.

    D-02: user-triggered action; audit Event logged.
    """
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    doc = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.tenant_id == user.tenant_id)
        .first()
    )
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if not check_extraction_consent(db, user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SME consent for AI extraction not recorded. Log consent first.",
        )

    previous_status = doc.status
    doc.status = "processing"
    db.commit()

    _log_event(
        db,
        user.tenant_id,
        event_type="extraction_retriggered",
        entity_type="document",
        entity_id=doc_id,
        actor=user.username,
        payload={"previous_status": previous_status},
    )

    _enqueue_extraction(background_tasks, doc_id, user.tenant_id, doc.doc_type)
    return {"ok": True, "doc_id": doc_id, "status": "processing"}
