"""HybridOCRProvider — DEC-049 scanned/digital PDF routing.

2-pass pipeline:
  Pass 1 (OCR): Scanned PDF → Document AI OCR; Digital PDF → pdftotext (free).
  Pass 2 (LLM): Feed extracted text → Gemini 2.5 Flash + ContractExtractionLLMFull.

Rationale (benchmark doc 22, 10-page scanned contract):
  Vision-only:  9 clauses, 7 obligations — Gemini does OCR+understanding simultaneously,
                misses articles on dense scanned pages.
  Hybrid DocAI: 14 clauses, 16 obligations — separating OCR from structured extraction
                lets each stage do its job.

Pricing:
  OCR pass:  Document AI ~39đ/page (1,000 pages/month free tier).
  LLM pass:  Gemini Flash $0.30/$2.50 per 1M tokens (text-only, no vision surcharge).
  Digital:   pdftotext = 0đ → LLM-only cost.

Env vars:
  GOOGLE_APPLICATION_CREDENTIALS — path to service account JSON (Document AI auth).
  DOCAI_PROJECT_ID, DOCAI_LOCATION, DOCAI_PROCESSOR_ID — processor coordinates.
  GEMINI_API_KEY or GOOGLE_API_KEY — Gemini Flash LLM pass.
"""

from __future__ import annotations

import asyncio
import io
import os
import time

from ..prompts import SYSTEM_GUARDRAIL, build_text_instruction
from ..scan_detect import extract_embedded_text, is_scanned_pdf
from ..schemas import ContractExtractionLLMFull, ExtractionResult, TokenUsage
from .base import cost_vnd, empty_result, to_result

_DOCAI_SYNC_PAGE_LIMIT = 15


class HybridOCRProvider:
    """DEC-049: Route scanned PDFs through Document AI OCR, digital through pdftotext,
    then feed extracted text to Gemini Flash for structured extraction."""

    name = "hybrid_ocr"
    model = "gemini-2.5-flash"
    in_usd_per_mtok = 0.30
    out_usd_per_mtok = 2.50
    ocr_cost_per_page_vnd = 39.0

    def __init__(
        self,
        gemini_api_key: str | None = None,
        docai_project_id: str | None = None,
        docai_location: str | None = None,
        docai_processor_id: str | None = None,
    ) -> None:
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "google-genai SDK not installed — `pip install google-genai` to use Gemini."
            ) from exc

        self._genai = genai
        self._gemini_client = genai.Client(
            api_key=gemini_api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )
        self._docai_project = docai_project_id or os.environ.get("DOCAI_PROJECT_ID", "")
        self._docai_location = docai_location or os.environ.get("DOCAI_LOCATION", "asia-southeast1")
        self._docai_processor = docai_processor_id or os.environ.get("DOCAI_PROCESSOR_ID", "")

    async def extract(self, image_bytes: bytes, doc_type: str = "auto") -> ExtractionResult:
        started = time.perf_counter()

        is_pdf = image_bytes[:4] == b"%PDF"
        if not is_pdf:
            latency_ms = (time.perf_counter() - started) * 1000
            return empty_result(
                provider=self.name,
                model=self.model,
                latency_ms=latency_ms,
                warning="hybrid_ocr is PDF-only — use gemini_flash for image inputs.",
            )

        scanned = is_scanned_pdf(image_bytes)

        ocr_text: str | None = None
        ocr_cost_vnd = 0.0
        ocr_page_count = 0
        ocr_warnings: list[str] = []

        if not scanned:
            ocr_text = extract_embedded_text(image_bytes)
            if not ocr_text:
                scanned = True

        if scanned:
            try:
                ocr_text, ocr_page_count = await self._document_ai_ocr(image_bytes)
                ocr_cost_vnd = ocr_page_count * self.ocr_cost_per_page_vnd
            except Exception as exc:  # noqa: BLE001
                latency_ms = (time.perf_counter() - started) * 1000
                return empty_result(
                    provider=self.name,
                    model=self.model,
                    latency_ms=latency_ms,
                    warning=f"Document AI OCR failed: {type(exc).__name__}: {exc}",
                )

        if not ocr_text or not ocr_text.strip():
            latency_ms = (time.perf_counter() - started) * 1000
            return empty_result(
                provider=self.name,
                model=self.model,
                latency_ms=latency_ms,
                warning="No text extracted from document (OCR returned empty).",
            )

        if ocr_page_count > _DOCAI_SYNC_PAGE_LIMIT:
            chunks_used = -(-ocr_page_count // _DOCAI_SYNC_PAGE_LIMIT)  # ceil div
            ocr_warnings.append(
                f"Document has {ocr_page_count} pages — processed in {chunks_used} chunks."
            )

        try:
            parsed, usage, llm_latency_ms = await self._llm_extract(ocr_text, doc_type)
        except Exception as exc:  # noqa: BLE001
            latency_ms = (time.perf_counter() - started) * 1000
            return empty_result(
                provider=self.name,
                model=self.model,
                latency_ms=latency_ms,
                warning=f"Gemini text extraction failed: {type(exc).__name__}: {exc}",
            )

        latency_ms = (time.perf_counter() - started) * 1000

        if not isinstance(parsed, ContractExtractionLLMFull):
            return empty_result(
                provider=self.name,
                model=self.model,
                latency_ms=latency_ms,
                warning=f"{self.name} returned no structured output.",
            )

        llm_cost = cost_vnd(usage, self.in_usd_per_mtok, self.out_usd_per_mtok)
        total_cost = round(ocr_cost_vnd + llm_cost, 2)

        extraction_path = "docai_ocr" if scanned else "pdftotext"
        warnings = [
            f"hybrid:{extraction_path} | OCR {ocr_cost_vnd:.0f}đ + LLM {llm_cost:.0f}đ",
            *ocr_warnings,
        ]

        return to_result(
            parsed,
            provider=self.name,
            model=self.model,
            latency_ms=latency_ms,
            usage=usage,
            cost=total_cost,
            warnings=warnings,
        )

    async def _document_ai_ocr(self, file_bytes: bytes) -> tuple[str, int]:
        """Run Document AI OCR, return (text, page_count).

        For PDFs >15 pages (sync API limit), splits into chunks of 15 pages,
        processes each via sync API, and concatenates the OCR text.
        Requires ``pypdf`` for chunking (falls back to single request if unavailable).
        """
        page_count = _pdf_page_count(file_bytes)

        if page_count <= _DOCAI_SYNC_PAGE_LIMIT:
            return await asyncio.to_thread(self._sync_ocr_single, file_bytes)

        chunks = _split_pdf(file_bytes, _DOCAI_SYNC_PAGE_LIMIT)
        results = []
        for chunk_bytes in chunks:
            text, _ = await asyncio.to_thread(self._sync_ocr_single, chunk_bytes)
            results.append(text)

        return "\n".join(results), page_count

    def _sync_ocr_single(self, file_bytes: bytes) -> tuple[str, int]:
        """Process a single PDF (≤15 pages) via Document AI sync API."""
        from google.api_core.client_options import ClientOptions
        from google.cloud import documentai

        location = self._docai_location
        opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
        client = documentai.DocumentProcessorServiceClient(client_options=opts)
        processor_name = client.processor_path(
            self._docai_project, location, self._docai_processor
        )

        raw_doc = documentai.RawDocument(content=file_bytes, mime_type="application/pdf")
        request = documentai.ProcessRequest(name=processor_name, raw_document=raw_doc)
        result = client.process_document(request=request)

        text = result.document.text
        page_count = len(result.document.pages)
        return text, page_count

    async def _llm_extract(  # noqa: C901 (kept together for readability)
        self, text: str, doc_type: str
    ) -> tuple[ContractExtractionLLMFull | None, TokenUsage, float]:
        """Feed OCR text to Gemini Flash for structured extraction."""
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_GUARDRAIL,
            response_mime_type="application/json",
            response_schema=ContractExtractionLLMFull,
            temperature=0.0,
        )
        contents = [
            types.Part.from_text(text=text),
            types.Part.from_text(text=build_text_instruction(doc_type)),
        ]

        started = time.perf_counter()
        response = await self._gemini_client.aio.models.generate_content(
            model=self.model, contents=contents, config=config
        )
        llm_latency_ms = (time.perf_counter() - started) * 1000

        parsed = getattr(response, "parsed", None)
        meta = getattr(response, "usage_metadata", None)
        usage = TokenUsage(
            input_tokens=getattr(meta, "prompt_token_count", 0) or 0,
            output_tokens=getattr(meta, "candidates_token_count", 0) or 0,
        )
        return parsed, usage, llm_latency_ms


def _pdf_page_count(file_bytes: bytes) -> int:
    """Get page count using pypdf (already a dependency for chunking)."""
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader  # type: ignore[no-redef]

    reader = PdfReader(io.BytesIO(file_bytes))
    return len(reader.pages)


def _split_pdf(file_bytes: bytes, chunk_size: int) -> list[bytes]:
    """Split a PDF into chunks of ``chunk_size`` pages each.

    Tries ``pypdf`` first; falls back to ``PyPDF2``."""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        from PyPDF2 import PdfReader, PdfWriter  # type: ignore[no-redef]

    reader = PdfReader(io.BytesIO(file_bytes))
    chunks: list[bytes] = []
    for start in range(0, len(reader.pages), chunk_size):
        writer = PdfWriter()
        for page in reader.pages[start : start + chunk_size]:
            writer.add_page(page)
        buf = io.BytesIO()
        writer.write(buf)
        chunks.append(buf.getvalue())
    return chunks
