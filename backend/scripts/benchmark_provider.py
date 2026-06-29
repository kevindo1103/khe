"""Benchmark a specific provider on an existing document.

Usage (on VPS):
    cd /opt/khe/backend-staging
    python scripts/benchmark_provider.py --doc-id 20 --tenant uat-demo --provider claude_haiku
    python scripts/benchmark_provider.py --doc-id 20 --tenant uat-demo --provider gemini_flash

Compares cost/tokens/output between providers on the SAME document.
"""
import argparse
import asyncio
import json
import time

import sys
sys.path.insert(0, ".")

from app.core.config import settings
from app.db.database import get_tenant_session
from app.models.tenant import Document
from modules.extraction.factory import get_extraction_provider


async def benchmark(doc_id: int, tenant_id: str, provider_name: str):
    db = get_tenant_session(tenant_id)
    try:
        doc = db.query(Document).filter(
            Document.id == doc_id, Document.tenant_id == tenant_id
        ).first()
        if not doc:
            print(f"Document {doc_id} not found in tenant {tenant_id}")
            return

        file_path = settings.STORAGE_DIR / doc.file_path
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return

        file_bytes = file_path.read_bytes()
        print(f"Doc: {doc.file_name} ({len(file_bytes):,} bytes)")
        print(f"Provider: {provider_name}")
        print("Extracting...")

        provider = get_extraction_provider(prefer=provider_name)
        t0 = time.time()
        result = await provider.extract(file_bytes, doc.doc_type or "auto")
        elapsed = time.time() - t0

        print(f"\n{'='*60}")
        print(f"Provider: {result.provider} / {result.model}")
        print(f"Latency:  {elapsed:.1f}s")
        print(f"Tokens:   in={result.usage.input_tokens:,}  out={result.usage.output_tokens:,}")
        print(f"Cost:     {result.cost_vnd:,.1f}đ (${result.cost_vnd/25000:.4f})")
        print(f"Doc type: {result.doc_type.value} (conf={result.doc_type_confidence:.0%})")
        print(f"Fields:   {len(result.fields)} extracted")
        print(f"Clauses:  {len(result.clauses)}")
        print(f"Parties:  {len(result.parties)}")
        print(f"Obligations: {len(result.obligation_schedule)}")
        print(f"Warnings: {result.warnings or 'none'}")
        print(f"Error:    {result.is_error}")

        if result.parties:
            print(f"\nParties:")
            for p in result.parties:
                print(f"  - {p.name} ({p.role_label})")

        if result.obligation_schedule:
            print(f"\nObligations:")
            for o in result.obligation_schedule:
                print(f"  - [{o.obligation_type}] {o.description[:80]}")
                if o.due_date:
                    print(f"    due: {o.due_date}")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc-id", type=int, required=True)
    parser.add_argument("--tenant", default="uat-demo")
    parser.add_argument("--provider", default="gemini_flash",
                        choices=["gemini_flash", "claude_haiku", "claude_sonnet"])
    args = parser.parse_args()
    asyncio.run(benchmark(args.doc_id, args.tenant, args.provider))
