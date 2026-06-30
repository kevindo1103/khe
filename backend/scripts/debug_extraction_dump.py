"""Debug: dump raw Gemini extraction output for a document (no DB persist).

Usage (run on VPS staging where DocAI + Gemini creds exist):
    cd /opt/khe/backend-staging
    python -m scripts.debug_extraction_dump <tenant_slug> <doc_id>

Confirms NN1 (defined_terms extracted but stub drops them) and NN2 (DocAI
flat text → shallow clause hierarchy). Remove after diagnosis confirmed.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402
from app.db.database import get_tenant_session  # noqa: E402
from app.models.tenant import Document  # noqa: E402


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python -m scripts.debug_extraction_dump <tenant_slug> <doc_id>")
        sys.exit(1)

    tenant_slug = sys.argv[1]
    doc_id = int(sys.argv[2])

    db = get_tenant_session(tenant_slug)
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            print(f"Document {doc_id} not found in tenant {tenant_slug}")
            sys.exit(1)

        file_path = settings.STORAGE_DIR / doc.file_path
        print(f"File: {file_path} (exists={file_path.exists()})")
        file_bytes = file_path.read_bytes()
        doc_type = doc.doc_type or "auto"
        print(f"Size: {len(file_bytes)} bytes, PDF={file_bytes[:4] == b'%PDF'}")
    finally:
        db.close()

    is_pdf = file_bytes[:4] == b"%PDF"
    if is_pdf:
        from modules.extraction.providers.hybrid_ocr import HybridOCRProvider
        provider = HybridOCRProvider()
        print(f"\nProvider: hybrid_ocr (DocAI OCR → Gemini text)")
    else:
        from modules.extraction.providers.gemini_flash import GeminiFlashProvider
        provider = GeminiFlashProvider()
        print(f"\nProvider: gemini_flash (vision)")

    print("Extracting... (this takes 30-60s)")
    result = asyncio.run(provider.extract(file_bytes, doc_type))

    print(f"\n{'='*60}")
    print(f"EXTRACTION RESULT DUMP")
    print(f"{'='*60}")
    print(f"Provider: {result.provider}")
    print(f"Model: {result.model}")
    print(f"is_error: {result.is_error}")
    print(f"Warnings: {result.warnings}")
    print(f"Latency: {result.latency_ms:.0f}ms")
    print(f"Tokens: in={result.usage.input_tokens} out={result.usage.output_tokens}")
    print(f"Cost: {result.cost_vnd:.0f}đ")

    print(f"\n--- CLAUSES ({len(result.clauses)} total) ---")
    for i, c in enumerate(result.clauses):
        level_str = f"L{c.level}" if c.level else "L?"
        path_str = c.clause_path or "no-path"
        num_str = (c.num or "")[:40]
        title_str = (c.title or "")[:40]
        content_preview = (c.content or "")[:80].replace("\n", " ")
        print(f"  [{i:3d}] {level_str} path={path_str:8s} num={num_str:40s} title={title_str}")
        print(f"        content: {content_preview}...")

    level_counts: dict[int | None, int] = {}
    for c in result.clauses:
        level_counts[c.level] = level_counts.get(c.level, 0) + 1
    print(f"\n  Level distribution: {dict(sorted(level_counts.items(), key=lambda x: (x[0] is None, x[0] or 0)))}")

    print(f"\n--- DEFINED_TERMS ({len(result.defined_terms)} total) ---")
    for i, dt in enumerate(result.defined_terms):
        term = (dt.term or "")[:50]
        defn = (dt.definition or "")[:80].replace("\n", " ")
        src = dt.source_clause or ""
        print(f"  [{i:3d}] term={term:50s} source={src}")
        print(f"        definition: {defn}...")

    print(f"\n--- PARTIES ({len(result.parties)} total) ---")
    for p in result.parties:
        print(f"  {p.name} — role={p.role_label}")

    print(f"\n--- SUMMARY ---")
    print(f"  Clauses:       {len(result.clauses)}")
    print(f"  Defined terms: {len(result.defined_terms)}")
    print(f"  Parties:       {len(result.parties)}")
    print(f"  Obligations:   {len(result.obligation_schedule)}")
    print(f"  Cross-refs:    {len(result.cross_references)}")
    print(f"  Doc type:      {result.doc_type} (conf={result.doc_type_confidence})")

    if len(result.clauses) <= 25 and all(c.level in (1, None) for c in result.clauses):
        print(f"\n  ⚠ NN2 CONFIRMED: Only {len(result.clauses)} clauses, all top-level.")
        print(f"    DocAI flat text likely lost indentation → Gemini sees no sub-clauses.")

    if len(result.defined_terms) > 0:
        print(f"\n  ⚠ NN1 CONFIRMED: Gemini extracted {len(result.defined_terms)} defined_terms")
        print(f"    but extraction_runner.py:275 is a no-op stub — never persisted to DB.")


if __name__ == "__main__":
    main()
