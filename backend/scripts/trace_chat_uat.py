#!/usr/bin/env python3
"""Diagnostic trace for a tenant's recent chat behaviour (#268).

Backend can't run SQL on the staging VPS from CI, so this dumps the exact trace
QC asked for — run on the VPS where the tenant DBs live:

    python scripts/trace_chat_uat.py uat-demo 5 14

Read-only. Uses the REAL column names (the issue's SQL guessed some):
chat_query_log.tool_calls (JSON), chat_sessions.state_json (pointer IDs, no PII).
"""
import sys

from app.db.database import get_tenant_session
from app.models.tenant import ChatQueryLog, ChatSession, Document, Party, Term


def trace(tenant_id: str, doc_ids: list[int]) -> None:
    db = get_tenant_session(tenant_id)
    try:
        print(f"\n=== chat_query_log (last 8) — tenant {tenant_id} ===")
        for r in (
            db.query(ChatQueryLog)
            .filter(ChatQueryLog.tenant_id == tenant_id)
            .order_by(ChatQueryLog.created_at.desc())
            .limit(8)
            .all()
        ):
            print(f"[{r.created_at}] found={r.found} n={r.result_count} llm={r.llm_calls}")
            print(f"    Q: {r.question!r}")
            print(f"    tool_calls: {r.tool_calls or '[]'}")

        print("\n=== chat_sessions (last 3) — state_json (pointer IDs only) ===")
        for s in (
            db.query(ChatSession)
            .filter(ChatSession.tenant_id == tenant_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(3)
            .all()
        ):
            print(f"session={s.session_id} updated={s.updated_at} state={s.state_json}")

        for did in doc_ids:
            print(f"\n=== terms — doc {did} ===")
            for t in (
                db.query(Term)
                .filter(Term.tenant_id == tenant_id, Term.document_id == did)
                .all()
            ):
                print(f"  {t.field_name}: {t.field_value!r}  superseded={t.is_superseded} conf={t.confidence}")
            doc = db.query(Document).filter(Document.id == did, Document.tenant_id == tenant_id).first()
            print(f"  file_name: {doc.file_name!r}" if doc else "  (doc not found)")
            parties = db.query(Party).filter(Party.tenant_id == tenant_id, Party.document_id == did).all()
            print(f"  parties: {[(p.name, p.role_label) for p in parties]}")
    finally:
        db.close()


if __name__ == "__main__":
    tid = sys.argv[1] if len(sys.argv) > 1 else "uat-demo"
    ids = [int(x) for x in sys.argv[2:]] or [5, 14]
    trace(tid, ids)
