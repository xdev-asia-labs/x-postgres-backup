# x-postgres-backup

Web dashboard + job scheduler cho backup/restore PostgreSQL HA Cluster (Patroni).

## Tính năng

- **Dashboard**: Tổng quan trạng thái cluster, backup history, disk usage
- **Backup Management**: Chạy backup thủ công hoặc theo lịch (pg_basebackup, pg_dump)
- **Restore Management**: Restore từ backup với UI trực quan
- **Job Scheduler**: Cấu hình lịch backup/cleanup/verify qua web
- **Cluster Monitoring**: Realtime cluster status từ Patroni REST API
- **Verification**: Tự động kiểm tra tính toàn vẹn backup

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI
- **Frontend**: Jinja2 + HTMX + Tailwind CSS (CDN)
- **Scheduler**: APScheduler
- **Database**: SQLite (local state tracking)
- **Container**: Docker / Docker Compose

## Quick Start

```bash
# 1. Clone & configure
git clone https://github.com/xdev-asia-labs/x-postgres-backup.git
cd x-postgres-backup
cp .env.example .env
# Edit .env with your cluster details

# 2. Docker Compose
docker compose up -d

# 3. Open dashboard
open http://localhost:8000
```

## Development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Ansible Deployment

An Ansible role is included in `deploy/ansible/` for automated deployment to your backup server. Copy it into your Ansible project:

```bash
# Copy role to your Ansible project
cp -r deploy/ansible/ /path/to/ansible/roles/x-postgres-backup/

# Run deployment
ansible-playbook playbooks/site.yml --tags "backup-manager"
```

## Configuration

All configuration via environment variables. See [.env.example](.env.example).

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | x-postgres-backup | Application name |
| `APP_HOST` | 0.0.0.0 | Listen address |
| `APP_PORT` | 8000 | Listen port |
| `PATRONI_NODES` | 10.10.10.11:8008 | Patroni endpoints (comma-separated) |
| `PG_PORT` | 5432 | PostgreSQL port |
| `PG_USER` | postgres | PostgreSQL superuser |
| `PG_PASSWORD` | | PostgreSQL password |
| `PG_BIN_DIR` | /usr/lib/postgresql/18/bin | PostgreSQL binaries path |
| `BACKUP_DIR` | /var/backups/postgresql | Backup storage directory |
| `BACKUP_RETENTION_DAYS` | 7 | Days to keep backups |
| `BACKUP_RETENTION_COPIES` | 7 | Minimum copies to keep |
| `SCHEDULE_BASEBACKUP` | 0 2 ** * | Cron schedule for pg_basebackup |
| `SCHEDULE_PGDUMP` | 0 3 ** * | Cron schedule for pg_dump |
| `SCHEDULE_VERIFY` | 0 4 ** * | Cron schedule for verification |
| `SCHEDULE_CLEANUP` | 0 6 ** * | Cron schedule for cleanup |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard overview |
| `/backups` | GET | Backup management page |
| `/restore` | GET | Restore management page |
| `/jobs` | GET | Job schedules & history |
| `/settings` | GET | App settings view |
| `/api/cluster/status` | GET | Cluster status (JSON) |
| `/api/cluster/databases` | GET | Database list |
| `/api/backups` | GET | Backup records |
| `/api/backups/run` | POST | Trigger backup |
| `/api/backups/disk` | GET | On-disk backups |
| `/api/restore/available` | GET | Available restore points |
| `/api/restore/run` | POST | Run restore |
| `/api/verify` | GET | Verify all backups |
| `/api/disk` | GET | Disk usage |
| `/api/cleanup` | POST | Remove old backups |
| `/api/jobs/schedules` | GET | List schedules |
| `/api/jobs/schedules/{id}` | PUT | Update schedule |
| `/api/jobs/run/{name}` | POST | Run job manually |
| `/api/jobs/history` | GET | Job execution history |

## Architecture

```
x-postgres-backup
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py             # Environment configuration
│   ├── database.py           # SQLAlchemy + SQLite
│   ├── models.py             # BackupRecord, JobHistory, JobSchedule
│   ├── scheduler.py          # APScheduler cron integration
│   ├── routers/
│   │   ├── api.py            # REST API endpoints
│   │   └── dashboard.py      # HTML dashboard routes
│   ├── services/
│   │   ├── backup.py         # pg_basebackup + pg_dump
│   │   ├── restore.py        # pg_restore operations
│   │   ├── cluster.py        # Patroni REST API client
│   │   └── verify.py         # Backup integrity checks
│   └── templates/            # Jinja2 + Tailwind + HTMX
├── deploy/
│   ├── ansible/              # Ansible role for deployment
│   └── systemd/              # Systemd service file
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Compatible With

- PostgreSQL 16+ / 18+
- Patroni 3.x / 4.x
- etcd 3.5.x

## License

MIT
