# KHE_Infra — Session State

_Last updated: 2026-06-19 | Sprint 0 COMPLETE + post-Sprint-0 ops + production VPS live_

---

## Current Sprint: Sprint 0 — DONE ✅ + post-Sprint-0 ops

### Status

| Item | Status | Notes |
|---|---|---|
| `pr-quality-gate.yml` | ✅ Done | All PRs. Branch pattern + backend import + alembic single-head + frontend build. Long-lived branches exempted. |
| `deploy-staging.yml` | ✅ Done | bootstrap → rsync → .env (incl. CORS_ORIGINS) → migrate_all_tenants.py → systemctl → HTTPS check |
| `deploy-main.yml` | ✅ Done | bootstrap → rsync → .env (incl. CORS_ORIGINS) → migrate_all_tenants.py → systemctl → Telegram notify |
| GitHub Actions secrets | ✅ Done | 8 secrets set (see below) |
| GitHub Environments | ✅ Done | `staging` + `production` created |
| API key injection to VPS | ✅ Done | GEMINI_API_KEY, CLAUDE_API_KEY, JWT_SECRET, TELEGRAM_BOT_TOKEN, CORS_ORIGINS written to `.env` via SSH stdin pipe |
| VPS dir bootstrap | ✅ Done | `mkdir -p` + `python3 -m venv` idempotent before first rsync |
| Telegram notify | ✅ Live | ✅/❌ firing on production deploy |
| Hotpatch playbook | ✅ Done | Documented below |
| `staging` sync ← `main` | ✅ Done | Re-synced after PR #48 merge |
| Per-tenant migrations wired | ✅ Done | `python scripts/migrate_all_tenants.py` after `alembic upgrade head` (PR #48) |
| CORS_ORIGINS injected | ✅ Done | staging=`https://staging.khe.iceflow.cloud`, prod=`https://khe.iceflow.cloud` |
| TLS / HTTPS | ✅ Done | certbot issued cert for `khe.iceflow.cloud` + `staging.khe.iceflow.cloud`. DNS A records set (`14.225.212.116`) |
| HTTPS check in deploy-staging | ✅ Done | Non-blocking warning step — fires if staging TLS unreachable |
| Production VPS bootstrap | ✅ Done | `/opt/khe/backend/` + venv + `khe-backend.service` enabled (2026-06-19) |
| Production nginx config | ✅ Done | `/etc/nginx/sites-available/khe` rewritten + enabled in sites-enabled. Trailing slash on `proxy_pass`. |
| `khe-backend-staging` stale proc fix | ✅ Done | Killed stale uvicorn holding port 8001, systemd service now owns port cleanly |
| `migrate_all_tenants.py` guard | ✅ Done | deploy-main.yml guarded with `[ -f ... ] &&` — script on staging, not yet on main |

### Bug + ops fixes post-Sprint-0

| Fix | PR / action | Issue |
|---|---|---|
| Wire `migrate_all_tenants.py` into deploy | #48 | #45 item 1 — tenant_002+ schema not applying |
| Triage phantom deploy failures | annotated | #45 item 2 — 0-job failure runs from feature branches (not real) |
| Inject CORS_ORIGINS into .env | #48 | #45 item 3 — credentialed CORS broken with wildcard |
| HTTPS staging warning step | #48 | #45 item 4 — auth cookie Secure flag needs TLS |
| Domain khe.vn → khe.iceflow.cloud | #48 | domain not yet acquired |
| DNS A records + certbot TLS | VPS ops | staging.khe.iceflow.cloud + khe.iceflow.cloud live |

### Bug fixes shipped Sprint 0

| Fix | PR | Issue |
|---|---|---|
| Skip rsync when `backend/` absent | #8 | Deploy crash on empty repo |
| Quality gate fires on all PRs | #13 | PR #12 had no check runs |
| Sync `staging` ← `main` | direct push | #15 — staging had no `.github/` |
| Inject API keys into VPS `.env` | #18 | GEMINI/CLAUDE keys were None → 401 |
| Exempt long-lived branches from pattern check | #21 | #20 — staging→main promote blocked |
| Bootstrap VPS dirs before rsync | #21 | #20 — rsync code 11 on first deploy |

---

## Required GitHub Actions Secrets

Go to: **repo Settings → Secrets and variables → Actions → New repository secret**

### Application secrets (shared staging + prod)

| Secret name | Value | Who provides |
|---|---|---|
| `JWT_SECRET` | Random 64-char hex string (`openssl rand -hex 32`) | ✅ Set |
| `GEMINI_API_KEY` | Google AI Studio key | ✅ Set |
| `CLAUDE_API_KEY` | Anthropic API key | ✅ Set |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | ✅ Set |
| `TELEGRAM_CHAT_ID` | Chat ID for deploy notifications | ✅ Set |

### VPS secrets (dùng chung staging + production — cùng 1 VPS, khác port/folder)

| Secret name | Value |
|---|---|
| `VPS_HOST` | ✅ Set |
| `VPS_USER` | ✅ Set |
| `VPS_SSH_KEY` | ✅ Set (`ed25519`, generated via `ssh-keygen -t ed25519 -C "khe-deploy"`) |

---

## VPS Port Allocation (CRITICAL — shared VPS với Bingxue ERP)

**VPS IP:** `14.225.212.116`

| Port | systemd service | Project | Path |
|------|----------------|---------|------|
| **8000** | `khe-backend` | **Khế production** | `/opt/khe/backend/` |
| **8001** | `khe-backend-staging` | **Khế staging** | `/opt/khe/backend-staging/` |
| **8002** | `bingxue-api-staging` | Bingxue ERP staging | — |
| **8003** | `bingxue-api` | Bingxue ERP production | — |

**KHÔNG dùng port 8002/8003 cho Khế** — đang được Bingxue ERP chiếm.

nginx configs:
- `/etc/nginx/sites-available/khe` → production (`khe.iceflow.cloud`, port 8000)
- `/etc/nginx/sites-available/khe-staging` → staging (`staging.khe.iceflow.cloud`, port 8001)

---

## GitHub Environments

Create two environments in **repo Settings → Environments**:
- `staging`
- `production`

Each environment can optionally add protection rules (required reviewers, wait timer) before production deploys.

---

## VPS Setup Checklist (Sprint 0 — to do when VPS provisioned)

```
[ ] Ubuntu 22.04 LTS
[ ] Create deploy user, add SSH pubkey
[ ] Install: python3.11, python3-venv, nginx, nodejs 20.x
[ ] mkdir -p /opt/khe/backend /opt/khe/frontend /opt/khe/frontend-staging
[ ] Create Python venv: python3.11 -m venv /opt/khe/backend/venv
[ ] Create systemd units: khe-backend, khe-backend-staging (see below)
[ ] Configure nginx (see §Nginx Config below)
[ ] Add deploy user to sudoers for: systemctl restart khe-backend*, nginx reload
[ ] Copy initial .env from backend/.env.example (fill secrets)
```

---

## Systemd Unit Template

`/etc/systemd/system/khe-backend.service`:

```ini
[Unit]
Description=Khế Backend (Production)
After=network.target

[Service]
User=deploy
WorkingDirectory=/opt/khe/backend
EnvironmentFile=/opt/khe/backend/.env
ExecStart=/opt/khe/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
# .env is written by deploy-main.yml on every deploy (GEMINI_API_KEY, CLAUDE_API_KEY, JWT_SECRET, TELEGRAM_BOT_TOKEN)
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Duplicate for `khe-backend-staging.service` with port 8001.

---

## Nginx Config Template

`/etc/nginx/sites-available/khe`:

```nginx
server {
    listen 80;
    server_name khe.iceflow.cloud www.khe.iceflow.cloud;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name khe.iceflow.cloud www.khe.iceflow.cloud;

    # TLS — use certbot / Let's Encrypt
    ssl_certificate /etc/letsencrypt/live/khe.iceflow.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/khe.iceflow.cloud/privkey.pem;

    root /opt/khe/frontend;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}

# Staging vhost (staging.khe.iceflow.cloud)
server {
    listen 443 ssl;
    server_name staging.khe.iceflow.cloud;

    ssl_certificate /etc/letsencrypt/live/staging.khe.iceflow.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.khe.iceflow.cloud/privkey.pem;

    root /opt/khe/frontend-staging;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## Hotpatch Playbook (Emergency Only)

**Trigger:** Production down + GitHub Actions CI unreachable or > 10 min queue.
**Requires:** Backend lead approve + PM aware.

```bash
# 1. SSH into VPS (only authorized in emergency)
ssh deploy@<PROD_VPS_HOST>

# 2. Hotpatch backend (nano edit or git pull from a pre-pushed branch)
cd /opt/khe/backend
git fetch origin main && git checkout origin/main -- <specific_file.py>

# 3. Restart service
sudo systemctl restart khe-backend

# 4. Verify
curl -s http://127.0.0.1:8000/health

# 5. Document incident in DOCS_INBOX (issue #1) within 1h
#    Title: INC-XX: <description>
#    Include: symptom, root cause, hotpatch applied, follow-up PR needed
```

**Post-hotpatch:** A proper PR MUST follow within 24h to bring main in sync. Hotpatch is never a substitute for a reviewed PR.

---

## Workflow Files

| File | Trigger | Jobs |
|---|---|---|
| `pr-quality-gate.yml` | PR → main, staging | branch-pattern-check, backend-check, frontend-check |
| `deploy-staging.yml` | push → staging, workflow_dispatch | quality-gate, deploy-staging |
| `deploy-main.yml` | push → main, workflow_dispatch | quality-gate, deploy-production |

---

## Change Log

| Date | Change | Branch |
|---|---|---|
| 2026-06-11 | Initial Sprint 0 setup: 3 workflow files + this STATE file | claude/infra-ci-quality-gate |
