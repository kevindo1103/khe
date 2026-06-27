"""DEC-049 Gate G2 — Multi-doc validation.

Run HybridOCRProvider on multiple documents (scanned + digital) to confirm
extraction quality is not a single-doc fluke. Compare hybrid vs vision-only
on each document.

Usage (on VPS, venv activated + env sourced):
    python3 scripts/validate_g2.py --tenant uat-demo
    python3 scripts/validate_g2.py --tenant uat-demo --doc-ids 19 21 24
    python3 scripts/validate_g2.py --tenant uat-demo --doc-ids 19 21 24 20

Env vars:
    GEMINI_API_KEY or GOOGLE_API_KEY          — required
    GOOGLE_APPLICATION_CREDENTIALS            — required for scanned PDFs
    DOCAI_PROJECT_ID, DOCAI_LOCATION, DOCAI_PROCESSOR_ID — Document AI coords
"""
import argparse
import asyncio
import json
import os
import sys
import time

sys.path.insert(0, ".")

from app.core.config import settings
from app.db.database import get_tenant_session
from app.models.tenant import Document


async def _run_hybrid(file_bytes: bytes):
    """Run HybridOCRProvider on file bytes."""
    from modules.extraction.providers.hybrid_ocr import HybridOCRProvider

    provider = HybridOCRProvider()
    t0 = time.time()
    result = await provider.extract(file_bytes, "auto")
    elapsed = time.time() - t0
    return result, elapsed


async def _run_vision(file_bytes: bytes):
    """Run vision-only GeminiFlashProvider on file bytes."""
    from modules.extraction.providers.gemini_flash import GeminiFlashProvider

    provider = GeminiFlashProvider()
    t0 = time.time()
    result = await provider.extract(file_bytes, "auto")
    elapsed = time.time() - t0
    return result, elapsed


def _summarize(result, elapsed):
    """Extract key metrics from ExtractionResult."""
    return {
        "clauses": len(result.clauses),
        "parties": len(result.parties),
        "obligations": len(result.obligation_schedule),
        "cost_vnd": result.cost_vnd,
        "latency_s": round(elapsed, 1),
        "tokens_in": result.usage.input_tokens,
        "tokens_out": result.usage.output_tokens,
        "doc_type": result.doc_type.value if hasattr(result.doc_type, "value") else str(result.doc_type),
        "is_error": result.is_error,
        "warnings": result.warnings[:2],
    }


async def validate_g2(doc_ids: list[int], tenant_id: str):
    print("=" * 74)
    print("GATE G2 — Multi-Doc Validation (DEC-049)")
    print("=" * 74)

    from modules.extraction.scan_detect import is_scanned_pdf

    db = get_tenant_session(tenant_id)
    try:
        docs_info = []
        for did in doc_ids:
            doc = db.query(Document).filter(
                Document.id == did, Document.tenant_id == tenant_id
            ).first()
            if not doc:
                print(f"  WARN: doc {did} not found in {tenant_id}, skipping")
                continue
            fp = settings.STORAGE_DIR / doc.file_path
            if not fp.exists():
                print(f"  WARN: file missing for doc {did}, skipping")
                continue
            fb = fp.read_bytes()
            is_pdf = fb[:4] == b"%PDF"
            scanned = is_scanned_pdf(fb) if is_pdf else False
            docs_info.append({
                "id": did,
                "name": doc.file_name,
                "bytes": len(fb),
                "is_pdf": is_pdf,
                "scanned": scanned,
                "file_bytes": fb,
            })
            print(f"  doc {did}: {doc.file_name} ({len(fb):,}B) — "
                  f"{'scanned' if scanned else 'digital'} {'PDF' if is_pdf else 'image'}")
    finally:
        db.close()

    if not docs_info:
        print("ERROR: No valid documents found.")
        return

    print(f"\nProcessing {len(docs_info)} documents...\n")

    results = []
    for info in docs_info:
        did = info["id"]
        fb = info["file_bytes"]
        scanned = info["scanned"]

        print(f"--- Doc {did}: {info['name']} ({'scanned' if scanned else 'digital'}) ---")

        # Run hybrid_ocr (the DEC-049 pipeline)
        print(f"  [hybrid_ocr] Running...")
        try:
            h_result, h_elapsed = await _run_hybrid(fb)
            h_summary = _summarize(h_result, h_elapsed)
            print(f"  [hybrid_ocr] {h_summary['latency_s']}s | {h_summary['cost_vnd']:,.0f}d | "
                  f"C={h_summary['clauses']} P={h_summary['parties']} O={h_summary['obligations']}")
            if h_summary["is_error"]:
                print(f"  [hybrid_ocr] ERROR: {h_summary['warnings']}")
        except Exception as exc:
            print(f"  [hybrid_ocr] EXCEPTION: {type(exc).__name__}: {exc}")
            h_summary = {"error": str(exc)}

        # Run vision-only baseline
        print(f"  [vision]     Running...")
        try:
            v_result, v_elapsed = await _run_vision(fb)
            v_summary = _summarize(v_result, v_elapsed)
            print(f"  [vision]     {v_summary['latency_s']}s | {v_summary['cost_vnd']:,.0f}d | "
                  f"C={v_summary['clauses']} P={v_summary['parties']} O={v_summary['obligations']}")
            if v_summary["is_error"]:
                print(f"  [vision]     ERROR: {v_summary['warnings']}")
        except Exception as exc:
            print(f"  [vision]     EXCEPTION: {type(exc).__name__}: {exc}")
            v_summary = {"error": str(exc)}

        results.append({
            "doc_id": did,
            "name": info["name"],
            "scanned": scanned,
            "hybrid": h_summary,
            "vision": v_summary,
        })
        print()

    # Summary table
    print("=" * 74)
    print("SUMMARY")
    print("=" * 74)
    hdr = f"{'Doc':>4s}  {'Type':>8s}  {'Provider':>10s}  {'Cost':>8s}  {'Lat':>6s}  {'C':>3s}  {'P':>3s}  {'O':>3s}  {'Status':>6s}"
    print(hdr)
    print("-" * len(hdr))

    hybrid_wins = 0
    vision_wins = 0
    ties = 0

    for r in results:
        did = r["doc_id"]
        dtype = "scanned" if r["scanned"] else "digital"

        for prov, key in [("hybrid", "hybrid"), ("vision", "vision")]:
            s = r[key]
            if "error" in s:
                print(f"{did:4d}  {dtype:>8s}  {prov:>10s}  {'ERR':>8s}  {'':>6s}  {'':>3s}  {'':>3s}  {'':>3s}  {'FAIL':>6s}")
            else:
                status = "OK" if not s["is_error"] else "FAIL"
                print(f"{did:4d}  {dtype:>8s}  {prov:>10s}  {s['cost_vnd']:8,.0f}  {s['latency_s']:6.1f}  {s['clauses']:3d}  {s['parties']:3d}  {s['obligations']:3d}  {status:>6s}")

        # Compare quality (clauses + obligations as primary metrics)
        h = r["hybrid"]
        v = r["vision"]
        if "error" not in h and "error" not in v:
            h_score = h["clauses"] + h["obligations"]
            v_score = v["clauses"] + v["obligations"]
            if h_score > v_score:
                hybrid_wins += 1
            elif v_score > h_score:
                vision_wins += 1
            else:
                ties += 1

    print(f"\nQuality comparison (clauses + obligations):")
    print(f"  Hybrid wins: {hybrid_wins}  |  Vision wins: {vision_wins}  |  Ties: {ties}")

    # Routing recommendation
    print(f"\n{'=' * 74}")
    print("ROUTING RECOMMENDATION")
    print("=" * 74)
    for r in results:
        did = r["doc_id"]
        h = r["hybrid"]
        v = r["vision"]
        scanned = r["scanned"]
        if "error" in h or "error" in v:
            rec = "INCONCLUSIVE (error)"
        elif scanned:
            h_q = h["clauses"] + h["obligations"]
            v_q = v["clauses"] + v["obligations"]
            if h_q >= v_q:
                rec = "hybrid_ocr (scanned, quality >= vision)"
            else:
                rec = f"REVIEW: vision got more ({v_q} vs {h_q})"
        else:
            if v["cost_vnd"] <= h["cost_vnd"] and v["clauses"] >= h["clauses"]:
                rec = "gemini_flash vision (digital, cheaper or equal quality)"
            else:
                rec = f"REVIEW: hybrid cheaper? h={h['cost_vnd']:.0f}d v={v['cost_vnd']:.0f}d"
        print(f"  doc {did} ({'scanned' if scanned else 'digital'}): {rec}")

    # Verdict
    all_ok = all(
        "error" not in r["hybrid"] and not r["hybrid"].get("is_error", False)
        for r in results
    )
    print(f"\n{'=' * 74}")
    verdict = "PASS" if all_ok and len(results) >= 3 else "FAIL"
    print(f"G2 VERDICT: {verdict}")
    if all_ok:
        print(f"  All {len(results)} documents processed successfully by hybrid_ocr.")
    else:
        failed = [r["doc_id"] for r in results
                  if "error" in r["hybrid"] or r["hybrid"].get("is_error", False)]
        print(f"  Failed docs: {failed}")
    print(f"{'=' * 74}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="DEC-049 Gate G2 — Multi-doc validation")
    p.add_argument("--doc-ids", type=int, nargs="+", default=[19, 21, 24],
                   help="Document IDs to validate (default: 19 21 24)")
    p.add_argument("--tenant", default="uat-demo")
    a = p.parse_args()
    asyncio.run(validate_g2(a.doc_ids, a.tenant))
