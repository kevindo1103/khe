#!/usr/bin/env python3
"""Regenerate backend/openapi.json from the running FastAPI app."""
import json
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from main import app

def main() -> None:
    openapi_schema = app.openapi()
    out_path = os.path.join(backend_dir, "openapi.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, ensure_ascii=False, indent=2)
    print(f"[regen_openapi] Wrote {out_path}")


if __name__ == "__main__":
    main()
