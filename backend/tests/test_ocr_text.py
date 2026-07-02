"""Tests for GET /documents/{id}/ocr-text endpoint (#444)."""
from unittest.mock import PropertyMock, patch

from app.core.config import Settings
from app.models.tenant import Document


def _make_doc(db, tenant_id, file_name="contract.pdf"):
    doc = Document(
        tenant_id=tenant_id,
        file_name=file_name,
        file_path=f"{tenant_id}/{file_name}",
        status="extracted",
        is_evidence=False,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_ocr_text_returns_file(auth_client, test_tenant, db, tmp_path):
    """GET /documents/{id}/ocr-text returns OCR text when available."""
    doc = _make_doc(db, test_tenant)

    ocr_path = tmp_path / (doc.file_path + ".ocr.txt")
    ocr_path.parent.mkdir(parents=True, exist_ok=True)
    ocr_path.write_text("Điều 1: Nội dung hợp đồng", encoding="utf-8")

    with patch.object(Settings, "STORAGE_DIR", new_callable=PropertyMock, return_value=tmp_path):
        r = auth_client.get(f"/documents/{doc.id}/ocr-text")
    assert r.status_code == 200
    assert "Điều 1" in r.text
    assert r.headers.get("x-khe-ocr-disclaimer") == "Machine-generated OCR, may contain errors"
    assert "text/plain" in r.headers.get("content-type", "")


def test_ocr_text_404_when_missing(auth_client, test_tenant, db, tmp_path):
    """GET /documents/{id}/ocr-text returns 404 when no OCR text exists."""
    doc = _make_doc(db, test_tenant)

    with patch.object(Settings, "STORAGE_DIR", new_callable=PropertyMock, return_value=tmp_path):
        r = auth_client.get(f"/documents/{doc.id}/ocr-text")
    assert r.status_code == 404
    assert "OCR text not available" in r.json()["detail"]


def test_ocr_text_404_wrong_doc(auth_client, test_tenant, db, tmp_path):
    """GET /documents/{id}/ocr-text returns 404 for non-existent doc."""
    with patch.object(Settings, "STORAGE_DIR", new_callable=PropertyMock, return_value=tmp_path):
        r = auth_client.get("/documents/99999/ocr-text")
    assert r.status_code == 404
