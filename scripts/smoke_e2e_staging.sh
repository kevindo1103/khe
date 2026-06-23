#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# Khế E2E Smoke Test — Staging Vertical Slice
# Issue #33 Task F (M0 smoke): login → consent → upload → poll → chat
#
# Usage:
#   export KHE_TENANT=<tenant_slug>
#   export KHE_USER=<username>
#   export KHE_PASS=<password>
#   bash scripts/smoke_e2e_staging.sh [base_url]
#
# Default base_url: https://staging.khe.iceflow.cloud
# Requires: curl, jq
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

BASE="${1:-https://staging.khe.iceflow.cloud}"
TENANT="${KHE_TENANT:?Set KHE_TENANT env var}"
USER="${KHE_USER:?Set KHE_USER env var}"
PASS="${KHE_PASS:?Set KHE_PASS env var}"
COOKIE_JAR=$(mktemp /tmp/khe_cookies.XXXXXX)
TEST_FILE="${KHE_TEST_FILE:-}"  # optional: path to a contract image/PDF

trap 'rm -f "$COOKIE_JAR"' EXIT

pass=0
fail=0
total=0

step() {
  total=$((total + 1))
  printf "\n── Step %d: %s ──\n" "$total" "$1"
}

ok() {
  pass=$((pass + 1))
  printf "  ✓ %s\n" "$1"
}

die() {
  fail=$((fail + 1))
  printf "  ✗ FAIL: %s\n" "$1" >&2
}

# ── 1. Health check ──────────────────────────────────────────────────
step "Health check"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/health")
if [ "$HTTP" = "200" ]; then ok "GET /health → 200"; else die "GET /health → $HTTP"; fi

# ── 2. Extraction provider check (non-prod diagnostic) ──────────────
step "Extraction provider diagnostic"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/health/extraction")
if [ "$HTTP" = "200" ]; then
  BODY=$(curl -s "$BASE/health/extraction")
  ANY=$(echo "$BODY" | jq -r '.any_provider_configured')
  ok "GET /health/extraction → 200 (any_provider_configured=$ANY)"
  if [ "$ANY" = "false" ]; then
    printf "  ⚠ WARNING: No extraction provider configured — upload+extract will fail\n"
  fi
else
  die "GET /health/extraction → $HTTP (maybe prod env? expected non-prod)"
fi

# ── 3. Login ─────────────────────────────────────────────────────────
step "Login"
LOGIN_BODY=$(jq -n --arg t "$TENANT" --arg u "$USER" --arg p "$PASS" \
  '{tenant_id: $t, username: $u, password: $p}')
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -c "$COOKIE_JAR" \
  -H "Content-Type: application/json" \
  -d "$LOGIN_BODY" \
  "$BASE/auth/login")
if [ "$HTTP" = "200" ] || [ "$HTTP" = "201" ]; then
  ok "POST /auth/login → $HTTP (cookie set)"
else
  die "POST /auth/login → $HTTP — cannot continue without auth"
  printf "\n══ ABORT: login failed. Check KHE_TENANT/KHE_USER/KHE_PASS. ══\n"
  exit 1
fi

# ── 4. Verify session ────────────────────────────────────────────────
step "Verify session (GET /auth/me)"
ME_BODY=$(curl -s -b "$COOKIE_JAR" "$BASE/auth/me")
HTTP=$(curl -s -o /dev/null -w "%{http_code}" -b "$COOKIE_JAR" "$BASE/auth/me")
if [ "$HTTP" = "200" ]; then
  ME_USER=$(echo "$ME_BODY" | jq -r '.username // empty')
  ME_TENANT=$(echo "$ME_BODY" | jq -r '.tenant_id // empty')
  ok "GET /auth/me → 200 (user=$ME_USER, tenant=$ME_TENANT)"
else
  die "GET /auth/me → $HTTP — session cookie not working"
fi

# ── 5. Grant extraction consent (NĐ 13/2023 gate) ───────────────────
step "Grant vision_extraction consent"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -b "$COOKIE_JAR" \
  -H "Content-Type: application/json" \
  -d '{"purpose":"vision_extraction"}' \
  "$BASE/consent")
if [ "$HTTP" = "201" ] || [ "$HTTP" = "200" ]; then
  ok "POST /consent → $HTTP (vision_extraction granted)"
else
  die "POST /consent → $HTTP"
fi

# ── 6. List consent status ───────────────────────────────────────────
step "Check consent status"
CONSENT_BODY=$(curl -s -b "$COOKIE_JAR" "$BASE/consent")
HTTP=$(curl -s -o /dev/null -w "%{http_code}" -b "$COOKIE_JAR" "$BASE/consent")
if [ "$HTTP" = "200" ]; then
  VE_STATUS=$(echo "$CONSENT_BODY" | jq -r '.[] | select(.purpose=="vision_extraction") | .status // "missing"')
  ok "GET /consent → 200 (vision_extraction=$VE_STATUS)"
  if [ "$VE_STATUS" != "granted" ]; then
    printf "  ⚠ WARNING: vision_extraction consent not granted — upload may be blocked\n"
  fi
else
  die "GET /consent → $HTTP"
fi

# ── 7. Upload document ───────────────────────────────────────────────
step "Upload document"
if [ -z "$TEST_FILE" ]; then
  printf "  ℹ KHE_TEST_FILE not set — creating a minimal test PNG\n"
  # 1×1 red PNG (67 bytes) — enough to test the pipeline plumbing.
  # Extraction will return low-confidence / empty fields, which is expected.
  TEST_FILE=$(mktemp /tmp/khe_test_XXXXXX.png)
  printf '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82' > "$TEST_FILE"
  CREATED_TEST_FILE=1
fi

# Single call — capture body + HTTP code together (a second curl would upload twice,
# burning quota + creating a duplicate doc).
UPLOAD_OUT=$(curl -s -w "\n%{http_code}" -b "$COOKIE_JAR" \
  -F "file=@${TEST_FILE}" \
  "$BASE/ingest/upload")
HTTP=$(printf '%s' "$UPLOAD_OUT" | tail -n1)
UPLOAD_RESP=$(printf '%s' "$UPLOAD_OUT" | sed '$d')

# Clean up generated test file
if [ "${CREATED_TEST_FILE:-}" = "1" ]; then rm -f "$TEST_FILE"; fi

if [ "$HTTP" = "201" ] || [ "$HTTP" = "200" ]; then
  # UploadOut.doc_id is the canonical field (backend/app/schemas/documents.py).
  DOC_ID=$(echo "$UPLOAD_RESP" | jq -r '.doc_id // .document_id // .id // empty')
  ok "POST /ingest/upload → $HTTP (doc_id=$DOC_ID)"
else
  die "POST /ingest/upload → $HTTP"
  printf "  Response: %s\n" "$UPLOAD_RESP"
  DOC_ID=""
fi

# ── 8. Poll extraction status ────────────────────────────────────────
step "Poll document extraction status"
if [ -n "$DOC_ID" ]; then
  MAX_POLLS=20
  POLL_INTERVAL=3
  for i in $(seq 1 $MAX_POLLS); do
    DOC_RESP=$(curl -s -b "$COOKIE_JAR" "$BASE/documents/$DOC_ID")
    # Terminal success = "extracted", failure = "failed" (extraction_runner.py).
    DOC_STATUS=$(echo "$DOC_RESP" | jq -r '.status // "unknown"')
    printf "  poll %d/%d: status=%s\n" "$i" "$MAX_POLLS" "$DOC_STATUS"

    if [ "$DOC_STATUS" = "extracted" ]; then
      ok "Extraction completed (status=extracted)"

      # DocumentDetailOut fields: obligations[] · clause_count (int) · parties[] · terms[]
      # · provider (#233/#235 — last extraction provider).
      OBL_COUNT=$(echo "$DOC_RESP" | jq '[.obligations // [] | length] | .[0]')
      CLAUSE_COUNT=$(echo "$DOC_RESP" | jq -r '.clause_count // 0')
      PARTY_COUNT=$(echo "$DOC_RESP" | jq '[.parties // [] | length] | .[0]')
      PROVIDER=$(echo "$DOC_RESP" | jq -r '.provider // "unknown"')
      printf "  provider=%s obligations=%s clause_count=%s parties=%s\n" \
        "$PROVIDER" "$OBL_COUNT" "$CLAUSE_COUNT" "$PARTY_COUNT"

      # ── #230 / FR-EX-05 anchor gate ──
      # provider is now on DocumentDetailOut (#233/#235), so the gate is machine-clean:
      #   gemini_flash → anchors REQUIRED (null = grammar 'too many states' / drop = FAIL)
      #   claude_*     → anchors null is correct (lean fallback schema is anchor-free)
      # Still skipped on the synthetic PNG (no extractable terms → would false-fail).
      TERM_COUNT=$(echo "$DOC_RESP" | jq '[.terms // [] | length] | .[0]')
      ANCHORED=$(echo "$DOC_RESP" | jq '[.terms // [] | map(select(.page_num != null)) | length] | .[0]')
      REFFED=$(echo "$DOC_RESP" | jq '[.terms // [] | map(select(.ref != null)) | length] | .[0]')
      printf "  terms=%s anchored(page_num)=%s with_ref=%s\n" "$TERM_COUNT" "$ANCHORED" "$REFFED"
      if [ "${CREATED_TEST_FILE:-}" = "1" ]; then
        printf "  ℹ synthetic PNG used — anchor gate SKIPPED. Set KHE_TEST_FILE to a real contract to gate #230.\n"
      elif [ "$PROVIDER" = "gemini_flash" ]; then
        if [ "${ANCHORED:-0}" -gt 0 ] 2>/dev/null; then
          ok "#230 anchors populate ($ANCHORED/$TERM_COUNT terms have page_num, provider=gemini_flash)"
        else
          die "#230 anchors EMPTY on gemini_flash — grammar 'too many states' / silent drop. Fallback: narrow anchor scope to the 4 benchmark fields, re-run."
        fi
      elif printf '%s' "$PROVIDER" | grep -q '^claude'; then
        printf "  ℹ provider=%s (Claude fallback) — null anchors expected (lean schema). anchored=%s.\n" "$PROVIDER" "$ANCHORED"
        ok "#230 not gated (Claude fallback path, graceful-null by design)"
      else
        printf "  ⚠ provider=%s — cannot gate #230 (expected gemini_flash or claude_*). anchored=%s.\n" "$PROVIDER" "$ANCHORED"
      fi
      break
    elif [ "$DOC_STATUS" = "failed" ]; then
      die "Extraction failed: $(echo "$DOC_RESP" | jq -r '.failure_reason // "no reason"')"
      break
    fi

    sleep "$POLL_INTERVAL"
  done

  if [ "$i" = "$MAX_POLLS" ] && [ "$DOC_STATUS" != "extracted" ]; then
    die "Extraction did not complete within $((MAX_POLLS * POLL_INTERVAL))s (last status=$DOC_STATUS)"
  fi
else
  die "Skipped — no doc_id from upload"
fi

# ── 9. Chat query against uploaded document ──────────────────────────
step "Chat query"
CHAT_BODY=$(jq -n '{question: "Hợp đồng này có những bên nào ký kết?"}')
CHAT_RESP=$(curl -s -b "$COOKIE_JAR" \
  -H "Content-Type: application/json" \
  -d "$CHAT_BODY" \
  "$BASE/chat/query")
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -b "$COOKIE_JAR" \
  -H "Content-Type: application/json" \
  -d "$CHAT_BODY" \
  "$BASE/chat/query")
if [ "$HTTP" = "200" ]; then
  FOUND=$(echo "$CHAT_RESP" | jq -r '.found // "n/a"')
  RESULT_COUNT=$(echo "$CHAT_RESP" | jq -r '.result_count // "n/a"')
  ok "POST /chat/query → 200 (found=$FOUND, result_count=$RESULT_COUNT)"
else
  die "POST /chat/query → $HTTP"
  printf "  Response: %s\n" "$CHAT_RESP"
fi

# ── 10. List documents (verify uploaded doc appears) ─────────────────
step "List documents"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" -b "$COOKIE_JAR" "$BASE/documents/")
if [ "$HTTP" = "200" ]; then
  LIST_BODY=$(curl -s -b "$COOKIE_JAR" "$BASE/documents/")
  DOC_COUNT=$(echo "$LIST_BODY" | jq '.items | length // 0' 2>/dev/null || echo "?")
  ok "GET /documents/ → 200 (count=$DOC_COUNT)"
else
  die "GET /documents/ → $HTTP"
fi

# ── 11. Logout ───────────────────────────────────────────────────────
step "Logout"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" -b "$COOKIE_JAR" -X POST "$BASE/auth/logout")
if [ "$HTTP" = "200" ]; then
  ok "POST /auth/logout → 200"
else
  die "POST /auth/logout → $HTTP"
fi

# ── Summary ──────────────────────────────────────────────────────────
printf "\n══════════════════════════════════════════════════════════\n"
printf "  Smoke test complete: %d passed, %d failed, %d total\n" "$pass" "$fail" "$total"
printf "══════════════════════════════════════════════════════════\n"

if [ "$fail" -gt 0 ]; then exit 1; fi
