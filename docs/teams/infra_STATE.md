# KHE_Infra — Session State

_Last updated: 2026-06-23 | Sprint 0 COMPLETE + Sprint 1 COMPLETE_

---

## Current Sprint: Sprint 1 — DONE ✅

### Status

| Item | Status | Notes |
|---|---|---|
| `pr-quality-gate.yml` | ✅ Done | All PRs. Branch pattern + backend import + alembic single-head + frontend build. Long-lived branches exempted. |
| `deploy-staging.yml` | ✅ Done | bootstrap → rsync (data-safe excludes) → .env (incl. CORS_ORIGINS, DATA_DIR, ENVIRONMENT) → migrate_all_tenants.py → systemctl → HTTPS check |
| `deploy-main.yml` | ✅ Done | Same as staging + guarded migrate script + Telegram notify ✅/❌ |
| GitHub Actions secrets | ✅ Done | 8 secrets set (see below) |
| GitHub Environments | ✅ Done | `staging` + `production` created |
| API key injection to VPS | ✅ Done | GEMINI_API_KEY, CLAUDE_API_KEY, JWT_SECRET, TELEGRAM_BOT_TOKEN, CORS_ORIGINS, DATA_DIR, ENVIRONMENT written to `.env` via SSH stdin pipe |
| VPS dir bootstrap | ✅ Done | `mkdir -p` + `python3 -m venv` idempotent before first rsync |
| Telegram notify | ✅ Live | ✅/❌ firing on production deploy |
| Hotpatch playbook | ✅ Done | Documented below |
| `staging` sync ← `main` | ✅ Done | Re-synced after PR #48 merge |
| Per-tenant migrations wired | ✅ Done | `python scripts/migrate_all_tenants.py` after `alembic upgrade head` (PR #48) |
| CORS_ORIGINS injected | ✅ Done | staging=`https://staging.khe.iceflow.cloud`, prod=`https://khe.iceflow.cloud` |
| TLS / HTTPS | ✅ Done | certbot issued cert for `khe.iceflow.cloud` + `staging.khe.iceflow.cloud`. DNS A records set (`14.225.212.116`) |
| HTTPS check in deploy-staging | ✅ Done | Non-blocking warning step — fires if staging TLS unreachable |
| Production VPS bootstrap | ✅ Done | `/opt/khe/backend/` + venv + `khe-backend.service` enabled |
| Production nginx config | ✅ Done | `/etc/nginx/sites-available/khe` live. Trailing slash on `proxy_pass`. `client_max_body_size 50M`. |
| `khe-backend-staging` stale proc fix | ✅ Done | Killed stale uvicorn holding port 8001, systemd service now owns port cleanly |
| `migrate_all_tenants.py` guard | ✅ Done | deploy-main.yml guarded with `[ -f ... ] &&` — script on staging, not yet on main |
| rsync data-safe excludes (#87) | ✅ Done | `--exclude=master.db --exclude='tenants/' --exclude='storage/'` in both workflows |
| DATA_DIR injected to .env (#97) | ✅ Done | staging→`/opt/khe/data-staging`, prod→`/opt/khe/data`. Backend reads `DATA_DIR` env. |
| ENVIRONMENT injected to .env | ✅ Done | `staging` / `production` — controls FastAPI docs visibility |
| nginx `client_max_body_size 50M` (#88) | ✅ Done | Both vhosts. Fixes 413 on PDF upload. |
| Cookie proxy headers (#136) | ✅ Done | `proxy_set_header Cookie $http_cookie` + `proxy_pass_header Set-Cookie` on `/api/` location in staging vhost |
| PWA removed from nginx routing | ✅ Done | `/pwa` location block removed. Admin SPA at `/`, no PWA route. |
| SW kill-switch at `/sw.js` | ✅ Done | `/opt/khe/sw-kill.js` served via nginx location block. Auto-unregisters cached service workers. |
| Uptime monitoring (#29) | ✅ Done | `khe-health-check.timer` fires every 5 min → Telegram alert on non-200 |
| Daily backup (#29) | ✅ Done | `khe-backup.timer` fires at 02:00 → tar.gz of `data/` + `data-staging/`, 30-day retention |
| `smoke-staging` workflow (#234) | ✅ Done | `workflow_dispatch` — runs `smoke_e2e_staging.sh` from CI with staging secrets + contract PDF |

### Bug + ops fixes Sprint 1

| Fix | PR / action | Issue |
|---|---|---|
| Wire `migrate_all_tenants.py` into deploy | #48 | #45 item 1 — tenant_002+ schema not applying |
| Inject CORS_ORIGINS into .env | #48 | #45 item 3 — credentialed CORS broken with wildcard |
| HTTPS staging warning step | #48 | #45 item 4 — auth cookie Secure flag needs TLS |
| Domain khe.vn → khe.iceflow.cloud | #48 | domain not yet acquired |
| DNS A records + certbot TLS | VPS ops | staging.khe.iceflow.cloud + khe.iceflow.cloud live |
| rsync --delete wipes DB files | workflows update | #87 — added data-safe excludes |
| nginx 413 on PDF upload | VPS ops + workflows | #88 — `client_max_body_size 50M` |
| Cookie not forwarded to backend | VPS ops | #136 — `proxy_set_header Cookie` + `proxy_pass_header Set-Cookie` |
| PWA SW cache trap (login → /chat) | VPS ops | Cached SW routed all traffic to PWA. Kill-switch at `/sw.js` unregisters SW. PWA route removed. |
| DATA_DIR mismatch (data outside venv) | workflows + VPS ops | #97 — DATA_DIR env + one-time migration of tenant DBs to correct path |
| Production VPS not bootstrapped | VPS ops | Dirs, venv, systemd units, nginx all set up manually |

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

### Smoke test secrets (staging Environment only)

| Secret name | Value |
|---|---|
| `STAGING_TENANT` | ✅ Set |
| `STAGING_USER` | ✅ Set |
| `STAGING_PASS` | ✅ Set |
| `STAGING_CONTRACT_B64` | ✅ Set (PII-scrubbed PDF, base64-encoded) |

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

## VPS Directory Layout

```
/opt/khe/
├── backend/              ← production backend (rsync target)
│   ├── venv/             ← excluded from rsync
│   └── .env              ← written by CI/CD on every deploy
├── backend-staging/      ← staging backend (rsync target)
│   ├── venv/
│   └── .env
├── frontend/             ← production Admin SPA (rsync target)
├── frontend-staging/     ← staging Admin SPA
├── data/                 ← production data (NOT in rsync target — durable)
│   ├── master.db
│   └── tenants/
├── data-staging/         ← staging data (durable)
│   ├── master.db
│   └── tenants/
├── scripts/
│   ├── health-check.sh   ← uptime monitor (called by systemd timer)
│   └── backup.sh         ← daily backup (called by systemd timer)
├── backups/              ← tar.gz archives, 30-day retention
└── sw-kill.js            ← PWA service worker kill-switch (served at /sw.js)
```

---

## Monitoring & Backup (Sprint 1)

### Health check

`/opt/khe/scripts/health-check.sh` — checks `/health` on both staging + prod every 5 min. Sends Telegram alert if non-200.

```bash
#!/bin/bash
source /opt/khe/backend-staging/.env
check() {
    local NAME=$1; local URL=$2; local STATUS
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$URL" 2>/dev/null || echo "000")
    if [ "$STATUS" != "200" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_CHAT_ID}" \
            -d text="🚨 Khế ${NAME} DOWN — /health returned HTTP ${STATUS}" > /dev/null
    fi
}
check "staging" "https://staging.khe.iceflow.cloud/api/health"
check "production" "https://khe.iceflow.cloud/api/health"
```

Systemd units:
- `/etc/systemd/system/khe-health-check.service`
- `/etc/systemd/system/khe-health-check.timer` — `OnCalendar=*:0/5` (every 5 min)

### Backup

`/opt/khe/scripts/backup.sh` — tars `data/` + `data-staging/` to `/opt/khe/backups/`. Deletes archives older than 30 days.

```bash
#!/bin/bash
BACKUP_DIR=/opt/khe/backups
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/data-staging-${DATE}.tar.gz" /opt/khe/data-staging/ 2>/dev/null
tar -czf "$BACKUP_DIR/data-${DATE}.tar.gz" /opt/khe/data/ 2>/dev/null
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
echo "[$DATE] Backup OK → $BACKUP_DIR"
```

Systemd units:
- `/etc/systemd/system/khe-backup.service`
- `/etc/systemd/system/khe-backup.timer` — `OnCalendar=*-*-* 02:00:00` (daily 02:00)

---

## GitHub Environments

Two environments in **repo Settings → Environments**:
- `staging`
- `production` (with required reviewer protection recommended)

---

## Systemd Unit Templates

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
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Duplicate for `khe-backend-staging.service` with `WorkingDirectory=/opt/khe/backend-staging`, `EnvironmentFile=/opt/khe/backend-staging/.env`, port 8001.

---

## Nginx Config (Current — Live on VPS)

### Production: `/etc/nginx/sites-available/khe`

```nginx
server {
    listen 80;
    server_name khe.iceflow.cloud www.khe.iceflow.cloud;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name khe.iceflow.cloud www.khe.iceflow.cloud;

    ssl_certificate /etc/letsencrypt/live/khe.iceflow.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/khe.iceflow.cloud/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 50M;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Cookie $http_cookie;
        proxy_pass_header Set-Cookie;
    }

    location / {
        root /opt/khe/frontend;
        try_files $uri /index.html;
    }
}
```

### Staging: `/etc/nginx/sites-available/khe-staging`

```nginx
server {
    listen 80;
    server_name staging.khe.iceflow.cloud;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name staging.khe.iceflow.cloud;

    ssl_certificate /etc/letsencrypt/live/staging.khe.iceflow.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.khe.iceflow.cloud/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 50M;

    location /api/ {
        proxy_pass http://127.0.0.1:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Cookie $http_cookie;
        proxy_pass_header Set-Cookie;
    }

    # PWA service worker kill-switch — auto-unregisters any cached SW
    location = /sw.js {
        alias /opt/khe/sw-kill.js;
        add_header Content-Type "application/javascript";
        add_header Cache-Control "no-store";
    }

    location / {
        root /opt/khe/frontend-staging;
        try_files $uri /index.html;
    }
}
```

### SW kill-switch: `/opt/khe/sw-kill.js`

```javascript
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', async () => {
  const keys = await caches.keys();
  await Promise.all(keys.map(k => caches.delete(k)));
  await self.registration.unregister();
  const clients = await self.clients.matchAll({ type: 'window' });
  clients.forEach(c => c.navigate(c.url));
});
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
| `smoke-staging.yml` | workflow_dispatch only | smoke (runs `smoke_e2e_staging.sh` with staging secrets) |

---

## Change Log

| Date | Change | Branch / Action |
|---|---|---|
| 2026-06-11 | Initial Sprint 0 setup: 3 workflow files + this STATE file | claude/infra-ci-quality-gate |
| 2026-06-19 | Production VPS bootstrap: dirs, venv, systemd units, nginx | VPS ops |
| 2026-06-23 | Sprint 1 complete: rsync data-safe excludes, DATA_DIR, Cookie proxy, SW kill-switch, monitoring timer, daily backup | Various PRs + VPS ops |
| 2026-06-26 | smoke-staging workflow (#234), infra_STATE Sprint 1 update, smoke secrets set | PR #239 |
