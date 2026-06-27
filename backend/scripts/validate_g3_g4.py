"""DEC-049 Gate G3 + G4 validation script.

G3 — Reconcile clause gap: compare Điều references in OCR text vs structured
     clauses from LLM. Identify which Điều was missed (if any).

G4 — Embedded-text path benchmark: run pdftotext → Gemini on a digital PDF,
     compare cost/quality vs vision-only.

Usage (on VPS, venv activated + .env sourced):
    # G3: clause reconciliation on scanned doc 22
    python3 scripts/validate_g3_g4.py --gate g3 --doc-id 22 --tenant uat-demo

    # G4: embedded-text benchmark on a digital PDF
    python3 scripts/validate_g3_g4.py --gate g4 --doc-id <digital-pdf-id> --tenant uat-demo

    # G4: auto-find a digital PDF in the tenant
    python3 scripts/validate_g3_g4.py --gate g4 --tenant uat-demo

Env vars:
    GEMINI_API_KEY                  — required
    GOOGLE_APPLICATION_CREDENTIALS  — required for G3 (Document AI OCR)
"""
import argparse
import asyncio
import json
import os
import re
import sys
import time

sys.path.insert(0, ".")

from app.core.config import settings
from app.db.database import get_tenant_session
from app.models.tenant import Document


def _find_dieu(text: str) -> list[str]:
    """Find all unique Điều N references, sorted numerically."""
    matches = re.findall(r"(?:ĐIỀU|Điều|điều)\s+(\d+)", text)
    unique = sorted(set(matches), key=int)
    return [f"Điều {n}" for n in unique]


def _cost_vnd(input_tokens, output_tokens, in_rate=0.30, out_rate=2.50):
    usd = (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000
    return usd * 25_400


async def gate_g3(doc_id: int, tenant_id: str):
    """G3: Reconcile OCR Điều count vs structured clauses from LLM."""
    print("=" * 70)
    print("GATE G3 — Clause Reconciliation")
    print("=" * 70)

    db = get_tenant_session(tenant_id)
    try:
        doc = db.query(Document).filter(
            Document.id == doc_id, Document.tenant_id == tenant_id
        ).first()
        if not doc:
            print(f"ERROR: Document {doc_id} not found in {tenant_id}")
            return
        file_path = settings.STORAGE_DIR / doc.file_path
        file_bytes = file_path.read_bytes()
        mime = "application/pdf" if file_bytes[:4] == b"%PDF" else "image/jpeg"
        print(f"Document: {doc.file_name} ({len(file_bytes):,} bytes)")
    finally:
        db.close()

    # Step 1: OCR via Document AI
    print("\n--- Step 1: Document AI OCR ---")
    ocr_text, page_count = await _docai_ocr(file_bytes)
    ocr_dieu = _find_dieu(ocr_text)
    print(f"Pages: {page_count}")
    print(f"OCR text length: {len(ocr_text):,} chars")
    print(f"Điều in OCR ({len(ocr_dieu)}): {ocr_dieu}")

    # Step 2: Structured extraction from OCR text
    print("\n--- Step 2: Gemini structured extraction from OCR text ---")
    ext = await _llm_extract(ocr_text)
    clause_nums = [c.num for c in ext["clauses_raw"] if c.num]
    llm_dieu = _find_dieu(" ".join(clause_nums))
    print(f"Clauses returned: {ext['clauses_count']}")
    print(f"Clause nums: {clause_nums}")
    print(f"Điều in clauses ({len(llm_dieu)}): {llm_dieu}")

    # Step 3: Reconcile
    print("\n--- Step 3: Reconciliation ---")
    ocr_set = set(ocr_dieu)
    llm_set = set(llm_dieu)

    missing = ocr_set - llm_set
    extra = llm_set - ocr_set
    matched = ocr_set & llm_set

    print(f"Matched:  {len(matched)}/{len(ocr_set)} — {sorted(matched)}")
    if missing:
        print(f"MISSING (in OCR but not in clauses):  {sorted(missing)}")
        print("  → LLM dropped these during structuring. Investigate prompt/schema.")
        for m in sorted(missing):
            dieu_num = re.search(r"\d+", m).group()
            pattern = rf"(?:ĐIỀU|Điều|điều)\s+{dieu_num}\b"
            positions = [(i.start(), ocr_text[max(0,i.start()-20):i.end()+80].strip())
                         for i in re.finditer(pattern, ocr_text)]
            for pos, context in positions:
                print(f"    OCR context (char {pos}): ...{context}...")
    else:
        print("  ✅ No missing Điều — all OCR references found in structured output.")

    if extra:
        print(f"EXTRA (in clauses but not in OCR):  {sorted(extra)}")
        print("  → LLM fabricated clause numbers? Check against document.")
    else:
        print("  ✅ No fabricated clause numbers.")

    # Step 4: Check for sub-articles (Khoản) coverage
    print("\n--- Step 4: Sub-article coverage ---")
    khoan_in_clauses = [c.num for c in ext["clauses_raw"]
                        if c.num and re.match(r"Khoản", c.num)]
    muc_in_clauses = [c.num for c in ext["clauses_raw"]
                      if c.num and re.match(r"Mục", c.num)]
    print(f"Khoản entries: {len(khoan_in_clauses)}")
    print(f"Mục entries: {len(muc_in_clauses)}")

    print(f"\n{'=' * 70}")
    verdict = "PASS" if not missing else "FAIL"
    print(f"G3 VERDICT: {verdict}")
    if missing:
        print(f"  {len(missing)} Điều missing from structured output: {sorted(missing)}")
        print("  Action: investigate prompt or schema limitation.")
    print(f"{'=' * 70}")


async def gate_g4(doc_id: int | None, tenant_id: str):
    """G4: Embedded-text path benchmark for digital PDF."""
    print("=" * 70)
    print("GATE G4 — Embedded-Text Path Benchmark (Digital PDF)")
    print("=" * 70)

    db = get_tenant_session(tenant_id)
    try:
        if doc_id:
            doc = db.query(Document).filter(
                Document.id == doc_id, Document.tenant_id == tenant_id
            ).first()
            if not doc:
                print(f"ERROR: Document {doc_id} not found in {tenant_id}")
                return
        else:
            print("Auto-finding a digital PDF...")
            docs = db.query(Document).filter(
                Document.tenant_id == tenant_id
            ).all()
            doc = None
            for d in docs:
                fp = settings.STORAGE_DIR / d.file_path
                if not fp.exists():
                    continue
                fb = fp.read_bytes()
                if fb[:4] != b"%PDF":
                    continue
                from modules.extraction.scan_detect import is_scanned_pdf
                if not is_scanned_pdf(fb):
                    doc = d
                    print(f"  Found digital PDF: doc {d.id} — {d.file_name}")
                    break
                else:
                    print(f"  doc {d.id} — {d.file_name} → scanned, skipping")
            if not doc:
                print("ERROR: No digital PDF found in tenant. Try --doc-id with a known digital PDF.")
                return

        file_path = settings.STORAGE_DIR / doc.file_path
        file_bytes = file_path.read_bytes()
        print(f"Document: {doc.file_name} (ID {doc.id}, {len(file_bytes):,} bytes)")
    finally:
        db.close()

    from modules.extraction.scan_detect import is_scanned_pdf, extract_embedded_text

    scanned = is_scanned_pdf(file_bytes)
    print(f"Scan detection: {'scanned' if scanned else 'digital'}")
    if scanned:
        print("WARNING: This PDF is detected as scanned. G4 tests the digital path.")
        print("  Running anyway but results represent hybrid OCR path, not embedded-text.")

    # --- Path A: Embedded text (pdftotext → Gemini) ---
    print("\n--- Path A: pdftotext → Gemini Flash (embedded text) ---")
    t0 = time.time()
    embedded_text = extract_embedded_text(file_bytes)
    pdftotext_time = time.time() - t0

    if not embedded_text:
        print("  pdftotext returned no text — cannot benchmark embedded path.")
        print("  This PDF may be scanned or have no text layer.")
        return

    print(f"  pdftotext: {len(embedded_text):,} chars in {pdftotext_time:.2f}s (0đ)")
    dieu_pdftotext = _find_dieu(embedded_text)
    print(f"  Điều found: {len(dieu_pdftotext)} — {dieu_pdftotext}")

    ext_a = await _llm_extract(embedded_text)
    cost_a = _cost_vnd(ext_a["input_tokens"], ext_a["output_tokens"])
    total_latency_a = pdftotext_time + ext_a["latency_s"]
    print(f"  LLM: {ext_a['latency_s']:.1f}s, {ext_a['input_tokens']:,}+{ext_a['output_tokens']:,} tokens")
    print(f"  Total cost: {cost_a:,.0f}đ (OCR 0đ + LLM {cost_a:,.0f}đ)")
    print(f"  Total latency: {total_latency_a:.1f}s")
    print(f"  Clauses: {ext_a['clauses_count']}  Parties: {ext_a['parties_count']}  Obligations: {ext_a['obligations_count']}")

    # --- Path B: Vision-only baseline ---
    print("\n--- Path B: Vision-only baseline (Gemini Flash) ---")
    from modules.extraction.factory import get_extraction_provider
    provider = get_extraction_provider(prefer="gemini_flash")
    t0 = time.time()
    result_b = await provider.extract(file_bytes, "auto")
    latency_b = time.time() - t0
    print(f"  Latency: {latency_b:.1f}s")
    print(f"  Tokens: in={result_b.usage.input_tokens:,}  out={result_b.usage.output_tokens:,}")
    print(f"  Cost: {result_b.cost_vnd:,.0f}đ")
    print(f"  Clauses: {len(result_b.clauses)}  Parties: {len(result_b.parties)}  Obligations: {len(result_b.obligation_schedule)}")

    # --- Comparison ---
    print(f"\n{'=' * 70}")
    print("COMPARISON: Embedded-text vs Vision-only")
    print(f"{'':30s}  {'Embedded':>12s}  {'Vision':>12s}  {'Saving':>12s}")
    print(f"{'Cost (đ)':30s}  {cost_a:12,.0f}  {result_b.cost_vnd:12,.0f}  {result_b.cost_vnd - cost_a:12,.0f}")
    print(f"{'Latency (s)':30s}  {total_latency_a:12.1f}  {latency_b:12.1f}  {latency_b - total_latency_a:12.1f}")
    print(f"{'Clauses':30s}  {ext_a['clauses_count']:12d}  {len(result_b.clauses):12d}")
    print(f"{'Parties':30s}  {ext_a['parties_count']:12d}  {len(result_b.parties):12d}")
    print(f"{'Obligations':30s}  {ext_a['obligations_count']:12d}  {len(result_b.obligation_schedule):12d}")

    cost_saving_pct = ((result_b.cost_vnd - cost_a) / result_b.cost_vnd * 100) if result_b.cost_vnd > 0 else 0
    print(f"\nCost saving: {cost_saving_pct:.0f}%")

    quality_match = (
        ext_a["clauses_count"] >= len(result_b.clauses)
        and ext_a["parties_count"] >= len(result_b.parties)
        and ext_a["obligations_count"] >= len(result_b.obligation_schedule)
    )
    verdict = "PASS" if cost_a < result_b.cost_vnd and quality_match else "REVIEW"
    print(f"\nG4 VERDICT: {verdict}")
    if cost_a < result_b.cost_vnd:
        print(f"  ✅ Embedded-text path is cheaper ({cost_a:,.0f}đ vs {result_b.cost_vnd:,.0f}đ)")
    else:
        print(f"  ⚠️ Embedded-text path is NOT cheaper — investigate")
    if quality_match:
        print(f"  ✅ Quality equal or better")
    else:
        print(f"  ⚠️ Quality lower on some metrics — review extraction details")
    print(f"{'=' * 70}")


async def _docai_ocr(file_bytes: bytes) -> tuple[str, int]:
    """Document AI OCR — sync call."""
    from google.api_core.client_options import ClientOptions
    from google.cloud import documentai

    project = os.environ.get("DOCAI_PROJECT_ID", "")
    location = os.environ.get("DOCAI_LOCATION", "asia-southeast1")
    processor = os.environ.get("DOCAI_PROCESSOR_ID", "")

    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)
    name = client.processor_path(project, location, processor)

    raw_doc = documentai.RawDocument(content=file_bytes, mime_type="application/pdf")
    request = documentai.ProcessRequest(name=name, raw_document=raw_doc)

    t0 = time.time()
    result = client.process_document(request=request)
    elapsed = time.time() - t0

    text = result.document.text
    pages = len(result.document.pages)
    print(f"  DocAI: {elapsed:.1f}s, {pages} pages, {len(text):,} chars")
    return text, pages


async def _llm_extract(text: str) -> dict:
    """Gemini Flash structured extraction from text."""
    from google import genai
    from google.genai import types
    from modules.extraction.schemas import ContractExtractionLLMFull
    from modules.extraction.prompts import SYSTEM_GUARDRAIL, build_text_instruction

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_GUARDRAIL,
        response_mime_type="application/json",
        response_schema=ContractExtractionLLMFull,
        temperature=0.0,
    )
    contents = [
        types.Part.from_text(text=text),
        types.Part.from_text(text=build_text_instruction("auto")),
    ]

    t0 = time.time()
    resp = await client.aio.models.generate_content(
        model="gemini-2.5-flash", contents=contents, config=config
    )
    elapsed = time.time() - t0
    meta = resp.usage_metadata

    parsed = getattr(resp, "parsed", None)
    clauses = list(getattr(parsed, "clauses", [])) if parsed else []
    parties = list(getattr(parsed, "parties", [])) if parsed else []
    obligations = list(getattr(parsed, "obligation_schedule", [])) if parsed else []

    return {
        "input_tokens": meta.prompt_token_count,
        "output_tokens": meta.candidates_token_count,
        "latency_s": elapsed,
        "clauses_count": len(clauses),
        "parties_count": len(parties),
        "obligations_count": len(obligations),
        "clauses_raw": clauses,
        "parsed_ok": parsed is not None,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="DEC-049 Gate G3/G4 validation")
    p.add_argument("--gate", required=True, choices=["g3", "g4"])
    p.add_argument("--doc-id", type=int, default=None)
    p.add_argument("--tenant", default="uat-demo")
    a = p.parse_args()

    if a.gate == "g3":
        if not a.doc_id:
            print("ERROR: --doc-id required for G3")
            sys.exit(1)
        asyncio.run(gate_g3(a.doc_id, a.tenant))
    elif a.gate == "g4":
        asyncio.run(gate_g4(a.doc_id, a.tenant))
