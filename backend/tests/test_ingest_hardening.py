"""Ingest hardening — upload size limit + atomic event logging (#56).

Uses conftest's per-test isolated tenant + admin auth_client.
"""
import io
import os
import sys
from unittest.mock import patch

import pytest

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.models.tenant import Document, Event


_PDF_HEADER = b"%PDF-1.4\n"


def _pdf_of_size(total_bytes: int) -> bytes:
    """Synthetic PDF: magic-byte header + filler padded to `total_bytes`."""
    if total_bytes <= len(_PDF_HEADER):
        return _PDF_HEADER[:total_bytes]
    return _PDF_HEADER + b"0" * (total_bytes - len(_PDF_HEADER))


class TestUploadSizeLimit:
    def test_upload_within_cap_succeeds(self, auth_client, test_tenant, monkeypatch):
        """Upload at < MAX_UPLOAD_MB succeeds with 201."""
        monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 1)  # 1 MB cap for the test
        body = _pdf_of_size(64 * 1024)  # 64 KB — comfortably under
        r = auth_client.post(
            "/ingest/upload",
            files={"file": ("small.pdf", io.BytesIO(body), "application/pdf")},
        )
        assert r.status_code == 201, r.text

    def test_upload_over_cap_returns_413(self, auth_client, test_tenant, monkeypatch):
        """Upload above MAX_UPLOAD_MB rejected with 413."""
        monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 1)
        body = _pdf_of_size(2 * 1024 * 1024)  # 2 MB — over the 1 MB cap
        r = auth_client.post(
            "/ingest/upload",
            files={"file": ("big.pdf", io.BytesIO(body), "application/pdf")},
        )
        assert r.status_code == 413
        assert "Maximum 1MB" in r.json()["detail"]

    def test_oversized_upload_leaves_no_orphan(self, auth_client, test_tenant, db, monkeypatch):
        """A 413 must not leave a Document row or a temp file behind."""
        monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 1)
        body = _pdf_of_size(2 * 1024 * 1024)
        r = auth_client.post(
            "/ingest/upload",
            files={"file": ("big.pdf", io.BytesIO(body), "application/pdf")},
        )
        assert r.status_code == 413
        # No row created.
        assert db.query(Document).filter(Document.tenant_id == test_tenant).count() == 0
        # No orphan files in the tenant storage dir.
        tenant_dir = settings.STORAGE_DIR / test_tenant
        if tenant_dir.exists():
            assert list(tenant_dir.iterdir()) == []


class TestAtomicEventLogging:
    def test_successful_upload_writes_document_and_event_atomically(
        self, auth_client, test_tenant, db
    ):
        """A 201 upload yields exactly one Document AND one document_uploaded Event."""
        body = _pdf_of_size(8 * 1024)
        r = auth_client.post(
            "/ingest/upload",
            files={"file": ("atomic.pdf", io.BytesIO(body), "application/pdf")},
        )
        assert r.status_code == 201
        doc_id = r.json()["doc_id"]

        # Document row committed with the final file_path (NOT the temp path).
        doc = db.query(Document).filter(Document.id == doc_id).first()
        assert doc is not None
        assert doc.file_path.endswith(f"{doc_id}_atomic.pdf")
        assert "temp_" not in doc.file_path

        # Audit Event for the same doc_id present.
        ev = (
            db.query(Event)
            .filter(
                Event.entity_type == "document",
                Event.entity_id == doc_id,
                Event.event_type == "document_uploaded",
            )
            .first()
        )
        assert ev is not None
        assert ev.actor == "qcuser"

    def test_event_commit_failure_rolls_back_document(
        self, auth_client, test_tenant, db
    ):
        """If the audit Event write fails, the Document row must also be rolled back."""
        body = _pdf_of_size(8 * 1024)

        # Force the final commit to raise. The function should roll back both
        # the Document insert (still uncommitted until step 5) and the audit row.
        with patch(
            "app.routers.documents.Event",
            side_effect=RuntimeError("simulated audit failure"),
        ):
            r = auth_client.post(
                "/ingest/upload",
                files={"file": ("rollback.pdf", io.BytesIO(body), "application/pdf")},
            )

        assert r.status_code == 500
        # No Document committed — audit integrity preserved.
        assert (
            db.query(Document)
            .filter(Document.tenant_id == test_tenant, Document.file_name == "rollback.pdf")
            .count()
            == 0
        )
