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
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.deps import get_current_user
from app.models.master import TenantUser
from app.models.tenant import Document, Event, Obligation, Term
from app.schemas.documents import (
    BulkUploadOut,
    DocumentDetailOut,
    DocumentListItem,
    DocumentListOut,
    TermOut,
    TermPatchIn,
    UploadOut,
)
from app.schemas.obligations import ObligationOut
from app.services.consent import check_extraction_consent
from app.services.extraction_runner import run_extraction

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


def _enqueue_extraction(
    background_tasks: BackgroundTasks,
    doc_id: int,
    tenant_id: str,
    doc_type: str | None,
) -> None:
    """Schedule the extraction worker in the background."""
    background_tasks.add_task(run_extraction, doc_id, tenant_id, doc_type)


def _persist_upload(
    db: Session,
    tenant_id: str,
    username: str,
    file: UploadFile,
    doc_type: str | None,
    background_tasks: BackgroundTasks,
) -> UploadOut:
    """Shared upload logic: write temp file, then commit DB row atomically.

    Avoids orphan Document rows if file I/O fails by writing the file before
    committing the Document row. If DB commit fails, the temporary file is
    removed.
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

    try:
        with open(temp_disk_path, "wb") as out:
            out.write(file.file.read())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file.",
        ) from e

    # 3. Persist Document row
    rel_path = str(Path(tenant_id) / temp_disk_name)
    doc = Document(
        tenant_id=tenant_id,
        file_name=file.filename or "unnamed.pdf",
        file_path=rel_path,
        doc_type=doc_type,
        status="processing",
    )
    db.add(doc)
    try:
        db.commit()
        db.refresh(doc)
    except Exception:
        # Rollback DB and delete temp file to avoid orphan storage
        db.rollback()
        try:
            temp_disk_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist document metadata.",
        )

    # 4. Rename to final path using doc_id
    final_disk_name = f"{doc.id}_{safe_name}"
    final_disk_path = tenant_dir / final_disk_name
    try:
        temp_disk_path.rename(final_disk_path)
    except Exception:
        # Clean up: delete DB row and temp file
        db.delete(doc)
        db.commit()
        try:
            temp_disk_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to finalise uploaded file.",
        )

    doc.file_path = str(Path(tenant_id) / final_disk_name)
    db.commit()

    # 5. Log upload event
    _log_event(
        db,
        tenant_id,
        event_type="document_uploaded",
        entity_type="document",
        entity_id=doc.id,
        actor=username,
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
):
    """Upload a single PDF. Consent gate FIRST; 403 if SME has not consented."""
    if not check_extraction_consent(db, user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SME consent for AI extraction not recorded. Log consent first.",
        )

    return _persist_upload(db, user.tenant_id, user.username, file, doc_type, background_tasks)


@ingest_router.post("/bulk", response_model=BulkUploadOut, status_code=status.HTTP_201_CREATED)
def upload_bulk(
    request: Request,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    doc_type: str | None = None,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
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

    results: list[UploadOut] = []
    for file in files:
        results.append(
            _persist_upload(db, user.tenant_id, user.username, file, doc_type, background_tasks)
        )

    return BulkUploadOut(count=len(results), documents=results)


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

    query = (
        db.query(
            Document,
            term_subq.c.term_count,
            term_subq.c.has_needs_review,
            obligation_subq.c.obligation_count,
        )
        .outerjoin(term_subq, term_subq.c.doc_id == Document.id)
        .outerjoin(obligation_subq, obligation_subq.c.doc_id == Document.id)
        .filter(Document.tenant_id == user.tenant_id)
    )

    if status_filter:
        query = query.filter(Document.status == status_filter)
    if q:
        query = query.filter(Document.file_name.ilike(f"%{q}%"))
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

    items: list[DocumentListItem] = []
    for doc, term_count, has_needs_review, obligation_count in rows:
        term_count = term_count or 0
        obligation_count = obligation_count or 0
        needs_rev = bool(has_needs_review)
        items.append(
            DocumentListItem(
                id=doc.id,
                file_name=doc.file_name,
                doc_type=doc.doc_type,
                status=doc.status,
                needs_review=needs_rev,
                term_count=term_count,
                obligation_count=obligation_count,
                created_at=doc.created_at,
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

    # When the doc failed extraction, surface the reason from the latest
    # extraction_failed Event (#79 follow-up — UAT self-diagnosis).
    failure_reason: str | None = None
    if doc.status == "failed":
        latest_fail = (
            db.query(Event)
            .filter(
                Event.tenant_id == user.tenant_id,
                Event.entity_type == "document",
                Event.entity_id == doc.id,
                Event.event_type == "extraction_failed",
            )
            .order_by(Event.created_at.desc(), Event.id.desc())
            .first()
        )
        if latest_fail and latest_fail.payload:
            try:
                failure_reason = json.loads(latest_fail.payload).get("reason")
            except (ValueError, TypeError):
                failure_reason = None

    return DocumentDetailOut(
        id=doc.id,
        file_name=doc.file_name,
        doc_type=doc.doc_type,
        status=doc.status,
        created_at=doc.created_at,
        file_url=f"/documents/{doc.id}/file",
        terms=[TermOut.model_validate(t) for t in terms],
        obligations=[ObligationOut.model_validate(o) for o in obligations],
        failure_reason=failure_reason,
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
