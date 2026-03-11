# CI/CD & Testing Setup

## Changes Made

### 1. CI/CD Pipeline

**GitHub Actions** (`.github/workflows/ci.yml`):
- ✅ Auto-run tests on every push/PR
- ✅ Code linting with Ruff
- ✅ Coverage reporting
- ✅ Docker build verification

### 2. Pre-commit Hooks

Automatically run before commits and pushes:
- Format code (ruff)
- Fix common issues
- Run fast tests before push

**Setup**:
```bash
make setup-hooks
```

**Bypass** (not recommended):
```bash
git push --no-verify
```

### 3. Development Workflow

```bash
# Initial setup
make install
make setup-hooks

# Daily development
make dev              # Start app with hot reload (port 8001)
make test             # Run full test suite with coverage
make test-fast        # Quick test (no coverage, stop on failure)
make format           # Auto-format code
make lint             # Check code quality

# Database (optional)
make db-up            # Start postgres in Docker
make db-down          # Stop postgres
```

### 4. Test Suite

**20 automated tests** covering:
- ✅ API endpoints (backup, restore, cluster)
- ✅ Authentication & JWT
- ✅ Job scheduling
- ✅ Permission checks

**Test isolation**: Each test gets a fresh in-memory SQLite DB.

### 5. What Gets Checked

**On every commit**:
- Trailing whitespace removed
- Files end with newline
- No large files (>2MB)
- Valid JSON/YAML
- Code formatting (ruff)

**Before push**:
- Fast test suite (20 tests)

**On GitHub CI**:
- Full test suite with coverage
- Docker build
- Code linting

## Files Added

```
.pre-commit-config.yaml    # Pre-commit hooks config
DEVELOPMENT.md             # Dev documentation
Makefile                   # Dev shortcuts
docker-compose.dev.yml     # Postgres-only for dev
requirements-dev.txt       # Dev dependencies
pytest.ini                 # Pytest config
scripts/setup-dev.sh       # Setup script
tests/
  conftest.py              # Test fixtures
  test_api.py              # API tests
  test_auth.py             # Auth tests
  test_schedules.py        # Schedule tests
```

## Files Modified

- `.github/workflows/ci.yml` - Updated with pytest-cov
- `app/database.py` - SQLite compatibility fix
- `app/services/auth.py` - Added `jti` to JWT (prevent duplicates)
- `.gitignore` - Added test/coverage artifacts
- `README.md` - Added CI badges

## Example Workflow

```bash
# 1. Make changes
vim app/routers/api.py

# 2. Run tests locally
make test-fast

# 3. Commit (hooks auto-format)
git add .
git commit -m "Add new endpoint"
# → Pre-commit runs: format, lint

# 4. Push (hooks auto-test)
git push
# → Pre-push runs: fast tests
# → GitHub Actions runs: full CI

# 5. Create PR
# → CI runs on PR
# → Shows status badge
```

## Benefits

1. **Catch bugs early** - Tests run locally before push
2. **Consistent style** - Auto-formatting
3. **Fast feedback** - Pre-push hooks are fast (<15s)
4. **CI confidence** - Know if PR will pass before pushing
5. **Documentation** - Coverage reports show what's tested

## Next Steps

Optional improvements:
- [ ] Add code coverage badges (Codecov)
- [ ] Add integration tests with real postgres
- [ ] Add load/performance tests
- [ ] Setup pre-commit.ci for PRs
- [ ] Add mutation testing
