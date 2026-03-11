# Development Guide

## Quick Setup

```bash
# 1. Clone repo
git clone <repo-url>
cd x-postgres-backup

# 2. Install dependencies
make install

# 3. Setup git hooks (runs tests before push)
make setup-hooks

# 4. Start PostgreSQL (optional, for integration tests)
make db-up

# 5. Run app in dev mode (hot reload)
make dev
```

App will be available at: **http://127.0.0.1:8001**

## Development Workflow

### Running Tests

```bash
# Run all tests with coverage
make test

# Run tests fast (no coverage, stop on first failure)
make test-fast

# Run specific test file
.venv/bin/pytest tests/test_auth.py -v

# Run specific test
.venv/bin/pytest tests/test_auth.py::test_login_success -v
```

### Code Quality

```bash
# Lint code (check only)
make lint

# Auto-fix and format code
make format

# Manual pre-commit run
.venv/bin/pre-commit run --all-files
```

### Git Workflow

Pre-commit hooks are configured to run automatically:
- **Before commit**: lint + format
- **Before push**: run fast tests

To skip hooks (not recommended):
```bash
git push --no-verify
```

### Database

```bash
# Start PostgreSQL for dev
make db-up

# Stop PostgreSQL
make db-down

# Connect to postgres
docker exec -it xpb-postgres-dev psql -U xpb -d xpb
```

## Project Structure

```
x-postgres-backup/
├── app/
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Settings & env vars
│   ├── database.py       # SQLAlchemy setup
│   ├── models.py         # Database models
│   ├── scheduler.py      # APScheduler jobs
│   ├── routers/          # API endpoints
│   │   ├── api.py        # Backup/restore APIs
│   │   ├── auth.py       # Authentication
│   │   └── dashboard.py  # Web UI
│   ├── services/         # Business logic
│   │   ├── backup.py
│   │   ├── restore.py
│   │   ├── cluster.py
│   │   └── auth.py
│   ├── templates/        # Jinja2 HTML templates
│   ├── static/           # CSS/JS assets
│   └── locales/          # i18n translations
├── tests/
│   ├── conftest.py       # Pytest fixtures
│   ├── test_api.py
│   ├── test_auth.py
│   └── test_schedules.py
├── docker-compose.yml        # Production setup
├── docker-compose.dev.yml    # Dev setup (postgres only)
├── Makefile                  # Dev commands
└── .env                      # Local config (gitignored)
```

## Environment Variables

Copy `.env.example` to `.env` and customize for local dev:

```bash
cp .env.example .env
```

Key settings for dev:
- `DATABASE_URL=sqlite:///data/backup_manager.db` (no external DB needed)
- `APP_PORT=8001` (avoid conflict with Docker on 8000)
- `AUTH_ENABLED=true`

## CI/CD

GitHub Actions runs automatically on push/PR:
- Linting with Ruff
- Tests with pytest + coverage
- Docker build test

See: `.github/workflows/ci.yml`

## Common Tasks

### Add a new endpoint

1. Add route in `app/routers/api.py` or `app/routers/auth.py`
2. Add business logic in `app/services/`
3. Write tests in `tests/`
4. Run tests: `make test`

### Add a database model

1. Define model in `app/models.py`
2. The tables will be created automatically on startup
3. For production, consider using Alembic migrations

### Add a scheduled job

1. Define job function in `app/scheduler.py`
2. Add to `JOB_MAP`
3. Add default schedule in `init_default_schedules()`

## Troubleshooting

### Port 8001 already in use
```bash
# Find process
lsof -i :8001

# Kill it or change APP_PORT in .env
```

### Tests fail with DB errors
```bash
# Delete test DB and retry
rm -f data/backup_manager.db
make test
```

### Pre-commit hooks not working
```bash
make setup-hooks
```

### Docker container won't start
```bash
# Check logs
docker logs xpb-postgres-dev

# Rebuild from scratch
make db-down
docker volume rm x-postgres-backup_pg-dev-data
make db-up
```
