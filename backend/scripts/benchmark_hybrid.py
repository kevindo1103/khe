"""Hybrid OCR+LLM extraction benchmark — compare vision-only vs OCR+text.

Tests the hypothesis: Gemini Vision misses clauses on scanned PDFs because it's
doing OCR+understanding simultaneously. Hybrid separates the two:
  Pass 1: OCR (extract raw text from all pages)
  Pass 2: LLM (structured extraction from TEXT, not images)

Usage (on VPS, with venv activated + .env sourced):
    # Phase 1: Gemini as OCR — does it see more in raw-text mode?
    python3 scripts/benchmark_hybrid.py --doc-id 22 --tenant uat-demo --mode gemini-ocr

    # Phase 2: Full hybrid — OCR text → structured extraction
    python3 scripts/benchmark_hybrid.py --doc-id 22 --tenant uat-demo --mode hybrid

    # Phase 3: Vision-only baseline (same as benchmark_provider.py)
    python3 scripts/benchmark_hybrid.py --doc-id 22 --tenant uat-demo --mode vision
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


async def gemini_ocr(file_bytes: bytes, mime: str) -> dict:
    """Pass 1: Ask Gemini to extract ALL text from document — no structured output."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    prompt = (
        "Trích xuất TOÀN BỘ văn bản từ tài liệu này, theo đúng thứ tự trang.\n"
        "Với mỗi trang, ghi rõ [Trang N] ở đầu.\n"
        "GIỮ NGUYÊN tiếng Việt, không dịch, không tóm tắt.\n"
        "Bao gồm MỌI điều khoản, bảng biểu, ghi chú — không bỏ sót."
    )
    t0 = time.time()
    resp = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=file_bytes, mime_type=mime),
            types.Part(text=prompt),
        ],
        config=types.GenerateContentConfig(temperature=0.0),
    )
    elapsed = time.time() - t0
    meta = resp.usage_metadata
    text = resp.text or ""

    dieu_matches = re.findall(r"(?:ĐIỀU|Điều|điều)\s+\d+", text, re.IGNORECASE)
    dieu_unique = sorted(set(dieu_matches), key=lambda x: int(re.search(r"\d+", x).group()))

    return {
        "text": text,
        "input_tokens": meta.prompt_token_count,
        "output_tokens": meta.candidates_token_count,
        "latency_s": elapsed,
        "dieu_found": dieu_unique,
        "dieu_count": len(dieu_unique),
        "text_length": len(text),
    }


async def hybrid_extract(ocr_text: str) -> dict:
    """Pass 2: Feed OCR text to Gemini for structured extraction (text input, no image)."""
    from google import genai
    from google.genai import types
    from modules.extraction.schemas import ContractExtractionLLMFull
    from modules.extraction.prompts import SYSTEM_GUARDRAIL, build_instruction

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    instruction = build_instruction("auto")
    user_prompt = (
        f"Dưới đây là toàn bộ văn bản đã OCR từ tài liệu hợp đồng.\n"
        f"Đọc kỹ và bóc tách thông tin theo schema JSON yêu cầu.\n\n"
        f"--- BẮT ĐẦU VĂN BẢN ---\n{ocr_text}\n--- KẾT THÚC VĂN BẢN ---\n\n"
        f"{instruction}"
    )

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_GUARDRAIL,
        response_mime_type="application/json",
        response_schema=ContractExtractionLLMFull,
        temperature=0.0,
    )

    t0 = time.time()
    resp = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=[types.Part(text=user_prompt)],
        config=config,
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
        "clauses": [(c.num, (c.title or "")[:40]) for c in clauses],
        "parties": [(p.name, p.role_label) for p in parties],
        "obligations": [(o.obligation_type, (o.description or "")[:60], o.due_date) for o in obligations],
        "parsed_ok": parsed is not None,
    }


async def vision_extract(file_bytes: bytes, mime: str) -> dict:
    """Baseline: current vision-only approach (same as production)."""
    from modules.extraction.factory import get_extraction_provider
    from modules.extraction.providers.base import cost_vnd

    provider = get_extraction_provider(prefer="gemini_flash")
    t0 = time.time()
    result = await provider.extract(file_bytes, "auto")
    elapsed = time.time() - t0

    return {
        "input_tokens": result.usage.input_tokens,
        "output_tokens": result.usage.output_tokens,
        "cost_vnd": result.cost_vnd,
        "latency_s": elapsed,
        "clauses_count": len(result.clauses),
        "parties_count": len(result.parties),
        "obligations_count": len(result.obligation_schedule),
        "clauses": [(c.num, (c.title or "")[:40]) for c in result.clauses],
        "parties": [(p.name, p.role_label) for p in result.parties],
        "obligations": [(o.obligation_type, (o.description or "")[:60], o.due_date) for o in result.obligation_schedule],
    }


def _cost_vnd(input_tokens, output_tokens, in_rate=0.30, out_rate=2.50):
    usd = (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000
    return usd * 25_400


async def run(doc_id: int, tenant_id: str, mode: str):
    db = get_tenant_session(tenant_id)
    try:
        doc = db.query(Document).filter(Document.id == doc_id, Document.tenant_id == tenant_id).first()
        if not doc:
            print(f"Document {doc_id} not found"); return
        file_path = settings.STORAGE_DIR / doc.file_path
        file_bytes = file_path.read_bytes()
        mime = "application/pdf" if file_bytes[:4] == b"%PDF" else "image/jpeg"
        print(f"Doc: {doc.file_name} ({len(file_bytes):,} bytes)")
    finally:
        db.close()

    if mode == "gemini-ocr":
        print("\n=== PHASE 1: Gemini OCR (raw text extraction) ===")
        r = await gemini_ocr(file_bytes, mime)
        cost = _cost_vnd(r["input_tokens"], r["output_tokens"])
        print(f"Latency:      {r['latency_s']:.1f}s")
        print(f"Tokens:       in={r['input_tokens']:,}  out={r['output_tokens']:,}")
        print(f"Cost:         {cost:,.0f}đ")
        print(f"Text length:  {r['text_length']:,} chars")
        print(f"Điều found:   {r['dieu_count']} — {r['dieu_found']}")
        print(f"\n--- First 2000 chars ---")
        print(r["text"][:2000])

    elif mode == "hybrid":
        print("\n=== PHASE 1: Gemini OCR ===")
        ocr = await gemini_ocr(file_bytes, mime)
        ocr_cost = _cost_vnd(ocr["input_tokens"], ocr["output_tokens"])
        print(f"OCR: {ocr['latency_s']:.1f}s, {ocr['input_tokens']:,}+{ocr['output_tokens']:,} tokens, {ocr_cost:,.0f}đ")
        print(f"Điều found in OCR: {ocr['dieu_count']} — {ocr['dieu_found']}")

        print(f"\n=== PHASE 2: Structured extraction from OCR text ===")
        ext = await hybrid_extract(ocr["text"])
        ext_cost = _cost_vnd(ext["input_tokens"], ext["output_tokens"])
        total_cost = ocr_cost + ext_cost
        print(f"LLM: {ext['latency_s']:.1f}s, {ext['input_tokens']:,}+{ext['output_tokens']:,} tokens, {ext_cost:,.0f}đ")
        print(f"Parsed OK:    {ext['parsed_ok']}")
        print(f"Clauses:      {ext['clauses_count']}")
        print(f"Parties:      {ext['parties_count']}")
        print(f"Obligations:  {ext['obligations_count']}")

        print(f"\n{'='*60}")
        print(f"TOTAL COST:   {total_cost:,.0f}đ (OCR {ocr_cost:,.0f} + LLM {ext_cost:,.0f})")
        print(f"TOTAL LATENCY: {ocr['latency_s'] + ext['latency_s']:.1f}s")

        print(f"\nClauses:")
        for num, title in ext["clauses"]:
            print(f"  {num}: {title}")
        print(f"\nParties:")
        for name, role in ext["parties"]:
            print(f"  {name} ({role})")
        print(f"\nObligations:")
        for otype, desc, due in ext["obligations"]:
            print(f"  [{otype}] {desc} — due: {due}")

    elif mode == "vision":
        print("\n=== BASELINE: Vision-only (current production) ===")
        r = await vision_extract(file_bytes, mime)
        print(f"Latency:      {r['latency_s']:.1f}s")
        print(f"Tokens:       in={r['input_tokens']:,}  out={r['output_tokens']:,}")
        print(f"Cost:         {r['cost_vnd']:,.0f}đ")
        print(f"Clauses:      {r['clauses_count']}")
        print(f"Parties:      {r['parties_count']}")
        print(f"Obligations:  {r['obligations_count']}")
        print(f"\nClauses:")
        for num, title in r["clauses"]:
            print(f"  {num}: {title}")
        print(f"\nParties:")
        for name, role in r["parties"]:
            print(f"  {name} ({role})")
        print(f"\nObligations:")
        for otype, desc, due in r["obligations"]:
            print(f"  [{otype}] {desc} — due: {due}")

    else:
        print(f"Unknown mode: {mode}. Use: gemini-ocr, hybrid, vision")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--doc-id", type=int, required=True)
    p.add_argument("--tenant", default="uat-demo")
    p.add_argument("--mode", required=True, choices=["gemini-ocr", "hybrid", "vision"])
    a = p.parse_args()
    asyncio.run(run(a.doc_id, a.tenant, a.mode))
