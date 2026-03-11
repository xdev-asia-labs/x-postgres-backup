# 🐘 x-postgres-backup

![x-postgres-backup banner](banner.png)

[![CI](https://github.com/xdev-asia-labs/x-postgres-backup/actions/workflows/ci.yml/badge.svg)](https://github.com/xdev-asia-labs/x-postgres-backup/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A comprehensive backup and restore management system for PostgreSQL High Availability Clusters (Patroni) with a web dashboard, automated job scheduling, and real-time notifications.

---

## 📋 Table of Contents

- [Introduction](#-introduction)
- [Features](#-features)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Configuration](#%EF%B8%8F-configuration)
- [Usage](#-usage)
- [API Endpoints](#-api-endpoints)
- [Architecture](#-architecture)
- [Deployment](#-deployment)
- [CI/CD & Release](#-cicd--release)
- [Internationalization (i18n)](#-internationalization-i18n)
- [Troubleshooting](#-troubleshooting)
- [Monitoring & Logs](#-monitoring--logs)
- [Contributing](#-contributing)
- [License](#-license)

## 📖 Introduction

`x-postgres-backup` is an all-in-one tool for managing backups and restores on PostgreSQL HA clusters that use [Patroni](https://patroni.readthedocs.io/). It provides a user-friendly web interface, automated scheduling via cron expressions, backup integrity verification, and smart notifications through Telegram and email.

### Key Highlights

✅ **Intuitive Dashboard** — Real-time cluster monitoring, backup history, and disk usage at a glance
✅ **Backup Management** — Supports both `pg_basebackup` (physical) and `pg_dump` (logical) with automated scheduling
✅ **Restore Management** — Point-and-click restore from any backup with a visual UI
✅ **Job Scheduler** — Configure backup/cleanup/verify schedules through the web interface using cron expressions
✅ **Cluster Monitoring** — Live cluster status via the Patroni REST API
✅ **Backup Verification** — Automatic integrity checks for all stored backups
✅ **Smart Notifications** — Telegram and email alerts for backup/restore success or failure
✅ **Retention Management** — Automatic cleanup of old backups based on configurable retention policies
✅ **Multi-Language UI** — Supports English, Vietnamese, Chinese, and Japanese
✅ **Authentication & SSO** — JWT-based auth with Google and Microsoft SSO support

## 🛠️ Features

| Feature | Description |
|---------|-------------|
| **Dashboard** | Cluster status overview, backup history, disk usage monitoring |
| **Backup Management** | Run backups manually or on schedule (`pg_basebackup`, `pg_dump`) |
| **Restore Management** | Restore from any backup with a visual, intuitive interface |
| **Job Scheduler** | Configure backup/cleanup/verify schedules via cron expressions |
| **Cluster Monitoring** | Real-time cluster status from the Patroni REST API |
| **Verification** | Automatic backup integrity checks |
| **Notifications** | Telegram & email alerts on backup/restore success or failure |
| **Authentication** | JWT auth, Google SSO, Microsoft SSO, user management |
| **i18n** | Multi-language support (EN, VI, ZH, JA) |

## 🏗️ Architecture

### System Workflow

![System Workflow](docs/system_workflow.png)

<details>
<summary>📐 Mermaid Source</summary>

```mermaid
graph TB
    subgraph "PostgreSQL HA Cluster"
        P1[Patroni Node 1<br/>Leader]
        P2[Patroni Node 2<br/>Replica]
        P3[Patroni Node 3<br/>Replica]
    end

    subgraph "x-postgres-backup"
        direction TB
        WEB[Web Dashboard<br/>Jinja2 + HTMX]
        API[FastAPI REST API]
        SCHED[APScheduler<br/>Job Scheduler]
        AUTH[Auth Module<br/>JWT + SSO]

        WEB --> API
        API --> SCHED
        API --> AUTH
    end

    subgraph "Services"
        BS[Backup Service<br/>pg_basebackup / pg_dump]
        RS[Restore Service<br/>pg_restore]
        CS[Cluster Service<br/>Patroni REST Client]
        VS[Verify Service<br/>Integrity Checks]
        NS[Notification Service<br/>Telegram + Email]
    end

    subgraph "Storage"
        DB[(SQLite<br/>State & History)]
        DISK[(Backup Storage<br/>/var/backups/postgresql)]
    end

    API --> BS & RS & CS & VS
    BS --> NS
    RS --> NS
    SCHED --> BS & VS

    CS -->|REST API| P1 & P2 & P3
    BS -->|pg_basebackup| P1
    BS -->|pg_dump| P1
    RS -->|pg_restore| P1

    BS --> DISK
    RS --> DISK
    API --> DB
    SCHED --> DB
```

</details>

### Backup & Restore Workflow

![Backup & Restore Workflow](docs/backup_restore_workflow.png)

<details>
<summary>📐 Mermaid Source</summary>

```mermaid
sequenceDiagram
    actor User
    participant Web as Web Dashboard
    participant API as FastAPI
    participant Svc as Backup Service
    participant PG as PostgreSQL Leader
    participant Disk as Backup Storage
    participant Notify as Notification Service

    User->>Web: Click "Run Backup"
    Web->>API: POST /api/backups/run
    API->>Svc: Execute backup
    Svc->>PG: pg_basebackup / pg_dump
    PG-->>Svc: Data stream
    Svc->>Disk: Write compressed backup
    Svc->>API: Record result in SQLite

    alt Success
        API->>Notify: Send success alert
        Notify-->>User: 📧 Telegram / Email
    else Failure
        API->>Notify: Send failure alert
        Notify-->>User: 🚨 Telegram / Email
    end

    API-->>Web: Return status
    Web-->>User: Show result
```

</details>

### Tech Stack

- **Backend**: Python 3.11+ / FastAPI
- **Frontend**: Jinja2 + HTMX + Tailwind CSS (CDN)
- **Scheduler**: APScheduler (cron-like scheduling)
- **Database**: SQLite (local state tracking)
- **HTTP Client**: httpx (async Patroni API calls)
- **Notifications**: aiosmtplib (Email), httpx (Telegram)
- **Authentication**: JWT + OAuth2 (Google, Microsoft SSO)

### Project Structure

```
x-postgres-backup/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Environment configuration loader
│   ├── database.py          # SQLAlchemy setup + session management
│   ├── models.py            # Database models (BackupRecord, JobHistory, JobSchedule)
│   ├── scheduler.py         # APScheduler integration + job definitions
│   ├── i18n.py              # Internationalization module
│   │
│   ├── locales/             # Translation files
│   │   ├── en.json          # English (default)
│   │   ├── vi.json          # Vietnamese
│   │   ├── zh.json          # Chinese (Simplified)
│   │   └── ja.json          # Japanese
│   │
│   ├── routers/
│   │   ├── api.py           # REST API endpoints
│   │   ├── auth.py          # Authentication routes
│   │   └── dashboard.py     # HTML dashboard routes (SSR)
│   │
│   ├── services/
│   │   ├── backup.py        # pg_basebackup + pg_dump operations
│   │   ├── restore.py       # pg_restore operations
│   │   ├── cluster.py       # Patroni REST API client
│   │   ├── verify.py        # Backup integrity verification
│   │   ├── auth.py          # Authentication service
│   │   └── notification.py  # Telegram & Email notification service
│   │
│   ├── static/
│   │   └── css/
│   │       └── style.css    # Custom CSS (extends Tailwind)
│   │
│   └── templates/           # Jinja2 HTML templates
│       ├── base.html        # Base template layout (with language switcher)
│       ├── dashboard.html   # Dashboard overview
│       ├── backups.html     # Backup management
│       ├── restore.html     # Restore management
│       ├── jobs.html        # Job scheduler
│       ├── settings.html    # Settings page
│       └── login.html       # Login / Register page
│
├── data/                    # SQLite database directory (created at runtime)
├── banner.png               # Project banner image
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Docker Compose configuration
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore
├── LICENSE
└── README.md
```

## 💻 System Requirements

### Required Software

- **Python**: 3.11 or higher
- **PostgreSQL Client Tools**: `pg_basebackup`, `pg_dump`, `pg_restore`, `psql`
  - Debian/Ubuntu: `sudo apt install postgresql-client-16`
  - RHEL/CentOS: `sudo yum install postgresql16`
  - macOS: `brew install postgresql@16`
- **PostgreSQL HA Cluster**: Patroni 3.x or 4.x with etcd
- **Disk Space**: Sufficient space for backup storage (recommended ≥ 2× database size)

### Optional (for deployment)

- **Docker & Docker Compose**: For containerized deployment
- **Systemd**: For production deployment on Linux

## 🚀 Installation

### Install with Python Virtual Environment (Development)

#### Step 1: Clone the repository

```bash
git clone https://github.com/xdev-asia-labs/x-postgres-backup.git
cd x-postgres-backup
```

#### Step 2: Create and activate a virtual environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

#### Step 3: Install dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install -r requirements.txt
```

#### Step 4: Create configuration files

```bash
# Copy example config
cp .env.example .env

# Create data directory for SQLite
mkdir -p data

# Create backup directory (customize as needed)
mkdir -p /var/backups/postgresql
```

#### Step 5: Configure connections

Open `.env` and update the following settings:

```bash
# Patroni connection
PATRONI_NODES=10.10.10.11:8008,10.10.10.12:8008,10.10.10.13:8008

# PostgreSQL connection
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=your_postgres_password
PG_BIN_DIR=/usr/lib/postgresql/16/bin  # Path to PostgreSQL binaries

# Replication user for pg_basebackup
PG_REPLICATION_USER=replicator
PG_REPLICATION_PASSWORD=your_replicator_password

# Backup directory
BACKUP_DIR=/var/backups/postgresql
```

#### Step 6: Start the application

```bash
# Development mode with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Step 7: Access the dashboard

Open your browser and navigate to:

```
http://localhost:8000
```

### Install with Docker Compose (Production)

```bash
# 1. Clone repository
git clone https://github.com/xdev-asia-labs/x-postgres-backup.git
cd x-postgres-backup

# 2. Configure
cp .env.example .env
nano .env  # Edit configuration

# 3. Start container
docker compose up -d

# 4. Check logs
docker compose logs -f

# 5. Access dashboard
open http://localhost:8000
```

## ⚙️ Configuration

All configuration is done via environment variables in the `.env` file.

### Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | x-postgres-backup | Application name |
| `APP_HOST` | 0.0.0.0 | Listen address |
| `APP_PORT` | 8000 | Listen port |
| `APP_LOG_LEVEL` | info | Log level (debug, info, warning, error) |
| `APP_SECRET_KEY` | *(auto-generated)* | Secret key for sessions (must change in production) |

### Cluster Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PATRONI_NODES` | 10.10.10.11:8008 | Comma-separated Patroni REST API endpoints |
| `PATRONI_AUTH_ENABLED` | false | Enable authentication for Patroni API |
| `PATRONI_AUTH_USERNAME` | | Patroni API username |
| `PATRONI_AUTH_PASSWORD` | | Patroni API password |

### PostgreSQL Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PG_PORT` | 5432 | PostgreSQL port |
| `PG_USER` | postgres | PostgreSQL superuser |
| `PG_PASSWORD` | | PostgreSQL password |
| `PG_BIN_DIR` | /usr/lib/postgresql/18/bin | Path to PostgreSQL binaries |
| `PG_REPLICATION_USER` | replicator | User for pg_basebackup |
| `PG_REPLICATION_PASSWORD` | | Replication user password |

### Backup Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKUP_DIR` | /var/backups/postgresql | Backup storage directory |
| `BACKUP_RETENTION_DAYS` | 7 | Number of days to retain backups |
| `BACKUP_RETENTION_COPIES` | 7 | Minimum number of backup copies to keep |
| `BACKUP_COMPRESSION` | gzip | Compression method (gzip, lz4, zstd) |

### Scheduler Settings (Cron)

| Variable | Default | Description |
|----------|---------|-------------|
| `SCHEDULE_BASEBACKUP` | 0 2 ** * | pg_basebackup schedule (daily at 2:00 AM) |
| `SCHEDULE_PGDUMP` | 0 3 ** * | pg_dump schedule (daily at 3:00 AM) |
| `SCHEDULE_VERIFY` | 0 4 ** * | Backup verification schedule (daily at 4:00 AM) |
| `SCHEDULE_CLEANUP` | 0 6 ** * | Old backup cleanup schedule (daily at 6:00 AM) |

**Cron format**: `minute hour day month day_of_week`

Examples:

- `0 2 * * *` — 2:00 AM every day
- `0 */6 * * *` — Every 6 hours
- `0 0 * * 0` — 12:00 AM every Sunday
- `30 3 * * 1-5` — 3:30 AM Monday through Friday

### Notification Settings

#### Telegram

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_ENABLED` | false | Enable/disable Telegram notifications |
| `TELEGRAM_BOT_TOKEN` | | Telegram Bot token |
| `TELEGRAM_CHAT_ID` | | Chat ID for notifications |

##### How to create a Telegram Bot

1. **Create a new bot**: Open Telegram and find [@BotFather](https://t.me/BotFather). Send `/newbot`, set a name and username, and save the **Bot Token**.
2. **Get your Chat ID**: Send a message to your bot, then visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` and find `"chat":{"id":123456789}`.
3. **Update `.env`**:

   ```bash
   TELEGRAM_ENABLED=true
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   TELEGRAM_CHAT_ID=123456789
   ```

#### Email

| Variable | Default | Description |
|----------|---------|-------------|
| `EMAIL_ENABLED` | false | Enable/disable email notifications |
| `EMAIL_SMTP_HOST` | smtp.gmail.com | SMTP server hostname |
| `EMAIL_SMTP_PORT` | 587 | SMTP server port |
| `EMAIL_SMTP_USER` | | SMTP username/email |
| `EMAIL_SMTP_PASSWORD` | | SMTP password (App Password for Gmail) |
| `EMAIL_FROM` | | Sender email address |
| `EMAIL_TO` | | Comma-separated recipient email addresses |
| `EMAIL_USE_TLS` | true | Use TLS/STARTTLS |

##### Gmail setup

1. **Create an App Password**: Go to [Google Account Security](https://myaccount.google.com/security), enable **2-Step Verification**, then go to [App Passwords](https://myaccount.google.com/apppasswords) and generate a 16-character password.
2. **Update `.env`**:

   ```bash
   EMAIL_ENABLED=true
   EMAIL_SMTP_HOST=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   EMAIL_SMTP_USER=your_email@gmail.com
   EMAIL_SMTP_PASSWORD=xxxx xxxx xxxx xxxx
   EMAIL_FROM=your_email@gmail.com
   EMAIL_TO=admin1@example.com,admin2@example.com
   EMAIL_USE_TLS=true
   ```

##### Other SMTP providers

**Office 365 / Outlook:**

```bash
EMAIL_SMTP_HOST=smtp.office365.com
EMAIL_SMTP_PORT=587
EMAIL_USE_TLS=true
```

**Yahoo Mail:**

```bash
EMAIL_SMTP_HOST=smtp.mail.yahoo.com
EMAIL_SMTP_PORT=587
EMAIL_USE_TLS=true
```

### Authentication & Authorization

#### Enable/Disable Authentication

```bash
# Enable authentication (default)
AUTH_ENABLED=true

# Disable authentication (no login required — development only)
AUTH_ENABLED=false
```

#### JWT & Session Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | *(auto-generated)* | Secret key for JWT tokens (MUST change in production) |
| `JWT_ALGORITHM` | HS256 | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 1440 | Access token expiry (24 hours) |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | 30 | Refresh token expiry (30 days) |
| `SESSION_SECRET_KEY` | *(auto-generated)* | Secret key for session cookie |
| `SESSION_COOKIE_NAME` | xpb_session | Session cookie name |
| `SESSION_MAX_AGE` | 86400 | Session lifetime in seconds (24 hours) |

#### Default Admin Account

On first startup, the system automatically creates an admin account:

```bash
DEFAULT_ADMIN_EMAIL=admin@localhost
DEFAULT_ADMIN_PASSWORD=admin
```

> ⚠️ **IMPORTANT**: Change the password immediately after the first login!

#### Single Sign-On (SSO) — Google

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Credentials** → **Create OAuth 2.0 Client ID**
2. Add Authorized redirect URIs: `http://localhost:8000/auth/google/callback` (dev) or `https://yourdomain.com/auth/google/callback` (production)
3. Update `.env`:

   ```bash
   GOOGLE_CLIENT_ID=123456789-abc123xyz.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-abc123xyz789
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
   ```

#### Single Sign-On (SSO) — Microsoft

1. Go to [Azure Portal](https://portal.azure.com/) → **Azure Active Directory** → **App registrations** → **New registration**
2. Add Redirect URI: `http://localhost:8000/auth/microsoft/callback`
3. Under **Certificates & secrets**, create a new client secret
4. Update `.env`:

   ```bash
   MICROSOFT_CLIENT_ID=12345678-1234-1234-1234-123456789abc
   MICROSOFT_CLIENT_SECRET=abc123~xyz789.def456
   MICROSOFT_TENANT_ID=common
   MICROSOFT_REDIRECT_URI=http://localhost:8000/auth/microsoft/callback
   ```

**Tenant ID options:**

- `common` — All Microsoft accounts (personal + organizational)
- `organizations` — Organizational accounts only
- `consumers` — Personal Microsoft accounts only
- `{tenant-id}` — A specific organization only

#### API Authentication

**Using Bearer Token (JWT):**

```bash
# Get access token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@localhost","password":"admin"}'

# Use token in API requests
curl http://localhost:8000/api/backups \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."

# Refresh token
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"eyJ0eXAiOiJKV1QiLCJhbGc..."}'
```

## 📖 Usage

### Login

1. Navigate to `http://localhost:8000/login`
2. Sign in with the default credentials: `admin@localhost` / `admin`
3. Alternatively, use **Google** or **Microsoft** SSO buttons
4. If registration is enabled (`ALLOW_REGISTRATION=true`), click **Sign up** to create a new account

### Dashboard Overview

After logging in, the main dashboard displays:

- **Cluster Status**: Shows node states (Leader, Replica, lag)
- **Recent Backups**: Latest backup records with status
- **Disk Usage**: Storage consumption monitoring
- **Quick Actions**: One-click backup shortcuts

### Backup Management

#### Run a manual backup

1. Navigate to the **Backups** tab
2. Choose backup type:
   - **Base Backup** (`pg_basebackup`): Full physical backup
   - **Logical Backup** (`pg_dump`): Per-database logical backup
3. Select a database (for pg_dump)
4. Click **Run Backup**

#### View backup history

The **Backups** tab displays all past backups with timestamp, size, status, and duration. Filter by backup type, database, or status.

### Restore Database

#### Restore from pg_dump

1. Navigate to the **Restore** tab
2. Select a dump file from the list
3. Enter the target database name
4. Choose options:
   - **Drop existing**: Drop old database before restore
   - **Target host**: Node to restore to (default: Leader)
5. Click **Start Restore**

#### Restore from pg_basebackup

Base backups restore the entire cluster and must be performed manually on the server:

```bash
# Stop PostgreSQL
systemctl stop postgresql

# Restore data directory
rm -rf /var/lib/postgresql/16/main/*
tar -xzf /var/backups/postgresql/basebackup_2024-01-15_020000/base.tar.gz \
    -C /var/lib/postgresql/16/main/

# Set permissions
chown -R postgres:postgres /var/lib/postgresql/16/main

# Start PostgreSQL
systemctl start postgresql
```

### Job Scheduler

1. Navigate to the **Jobs** tab
2. View and edit scheduled jobs with their cron expressions
3. Toggle jobs on/off with the enable switch
4. Run any job immediately with the **Run Now** button

## 🔌 API Endpoints

### Web UI Routes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard overview |
| `/login` | GET | Login page |
| `/backups` | GET | Backup management page |
| `/restore` | GET | Restore management page |
| `/jobs` | GET | Job scheduler page |
| `/settings` | GET | Configuration page |
| `/set-language/{lang}` | GET | Switch UI language (en, vi, zh, ja) |

### Authentication APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Register a new account |
| `/auth/login` | POST | Sign in with email/password |
| `/auth/logout` | POST | Sign out |
| `/auth/refresh` | POST | Refresh access token |
| `/auth/me` | GET | Current user info |
| `/auth/google/login` | GET | Google SSO login |
| `/auth/google/callback` | GET | Google OAuth callback |
| `/auth/microsoft/login` | GET | Microsoft SSO login |
| `/auth/microsoft/callback` | GET | Microsoft OAuth callback |
| `/auth/users` | GET | List users (admin only) |
| `/auth/users/{id}` | DELETE | Delete user (admin only) |

### Cluster APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cluster/status` | GET | Cluster status from Patroni |
| `/api/cluster/databases` | GET | List databases |

### Backup APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/backups` | GET | List backup records |
| `/api/backups/run` | POST | Run a new backup |
| `/api/backups/disk` | GET | List on-disk backups |
| `/api/verify` | GET | Verify all backups |

**Example — Run pg_dump:**

```bash
curl -X POST http://localhost:8000/api/backups/run \
  -H "Content-Type: application/json" \
  -d '{"backup_type": "pgdump", "database": "mydb"}'
```

**Example — Run pg_basebackup:**

```bash
curl -X POST http://localhost:8000/api/backups/run \
  -H "Content-Type: application/json" \
  -d '{"backup_type": "basebackup"}'
```

### Restore APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/restore/available` | GET | List restorable backups |
| `/api/restore/run` | POST | Run a restore operation |

**Example — Restore database:**

```bash
curl -X POST http://localhost:8000/api/restore/run \
  -H "Content-Type: application/json" \
  -d '{
    "dump_file": "/var/backups/postgresql/pg_dump/2024-01-15_030000/mydb_backup.dump",
    "target_database": "mydb_restored",
    "drop_existing": false
  }'
```

### Job APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs/schedules` | GET | List job schedules |
| `/api/jobs/schedules/{id}` | PUT | Update a job schedule |
| `/api/jobs/run/{name}` | POST | Run a job manually |
| `/api/jobs/history` | GET | Job execution history |

### Disk APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/disk` | GET | Disk usage information |
| `/api/cleanup` | POST | Remove old backups per retention policy |

## 🚢 Deployment

### Ansible Deployment (Recommended for Production)

An Ansible role is provided in `deploy/ansible/` for automated deployment.

```bash
# Copy role to your Ansible project
cp -r deploy/ansible/ /path/to/your/ansible/roles/x-postgres-backup/
```

Example playbook:

```yaml
---
- name: Deploy x-postgres-backup
  hosts: backup_servers
  become: yes
  roles:
    - role: x-postgres-backup
      vars:
        app_version: "latest"
        patroni_nodes: "10.10.10.11:8008,10.10.10.12:8008,10.10.10.13:8008"
        pg_password: "{{ vault_pg_password }}"
        pg_replication_password: "{{ vault_pg_replication_password }}"
        backup_dir: "/var/backups/postgresql"
        telegram_enabled: true
        telegram_bot_token: "{{ vault_telegram_bot_token }}"
        telegram_chat_id: "{{ vault_telegram_chat_id }}"
```

```bash
ansible-playbook -i inventory/production.yml playbooks/deploy-backup.yml
```

### Systemd Service (Linux Production)

```bash
# Copy service file
sudo cp deploy/systemd/x-postgres-backup.service /etc/systemd/system/

# Reload, enable, and start
sudo systemctl daemon-reload
sudo systemctl enable x-postgres-backup
sudo systemctl start x-postgres-backup

# Check status
sudo systemctl status x-postgres-backup

# View logs
sudo journalctl -u x-postgres-backup -f
```

### Docker Compose

```bash
git clone https://github.com/xdev-asia-labs/x-postgres-backup.git
cd x-postgres-backup
cp .env.example .env
nano .env

docker compose up -d
docker compose logs -f
```

### Docker Standalone

```bash
# Build image
docker build -t x-postgres-backup:latest .

# Run container
docker run -d \
  --name x-postgres-backup \
  -p 8000:8000 \
  -v /var/backups/postgresql:/var/backups/postgresql \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  x-postgres-backup:latest

docker logs -f x-postgres-backup
```

## 🔄 CI/CD & Release

### GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **CI** | Push/PR → `main` | Lint (Ruff), test, build Docker image |
| **Build & Push** | Push → `main`, tag `v*` | Build multi-arch (amd64/arm64) and push to Docker Hub + GHCR |
| **Release** | Push → `main` | Automatic semantic versioning, GitHub Release, push release image |

### Semantic Versioning

Versions are created automatically based on [Conventional Commits](https://www.conventionalcommits.org/):

| Commit prefix | Release type | Example |
|---------------|-------------|---------|
| `feat:` | Minor (0.**1**.0) | `feat: add SSO login` |
| `fix:` | Patch (0.0.**1**) | `fix: bcrypt compatibility` |
| `perf:` | Patch | `perf: optimize backup query` |
| `feat!:` or `BREAKING CHANGE:` | Major (**1**.0.0) | `feat!: new API schema` |

Commits with `docs:`, `style:`, `chore:`, `ci:`, `test:` do **not** trigger a new release.

### Secrets Configuration

Add to **Settings → Secrets and variables → Actions** in the GitHub repository:

| Secret/Variable | Type | Description |
|-----------------|------|-------------|
| `DOCKERHUB_TOKEN` | Secret | Docker Hub Access Token |
| `DOCKERHUB_USERNAME` | Variable | Docker Hub username |

> `GITHUB_TOKEN` is automatically provided by GitHub Actions — no configuration needed.

### Docker Images

After pushing to `main`, images are published at:

```bash
# Docker Hub
docker pull <dockerhub-username>/x-postgres-backup:latest
docker pull <dockerhub-username>/x-postgres-backup:1.2.3

# GitHub Container Registry
docker pull ghcr.io/xdev-asia-labs/x-postgres-backup:latest
docker pull ghcr.io/xdev-asia-labs/x-postgres-backup:1.2.3
```

## 🌐 Internationalization (i18n)

The web dashboard supports **4 languages**:

| Code | Language |
|------|----------|
| `en` | English (default) |
| `vi` | Tiếng Việt (Vietnamese) |
| `zh` | 中文 (Chinese Simplified) |
| `ja` | 日本語 (Japanese) |

### How it works

- Language preference is stored in a cookie (`xpb_lang`) that persists for 1 year
- Switch languages using the **🌐 Language** dropdown in the navigation bar or on the login page
- All UI text is loaded from JSON translation files in `app/locales/`
- The default language is English

### Adding a new language

1. Create a new JSON file in `app/locales/` (e.g., `ko.json` for Korean)
2. Copy the structure from `en.json` and translate all values
3. Add the language code to `SUPPORTED_LANGUAGES` and `LANGUAGE_NAMES` in `app/i18n.py`

## 🐛 Troubleshooting

### Server won't start

**Error: `ModuleNotFoundError: No module named 'app'`**

```bash
# Make sure you're in the project root directory
cd /path/to/x-postgres-backup

# And the virtual environment is activated
source venv/bin/activate
```

**Error: `Permission denied` when creating backups**

```bash
# Check backup directory permissions
ls -la /var/backups/postgresql

# Grant permissions to the service user
sudo chown -R $USER:$USER /var/backups/postgresql
sudo chmod -R 755 /var/backups/postgresql
```

### Cannot connect to Patroni

**Error: `No cluster leader found`**

1. Check that Patroni nodes are running:

   ```bash
   curl http://10.10.10.11:8008/patroni
   ```

2. Verify `PATRONI_NODES` in `.env`
3. If Patroni uses authentication, enable it:

   ```bash
   PATRONI_AUTH_ENABLED=true
   PATRONI_AUTH_USERNAME=your_username
   PATRONI_AUTH_PASSWORD=your_password
   ```

### pg_basebackup fails

**Error: `FATAL: no pg_hba.conf entry for replication`**

Add a replication entry in `pg_hba.conf`:

```
host    replication    replicator    <backup_server_ip>/32    md5
```

Then reload: `sudo systemctl reload postgresql`

**Error: `pg_basebackup: command not found`**

```bash
# Install PostgreSQL client tools:
# Ubuntu/Debian:
sudo apt install postgresql-client-16
# RHEL/CentOS:
sudo yum install postgresql16

# Update PG_BIN_DIR in .env
PG_BIN_DIR=/usr/bin
```

### Notifications not working

**Telegram not receiving alerts:**

```bash
# Verify bot token
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"

# Test sending a message
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage" \
  -d "chat_id=<YOUR_CHAT_ID>&text=Test message"
```

**Email not sending:**

1. Test SMTP connection: `telnet smtp.gmail.com 587`
2. For Gmail: ensure 2-Step Verification is enabled and you're using an App Password
3. Check logs: `docker compose logs -f | grep -i "email\|smtp"`

### SQLite database locked

```bash
sudo systemctl stop x-postgres-backup
rm -f data/backup_manager.db-wal data/backup_manager.db-shm
sudo systemctl start x-postgres-backup
```

### Disk full from backups

```bash
# Check disk usage
df -h /var/backups/postgresql

# Run cleanup manually
curl -X POST http://localhost:8000/api/cleanup

# Or delete old backups manually
find /var/backups/postgresql -type f -mtime +7 -delete
```

## 📊 Monitoring & Logs

### Viewing Logs

**Development (venv):**

```bash
uvicorn app.main:app --log-config logging.yaml > logs/app.log 2>&1
```

**Docker:**

```bash
docker compose logs -f
docker compose logs -f x-postgres-backup
docker compose logs | grep -i "error\|backup"
```

**Systemd:**

```bash
sudo journalctl -u x-postgres-backup -f
sudo journalctl -u x-postgres-backup --since "2024-01-15 10:00:00"
sudo journalctl -u x-postgres-backup -p err
```

### Integration with Monitoring Tools

- **Prometheus**: Expose metrics endpoint at `/metrics` (extensible)
- **Grafana**: Import dashboard templates to visualize backup trends, success rates, and duration
- **Nagios/Icinga**: Check API endpoint health and alert on backup failures

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'feat: add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

MIT License — see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Repository**: <https://github.com/xdev-asia-labs/x-postgres-backup>
- **Issues**: <https://github.com/xdev-asia-labs/x-postgres-backup/issues>
- **Patroni Documentation**: <https://patroni.readthedocs.io/>
- **PostgreSQL Documentation**: <https://www.postgresql.org/docs/>

## ✨ Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) — Modern web framework
- [HTMX](https://htmx.org/) — High power tools for HTML
- [Tailwind CSS](https://tailwindcss.com/) — Utility-first CSS framework
- [Patroni](https://github.com/patroni/patroni) — PostgreSQL HA solution

---

Made with ❤️ by [xdev.asia](https://xdev.asia)
