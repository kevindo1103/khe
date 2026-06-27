"""DEC-049 Gate G5 — p90 variance (multi-run stability).

Run HybridOCRProvider N times on the same document to measure variance in
cost, latency, and extraction counts. Budget/SLA should use p90, not mean.

Usage (on VPS, venv activated + env sourced):
    # Default: 5 runs on doc 22
    python3 scripts/validate_g5.py --doc-id 22 --tenant uat-demo

    # Custom runs
    python3 scripts/validate_g5.py --doc-id 22 --tenant uat-demo --runs 10

Env vars:
    GEMINI_API_KEY or GOOGLE_API_KEY          — required
    GOOGLE_APPLICATION_CREDENTIALS            — required for scanned PDFs
    DOCAI_PROJECT_ID, DOCAI_LOCATION, DOCAI_PROCESSOR_ID — Document AI coords
"""
import argparse
import asyncio
import statistics
import sys
import time

sys.path.insert(0, ".")

from app.core.config import settings
from app.db.database import get_tenant_session
from app.models.tenant import Document


def _percentile(data, pct):
    """Simple percentile without numpy."""
    s = sorted(data)
    k = (len(s) - 1) * pct / 100
    f = int(k)
    c = f + 1
    if c >= len(s):
        return s[f]
    return s[f] + (k - f) * (s[c] - s[f])


async def validate_g5(doc_id: int, tenant_id: str, runs: int):
    print("=" * 74)
    print(f"GATE G5 — p90 Variance ({runs} runs on doc {doc_id})")
    print("=" * 74)

    from modules.extraction.scan_detect import is_scanned_pdf

    db = get_tenant_session(tenant_id)
    try:
        doc = db.query(Document).filter(
            Document.id == doc_id, Document.tenant_id == tenant_id
        ).first()
        if not doc:
            print(f"ERROR: Document {doc_id} not found in {tenant_id}")
            return
        fp = settings.STORAGE_DIR / doc.file_path
        file_bytes = fp.read_bytes()
        scanned = is_scanned_pdf(file_bytes) if file_bytes[:4] == b"%PDF" else False
        print(f"Document: {doc.file_name} ({len(file_bytes):,}B)")
        print(f"Type: {'scanned' if scanned else 'digital'} PDF")
    finally:
        db.close()

    from modules.extraction.providers.hybrid_ocr import HybridOCRProvider
    provider = HybridOCRProvider()

    latencies = []
    costs = []
    clause_counts = []
    party_counts = []
    obligation_counts = []
    tokens_in = []
    tokens_out = []
    errors = 0

    print(f"\n{'Run':>4s}  {'Lat(s)':>7s}  {'Cost(d)':>8s}  {'C':>3s}  {'P':>3s}  {'O':>3s}  {'TokIn':>7s}  {'TokOut':>7s}  {'Status':>6s}")
    print("-" * 68)

    for i in range(1, runs + 1):
        t0 = time.time()
        try:
            result = await provider.extract(file_bytes, "auto")
            elapsed = time.time() - t0

            if result.is_error:
                print(f"{i:4d}  {'':>7s}  {'':>8s}  {'':>3s}  {'':>3s}  {'':>3s}  {'':>7s}  {'':>7s}  {'ERROR':>6s}")
                print(f"      {result.warnings[:1]}")
                errors += 1
                continue

            lat = round(elapsed, 1)
            cost = result.cost_vnd
            nc = len(result.clauses)
            np_ = len(result.parties)
            no = len(result.obligation_schedule)
            ti = result.usage.input_tokens
            to_ = result.usage.output_tokens

            latencies.append(lat)
            costs.append(cost)
            clause_counts.append(nc)
            party_counts.append(np_)
            obligation_counts.append(no)
            tokens_in.append(ti)
            tokens_out.append(to_)

            print(f"{i:4d}  {lat:7.1f}  {cost:8,.0f}  {nc:3d}  {np_:3d}  {no:3d}  {ti:7,d}  {to_:7,d}  {'OK':>6s}")

        except Exception as exc:
            elapsed = time.time() - t0
            print(f"{i:4d}  {elapsed:7.1f}  {'':>8s}  {'':>3s}  {'':>3s}  {'':>3s}  {'':>7s}  {'':>7s}  {'FAIL':>6s}")
            print(f"      {type(exc).__name__}: {exc}")
            errors += 1

        if i < runs:
            await asyncio.sleep(1)

    if not latencies:
        print(f"\nAll {runs} runs failed. G5 VERDICT: FAIL")
        return

    n = len(latencies)
    print(f"\n{'=' * 74}")
    print(f"STATISTICS ({n} successful runs, {errors} errors)")
    print(f"{'=' * 74}")

    def _stats_row(label, data, fmt=",.1f"):
        mn = min(data)
        mx = max(data)
        avg = statistics.mean(data)
        med = statistics.median(data)
        p90 = _percentile(data, 90)
        sd = statistics.stdev(data) if len(data) > 1 else 0
        cv = (sd / avg * 100) if avg > 0 else 0
        print(f"  {label:12s}  min={mn:{fmt}}  max={mx:{fmt}}  "
              f"avg={avg:{fmt}}  med={med:{fmt}}  p90={p90:{fmt}}  "
              f"sd={sd:{fmt}}  cv={cv:.0f}%")

    _stats_row("Latency(s)", latencies, ".1f")
    _stats_row("Cost(d)", costs, ",.0f")
    _stats_row("Clauses", [float(x) for x in clause_counts], ".0f")
    _stats_row("Parties", [float(x) for x in party_counts], ".0f")
    _stats_row("Obligations", [float(x) for x in obligation_counts], ".0f")
    _stats_row("Tokens In", [float(x) for x in tokens_in], ",.0f")
    _stats_row("Tokens Out", [float(x) for x in tokens_out], ",.0f")

    # Extraction stability check
    clause_stable = len(set(clause_counts)) == 1
    party_stable = len(set(party_counts)) == 1
    obligation_stable = len(set(obligation_counts)) == 1

    print(f"\nExtraction stability:")
    print(f"  Clauses:     {'STABLE' if clause_stable else 'VARIES'} — {sorted(set(clause_counts))}")
    print(f"  Parties:     {'STABLE' if party_stable else 'VARIES'} — {sorted(set(party_counts))}")
    print(f"  Obligations: {'STABLE' if obligation_stable else 'VARIES'} — {sorted(set(obligation_counts))}")

    # Cost variance
    cost_cv = (statistics.stdev(costs) / statistics.mean(costs) * 100) if len(costs) > 1 and statistics.mean(costs) > 0 else 0
    lat_p90 = _percentile(latencies, 90)
    cost_p90 = _percentile(costs, 90)

    print(f"\nBudgeting numbers (use p90):")
    print(f"  Latency p90:  {lat_p90:.1f}s")
    print(f"  Cost p90:     {cost_p90:,.0f}d")

    # Verdict
    print(f"\n{'=' * 74}")
    error_rate = errors / runs * 100
    pass_criteria = (
        error_rate <= 20
        and cost_cv < 30
    )
    verdict = "PASS" if pass_criteria else "REVIEW"
    print(f"G5 VERDICT: {verdict}")
    print(f"  Runs: {n}/{runs} successful ({error_rate:.0f}% error rate)")
    print(f"  Cost CV: {cost_cv:.0f}% ({'<30% OK' if cost_cv < 30 else '>30% HIGH'})")
    print(f"  Extraction counts: {'stable' if clause_stable and obligation_stable else 'some variance'}")
    if not pass_criteria:
        if error_rate > 20:
            print(f"  ISSUE: error rate {error_rate:.0f}% > 20% threshold")
        if cost_cv >= 30:
            print(f"  ISSUE: cost CV {cost_cv:.0f}% >= 30% — high variance")
    print(f"{'=' * 74}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="DEC-049 Gate G5 — p90 variance")
    p.add_argument("--doc-id", type=int, default=22,
                   help="Document ID to test (default: 22)")
    p.add_argument("--tenant", default="uat-demo")
    p.add_argument("--runs", type=int, default=5,
                   help="Number of runs (default: 5)")
    a = p.parse_args()
    asyncio.run(validate_g5(a.doc_id, a.tenant, a.runs))
