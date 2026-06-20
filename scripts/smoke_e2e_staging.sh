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
if [ "$HTTP" = "201" ]; then
  ok "POST /auth/login → 201 (cookie set)"
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

UPLOAD_RESP=$(curl -s -b "$COOKIE_JAR" \
  -F "file=@${TEST_FILE}" \
  "$BASE/ingest/upload")
HTTP=$(curl -s -o /dev/null -w "%{http_code}" -b "$COOKIE_JAR" \
  -F "file=@${TEST_FILE}" \
  "$BASE/ingest/upload")

# Clean up generated test file
if [ "${CREATED_TEST_FILE:-}" = "1" ]; then rm -f "$TEST_FILE"; fi

if [ "$HTTP" = "201" ] || [ "$HTTP" = "200" ]; then
  DOC_ID=$(echo "$UPLOAD_RESP" | jq -r '.document_id // .id // empty')
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
    DOC_STATUS=$(echo "$DOC_RESP" | jq -r '.extraction_status // .status // "unknown"')
    printf "  poll %d/%d: status=%s\n" "$i" "$MAX_POLLS" "$DOC_STATUS"

    if [ "$DOC_STATUS" = "completed" ] || [ "$DOC_STATUS" = "done" ]; then
      ok "Extraction completed"

      # Check for obligation_schedule (DEC-030 Phase 2)
      OBL_COUNT=$(echo "$DOC_RESP" | jq '[.obligation_schedule // [] | length] | .[0]')
      CLAUSE_COUNT=$(echo "$DOC_RESP" | jq '[.clauses // [] | length] | .[0]')
      PARTY_COUNT=$(echo "$DOC_RESP" | jq '[.parties // [] | length] | .[0]')
      COST=$(echo "$DOC_RESP" | jq -r '.cost_vnd // "n/a"')
      PROVIDER=$(echo "$DOC_RESP" | jq -r '.provider // "n/a"')
      printf "  provider=%s cost_vnd=%s obligations=%s clauses=%s parties=%s\n" \
        "$PROVIDER" "$COST" "$OBL_COUNT" "$CLAUSE_COUNT" "$PARTY_COUNT"
      break
    elif [ "$DOC_STATUS" = "failed" ] || [ "$DOC_STATUS" = "error" ]; then
      die "Extraction failed"
      printf "  Response: %s\n" "$(echo "$DOC_RESP" | jq -c '.')"
      break
    fi

    sleep "$POLL_INTERVAL"
  done

  if [ "$i" = "$MAX_POLLS" ] && [ "$DOC_STATUS" != "completed" ] && [ "$DOC_STATUS" != "done" ]; then
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
