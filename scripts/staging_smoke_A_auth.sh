#!/usr/bin/env bash
# Staging UAT smoke — §A Auth (#75 cases A1–A6).
# Cookie-based auth (DEC-#43 / #46). Run from a host with egress to staging.
#
# Usage:
#   bash scripts/staging_smoke_A_auth.sh
#
# Optional env:
#   BASE=https://staging.khe.iceflow.cloud    (default)
#   TENANT=uat-demo                            (default)
#   USER=demo                                  (default)
#   PASS=Khe@UAT2026                           (default; from PR #73 seed)
#
# Exits 0 on all-pass, non-zero on first failure. Per #75 stop rule, do NOT
# continue to §B if A fails.

set -u

BASE="${BASE:-https://staging.khe.iceflow.cloud}"
TENANT="${TENANT:-uat-demo}"
USERNAME="${USER:-demo}"
PASSWORD="${PASS:-Khe@UAT2026}"
JAR="$(mktemp -t khe-jar.XXXXXX)"
trap 'rm -f "$JAR"' EXIT

pass=0; fail=0
ok() { echo "  ✅ $1"; pass=$((pass+1)); }
ko() { echo "  ❌ $1 — $2"; fail=$((fail+1)); }

# Pre-flight: /api/health
echo "── pre-flight: GET /api/health ──"
code=$(curl -sS -o /tmp/khe-health.txt -w "%{http_code}" "$BASE/api/health" || echo "000")
if [[ "$code" == "200" ]]; then
  ok "health → 200 ($(cat /tmp/khe-health.txt))"
else
  ko "health" "expected 200, got $code"
  echo "STOPPING — nginx /api/ proxy not green yet (see #70). Cannot run §A."
  exit 2
fi

# A1 — login success: cookie set, no access_token in body
echo "── A1: POST /api/auth/login (valid) ──"
body=$(curl -sS -c "$JAR" -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"tenant_id\":\"$TENANT\",\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")
if echo "$body" | grep -q '"access_token"'; then
  ko "A1" "access_token leaked in body (DEC-#43 violation)"
elif echo "$body" | grep -q "\"tenant_id\":\"$TENANT\""; then
  if grep -q khe_session "$JAR"; then
    ok "A1 login success — cookie set, no token in body"
  else
    ko "A1" "no khe_session cookie set"
  fi
else
  ko "A1" "unexpected body: $body"
fi

# A2 — /me with cookie → 200
echo "── A2: GET /api/auth/me (cookie) ──"
code=$(curl -sS -b "$JAR" -o /tmp/khe-me.txt -w "%{http_code}" "$BASE/api/auth/me")
if [[ "$code" == "200" ]] && grep -q "\"username\":\"$USERNAME\"" /tmp/khe-me.txt; then
  ok "A2 /me → 200 with user payload"
else
  ko "A2" "expected 200 with user, got $code | body=$(cat /tmp/khe-me.txt)"
fi

# A3 — /me without cookie → 401
echo "── A3: GET /api/auth/me (no cookie) ──"
code=$(curl -sS -o /tmp/khe-me-noauth.txt -w "%{http_code}" "$BASE/api/auth/me")
if [[ "$code" == "401" ]]; then
  ok "A3 /me without cookie → 401"
else
  ko "A3" "expected 401, got $code"
fi

# A4 — logout clears cookie
echo "── A4: POST /api/auth/logout ──"
code=$(curl -sS -b "$JAR" -c "$JAR" -X POST -o /dev/null -w "%{http_code}" "$BASE/api/auth/logout")
if [[ "$code" == "200" ]]; then
  ok "A4 logout → 200"
else
  ko "A4" "expected 200, got $code"
fi

# A5 — /me after logout → 401
echo "── A5: GET /api/auth/me (post-logout) ──"
code=$(curl -sS -b "$JAR" -o /dev/null -w "%{http_code}" "$BASE/api/auth/me")
if [[ "$code" == "401" ]]; then
  ok "A5 post-logout /me → 401"
else
  ko "A5" "expected 401, got $code"
fi

# A6 — wrong credentials → 401, no cookie
echo "── A6: POST /api/auth/login (wrong password) ──"
rm -f "$JAR" && JAR="$(mktemp -t khe-jar.XXXXXX)"
code=$(curl -sS -c "$JAR" -X POST -o /dev/null -w "%{http_code}" "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"tenant_id\":\"$TENANT\",\"username\":\"$USERNAME\",\"password\":\"wrong-$$\"}")
if [[ "$code" == "401" ]] && ! grep -q khe_session "$JAR"; then
  ok "A6 wrong password → 401, no cookie"
else
  ko "A6" "expected 401 + no cookie, got $code (cookie set: $(grep -q khe_session "$JAR" && echo yes || echo no))"
fi

echo
echo "── §A summary: $pass pass / $fail fail ──"
[[ "$fail" -eq 0 ]] || exit 1
