"""Ingest router — upload, storage, CRUD, consent-gate-first (#25 PR-A)."""
import json
from pathlib import Path

from fastapi import (
    APIRouter,
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
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.deps import get_current_user
from app.models.master import TenantUser
from app.models.tenant import Document, Event, Term
from app.schemas.documents import (
    BulkUploadOut,
    DocumentDetailOut,
    DocumentListItem,
    DocumentListOut,
    TermOut,
    TermPatchIn,
    UploadOut,
)
from app.services.consent import check_extraction_consent

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _tenant_storage_dir(tenant_id: str) -> Path:
    path = settings.STORAGE_DIR / tenant_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _is_pdf(file: UploadFile) -> bool:
    """Validate PDF magic bytes (%PDF)."""
    header = file.file.read(4)
    file.file.seek(0)
    return header == b"%PDF"


def _safe_filename(name: str) -> str:
    """Sanitise filename for filesystem storage."""
    return "".join(c for c in name if c.isalnum() or c in "._-").rstrip()


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


def _enqueue_extraction_stub(doc_id: int, tenant_id: str) -> None:
    """PR-A stub — extraction worker implemented in PR-B (#25)."""
    pass


# ── Upload ──

@router.post("/upload", response_model=UploadOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    doc_type: str | None = None,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a single PDF. Consent gate FIRST; 403 if SME has not consented."""
    # 1. Consent gate
    if not check_extraction_consent(db, user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SME consent for AI extraction not recorded. Log consent first.",
        )

    # 2. PDF validation
    if not _is_pdf(file):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF files are accepted.",
        )

    # 3. Persist Document row first (to get doc_id)
    doc = Document(
        tenant_id=user.tenant_id,
        file_name=file.filename or "unnamed.pdf",
        file_path="",  # placeholder, updated after saving file
        doc_type=doc_type,
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 4. Save file to per-tenant storage
    tenant_dir = _tenant_storage_dir(user.tenant_id)
    safe_name = _safe_filename(file.filename or "unnamed.pdf")
    disk_name = f"{doc.id}_{safe_name}"
    disk_path = tenant_dir / disk_name

    with open(disk_path, "wb") as out:
        out.write(file.file.read())

    # 5. Update Document with relative file_path
    rel_path = str(Path(user.tenant_id) / disk_name)
    doc.file_path = rel_path
    db.commit()

    # 6. Log upload event
    _log_event(
        db,
        user.tenant_id,
        event_type="document_uploaded",
        entity_type="document",
        entity_id=doc.id,
        actor=user.username,
    )

    # 7. Stub enqueue for PR-B
    _enqueue_extraction_stub(doc.id, user.tenant_id)

    return UploadOut(doc_id=doc.id, file_name=doc.file_name, status=doc.status)


@router.post("/bulk", response_model=BulkUploadOut, status_code=status.HTTP_201_CREATED)
def upload_bulk(
    request: Request,
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

    results: list[UploadOut] = []
    for file in files:
        # Consent gate is checked per-file (re-use single upload logic inline)
        if not check_extraction_consent(db, user.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="SME consent for AI extraction not recorded. Log consent first.",
            )
        if not _is_pdf(file):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Only PDF files are accepted. Rejected: {file.filename}",
            )

        doc = Document(
            tenant_id=user.tenant_id,
            file_name=file.filename or "unnamed.pdf",
            file_path="",
            doc_type=doc_type,
            status="processing",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        tenant_dir = _tenant_storage_dir(user.tenant_id)
        safe_name = _safe_filename(file.filename or "unnamed.pdf")
        disk_name = f"{doc.id}_{safe_name}"
        disk_path = tenant_dir / disk_name

        with open(disk_path, "wb") as out:
            out.write(file.file.read())

        doc.file_path = str(Path(user.tenant_id) / disk_name)
        db.commit()

        _log_event(
            db,
            user.tenant_id,
            event_type="document_uploaded",
            entity_type="document",
            entity_id=doc.id,
            actor=user.username,
        )
        _enqueue_extraction_stub(doc.id, user.tenant_id)

        results.append(UploadOut(doc_id=doc.id, file_name=doc.file_name, status=doc.status))

    return BulkUploadOut(count=len(results), documents=results)


# ── List ──

@router.get("/documents", response_model=DocumentListOut)
def list_documents(
    status_filter: str | None = Query(None, alias="status"),
    needs_review: bool | None = Query(None),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List documents for the tenant with pagination and filters."""
    query = db.query(Document).filter(Document.tenant_id == user.tenant_id)

    if status_filter:
        query = query.filter(Document.status == status_filter)
    if q:
        query = query.filter(Document.file_name.ilike(f"%{q}%"))

    total = query.count()
    docs = (
        query.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items: list[DocumentListItem] = []
    for doc in docs:
        # Rollup: any term needs_review?
        term_count = db.query(Term).filter(Term.document_id == doc.id).count()
        needs_rev = (
            db.query(Term)
            .filter(Term.document_id == doc.id, Term.needs_review == True)
            .first()
            is not None
        )
        items.append(
            DocumentListItem(
                id=doc.id,
                file_name=doc.file_name,
                doc_type=doc.doc_type,
                status=doc.status,
                needs_review=needs_rev,
                term_count=term_count,
                obligation_count=0,  # populated in #26
                created_at=doc.created_at,
            )
        )

    return DocumentListOut(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


# ── Detail ──

@router.get("/documents/{doc_id}", response_model=DocumentDetailOut)
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

    return DocumentDetailOut(
        id=doc.id,
        file_name=doc.file_name,
        doc_type=doc.doc_type,
        status=doc.status,
        created_at=doc.created_at,
        file_url=f"/ingest/documents/{doc.id}/file",
        terms=[TermOut.model_validate(t) for t in terms],
        obligations=[],
    )


# ── File download ──

@router.get("/documents/{doc_id}/file")
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

@router.patch("/documents/{doc_id}/terms/{term_id}")
def patch_term(
    doc_id: int,
    term_id: int,
    payload: TermPatchIn,
    user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a term's field_value, clear needs_review, log Event."""
    # Verify document belongs to tenant
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
