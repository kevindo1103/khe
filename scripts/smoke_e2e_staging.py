#!/usr/bin/env python3
"""Khế E2E Smoke Test — Staging Vertical Slice (Python, no external deps).

Issue #33 Task F (M0 smoke): login → consent → upload → poll → chat

Usage:
    set KHE_TENANT=<tenant_slug>
    set KHE_USER=<username>
    set KHE_PASS=<password>
    python scripts/smoke_e2e_staging.py [base_url]

    Optional: set KHE_TEST_FILE to a real contract image/PDF path.

Default base_url: https://staging.khe.iceflow.cloud
Requires: Python 3.7+ (stdlib only — no pip install needed)
"""
from __future__ import annotations

import io
import json
import os
import struct
import sys
import tempfile
import time
import zlib
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import (
    HTTPCookieProcessor,
    Request,
    build_opener,
)

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://staging.khe.iceflow.cloud"
TENANT = os.environ.get("KHE_TENANT")
USER = os.environ.get("KHE_USER")
PASS = os.environ.get("KHE_PASS")

if not TENANT or not USER or not PASS:
    print("ERROR: Set KHE_TENANT, KHE_USER, KHE_PASS env vars")
    sys.exit(2)

TEST_FILE = os.environ.get("KHE_TEST_FILE", "")

cookie_jar = CookieJar()
opener = build_opener(HTTPCookieProcessor(cookie_jar))

passed = 0
failed = 0
total = 0


def url(path: str) -> str:
    return BASE.rstrip("/") + path


def step(name: str):
    global total
    total += 1
    print(f"\n── Step {total}: {name} ──")


def ok(msg: str):
    global passed
    passed += 1
    print(f"  ✓ {msg}")


def die(msg: str):
    global failed
    failed += 1
    print(f"  ✗ FAIL: {msg}", file=sys.stderr)


def do_request(
    path: str,
    *,
    method: str = "GET",
    json_body: dict | None = None,
    file_path: str | None = None,
    file_field: str = "file",
) -> tuple[int, str, dict | None]:
    """Returns (status_code, raw_body, parsed_json_or_None)."""
    headers: dict[str, str] = {}
    data: bytes | None = None

    if json_body is not None:
        data = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json"
        if method == "GET":
            method = "POST"

    if file_path is not None:
        boundary = "----KheSmokeFormBoundary"
        body_parts: list[bytes] = []
        fname = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            file_data = f.read()
        body_parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{file_field}"; filename="{fname}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n".encode()
        )
        body_parts.append(file_data)
        body_parts.append(f"\r\n--{boundary}--\r\n".encode())
        data = b"".join(body_parts)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        if method == "GET":
            method = "POST"

    req = Request(url(path), data=data, headers=headers, method=method)
    try:
        resp = opener.open(req)
        body = resp.read().decode("utf-8", errors="replace")
        code = resp.status
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        code = e.code
    except URLError as e:
        return (0, str(e.reason), None)

    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        parsed = None
    return (code, body, parsed)


def make_minimal_png() -> str:
    """Create a valid 1×1 red PNG file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".png")
    with os.fdopen(fd, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
        ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
        f.write(struct.pack(">I", 13) + b"IHDR" + ihdr_data + struct.pack(">I", ihdr_crc))
        raw_row = b"\x00\xff\x00\x00"
        compressed = zlib.compress(raw_row)
        idat_crc = zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF
        f.write(struct.pack(">I", len(compressed)) + b"IDAT" + compressed + struct.pack(">I", idat_crc))
        iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
        f.write(struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc))
    return path


# ── 1. Health check ──────────────────────────────────────────────────
step("Health check")
code, body, _ = do_request("/health")
if code == 200:
    ok(f"GET /health → {code}")
else:
    die(f"GET /health → {code}")

# ── 2. Extraction provider check ─────────────────────────────────────
step("Extraction provider diagnostic")
code, body, data = do_request("/health/extraction")
if code == 200 and data:
    any_prov = data.get("any_provider_configured", "n/a")
    ok(f"GET /health/extraction → 200 (any_provider_configured={any_prov})")
    if any_prov is False:
        print("  ⚠ WARNING: No extraction provider configured — upload+extract will fail")
else:
    die(f"GET /health/extraction → {code} (maybe prod env? expected non-prod)")

# ── 3. Login ─────────────────────────────────────────────────────────
step("Login")
code, body, data = do_request(
    "/auth/login",
    json_body={"tenant_id": TENANT, "username": USER, "password": PASS},
)
if code in (200, 201):
    ok(f"POST /auth/login → {code} (cookie set)")
else:
    die(f"POST /auth/login → {code} — cannot continue without auth")
    print(f"\n══ ABORT: login failed. Check KHE_TENANT/KHE_USER/KHE_PASS. ══")
    print(f"  Response: {body}")
    sys.exit(1)

# ── 4. Verify session ────────────────────────────────────────────────
step("Verify session (GET /auth/me)")
code, body, data = do_request("/auth/me")
if code == 200 and data:
    ok(f"GET /auth/me → 200 (user={data.get('username')}, tenant={data.get('tenant_id')})")
else:
    die(f"GET /auth/me → {code} — session cookie not working")

# ── 5. Grant extraction consent ──────────────────────────────────────
step("Grant vision_extraction consent")
code, body, _ = do_request("/consent", json_body={"purpose": "vision_extraction"})
if code in (200, 201):
    ok(f"POST /consent → {code} (vision_extraction granted)")
else:
    die(f"POST /consent → {code}")

# ── 6. Check consent status ──────────────────────────────────────────
step("Check consent status")
code, body, data = do_request("/consent")
if code == 200 and isinstance(data, list):
    ve = next((c for c in data if c.get("purpose") == "vision_extraction"), None)
    ve_status = ve.get("status", "missing") if ve else "missing"
    ok(f"GET /consent → 200 (vision_extraction={ve_status})")
    if ve_status != "granted":
        print("  ⚠ WARNING: vision_extraction consent not granted — upload may be blocked")
else:
    die(f"GET /consent → {code}")

# ── 7. Upload document ───────────────────────────────────────────────
step("Upload document")
created_test_file = False
test_file = TEST_FILE
if not test_file:
    print("  ℹ KHE_TEST_FILE not set — creating a minimal test PNG")
    test_file = make_minimal_png()
    created_test_file = True

code, body, data = do_request("/ingest/upload", file_path=test_file)

if created_test_file:
    try:
        os.unlink(test_file)
    except OSError:
        pass

doc_id = ""
if code in (200, 201) and data:
    doc_id = data.get("doc_id") or data.get("document_id") or data.get("id") or ""
    ok(f"POST /ingest/upload → {code} (doc_id={doc_id})")
else:
    die(f"POST /ingest/upload → {code}")
    print(f"  Response: {body}")

# ── 8. Poll extraction status ────────────────────────────────────────
step("Poll document extraction status")
if doc_id:
    max_polls = 20
    poll_interval = 3
    doc_status = "unknown"
    doc_data: dict = {}

    for i in range(1, max_polls + 1):
        code, body, doc_data_raw = do_request(f"/documents/{doc_id}")
        doc_data = doc_data_raw or {}
        doc_status = doc_data.get("status", "unknown")
        print(f"  poll {i}/{max_polls}: status={doc_status}")

        if doc_status == "extracted":
            ok("Extraction completed (status=extracted)")

            obligations = doc_data.get("obligations") or []
            clause_count = doc_data.get("clause_count", 0)
            parties = doc_data.get("parties") or []
            provider = doc_data.get("provider", "unknown")
            print(f"  provider={provider} obligations={len(obligations)} clause_count={clause_count} parties={len(parties)}")

            # ── #230 / FR-EX-05 anchor gate ──
            terms = doc_data.get("terms") or []
            term_count = len(terms)
            anchored = sum(1 for t in terms if t.get("page_num") is not None)
            reffed = sum(1 for t in terms if t.get("ref") is not None)
            print(f"  terms={term_count} anchored(page_num)={anchored} with_ref={reffed}")

            if created_test_file:
                print("  ℹ synthetic PNG used — anchor gate SKIPPED. Set KHE_TEST_FILE to a real contract to gate #230.")
            elif provider == "gemini_flash":
                if anchored > 0:
                    ok(f"#230 anchors populate ({anchored}/{term_count} terms have page_num, provider=gemini_flash)")
                else:
                    die("#230 anchors EMPTY on gemini_flash — grammar 'too many states' / silent drop. Fallback: narrow anchor scope to the 4 benchmark fields, re-run.")
            elif provider and provider.startswith("claude"):
                print(f"  ℹ provider={provider} (Claude fallback) — null anchors expected (lean schema). anchored={anchored}.")
                ok("#230 not gated (Claude fallback path, graceful-null by design)")
            else:
                print(f"  ⚠ provider={provider} — cannot gate #230 (expected gemini_flash or claude_*). anchored={anchored}.")
            break

        elif doc_status == "failed":
            reason = doc_data.get("failure_reason", "no reason")
            die(f"Extraction failed: {reason}")
            break

        time.sleep(poll_interval)
    else:
        if doc_status != "extracted":
            die(f"Extraction did not complete within {max_polls * poll_interval}s (last status={doc_status})")
else:
    die("Skipped — no doc_id from upload")

# ── 9. Chat query ────────────────────────────────────────────────────
step("Chat query")
code, body, data = do_request(
    "/chat/query",
    json_body={"question": "Hợp đồng này có những bên nào ký kết?"},
)
if code == 200 and data:
    found = data.get("found", "n/a")
    result_count = data.get("result_count", "n/a")
    ok(f"POST /chat/query → 200 (found={found}, result_count={result_count})")
else:
    die(f"POST /chat/query → {code}")
    print(f"  Response: {body}")

# ── 10. List documents ───────────────────────────────────────────────
step("List documents")
code, body, data = do_request("/documents/")
if code == 200 and data:
    items = data.get("items") or []
    ok(f"GET /documents/ → 200 (count={len(items)})")
else:
    die(f"GET /documents/ → {code}")

# ── 11. Logout ───────────────────────────────────────────────────────
step("Logout")
code, body, _ = do_request("/auth/logout", method="POST")
if code == 200:
    ok("POST /auth/logout → 200")
else:
    die(f"POST /auth/logout → {code}")

# ── Summary ──────────────────────────────────────────────────────────
print(f"\n{'═' * 58}")
print(f"  Smoke test complete: {passed} passed, {failed} failed, {total} total")
print(f"{'═' * 58}")

if failed > 0:
    sys.exit(1)
