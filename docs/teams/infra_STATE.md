# KHE_Infra — Session State

_Last updated: 2026-06-11 | Branch: claude/infra-ci-quality-gate_

---

## Current Sprint: Sprint 0

### Status

| Item | Status | Notes |
|---|---|---|
| `pr-quality-gate.yml` | ✅ Done | Triggers on PR → main/staging. Branch pattern + backend import + alembic single-head + frontend build. |
| `deploy-staging.yml` | ✅ Done | Push to `staging` → quality gate → rsync + systemctl restart. Needs VPS secrets. |
| `deploy-main.yml` | ✅ Done | Push to `main` → quality gate → rsync + systemctl restart + Telegram notify. Needs VPS secrets. |
| GitHub Actions secrets | ⏳ Pending | User must add in repo Settings → Secrets (see below). |
| Hotpatch playbook | ✅ Done (below) | Documented under §Hotpatch Playbook. |

---

## Required GitHub Actions Secrets

Go to: **repo Settings → Secrets and variables → Actions → New repository secret**

### Application secrets (shared staging + prod)

| Secret name | Value | Who provides |
|---|---|---|
| `JWT_SECRET` | Random 64-char hex string | PM / Backend lead |
| `GEMINI_API_KEY` | Google AI Studio key | PM |
| `CLAUDE_API_KEY` | Anthropic API key | PM |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | PM |
| `TELEGRAM_CHAT_ID` | Chat ID for deploy notifications | PM |

### Staging VPS secrets

| Secret name | Value |
|---|---|
| `STAGING_VPS_HOST` | IP or hostname of staging VPS |
| `STAGING_VPS_USER` | SSH user (e.g. `deploy`) |
| `STAGING_VPS_SSH_KEY` | Private key (multiline, paste full PEM) |

### Production VPS secrets

| Secret name | Value |
|---|---|
| `PROD_VPS_HOST` | IP or hostname of production VPS |
| `PROD_VPS_USER` | SSH user (e.g. `deploy`) |
| `PROD_VPS_SSH_KEY` | Private key (multiline, paste full PEM) |

**Note:** Workflows gracefully skip VPS steps if secrets are unset — safe to merge before VPS is provisioned.

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
    server_name khe.vn www.khe.vn;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name khe.vn www.khe.vn;

    # TLS — use certbot / Let's Encrypt
    ssl_certificate /etc/letsencrypt/live/khe.vn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/khe.vn/privkey.pem;

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

# Staging vhost (staging.khe.vn)
server {
    listen 443 ssl;
    server_name staging.khe.vn;

    ssl_certificate /etc/letsencrypt/live/staging.khe.vn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging.khe.vn/privkey.pem;

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
