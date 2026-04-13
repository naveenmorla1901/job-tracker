# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Start API server (port 8001)
python run.py api

# Start Streamlit dashboard (port 8501)
python run.py dashboard

# Database management
python run.py reset_db       # DESTRUCTIVE: wipes all data
python run.py update_db      # Run schema migrations
python run.py purge          # Delete records older than 7 days
python run.py cleanup        # Remove duplicates and fix issues

# Utilities
python run.py create_admin EMAIL PASSWORD
python run.py free           # Free port 8000 if occupied

# Run tests
pytest                        # All tests
pytest tests/test_api.py     # Single file
pytest -m api                # By marker (api, scrapers, integration, unit)
pytest -m "not api"          # Exclude marker

# Alembic migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

**Environment**: copy `.env` with `DATABASE_URL=postgresql://postgres:1901@localhost/job_tracker`. Tests use `ENVIRONMENT=test` and SQLite by default (`DATABASE_URL` in `pytest.ini`).

## Architecture

Four main layers:

### 1. FastAPI Backend (`main.py`, `app/api/`)
- Entry point: `main.py` — registers routers, CORS, rate limiter, startup scheduler
- Routers: `app/api/endpoints/jobs.py`, `stats.py`, `health.py`, `auth/routes.py`, `user_jobs.py`
- Middleware: `app/api/middleware/rate_limiter.py` (5 req/min auth, 60 req/min general)
- Auth: JWT via `python-jose`, bcrypt passwords in `app/auth/`

### 2. Streamlit Dashboard (`dashboard.py`, `dashboard_components/`)
- Entry: `dashboard.py` — page routing via `st.sidebar`
- Pages: `dashboard_components/jobs_page.py` (all jobs), `ai_jobs_page.py` (DS/ML filtered), `app/dashboard/logs.py`, `app/dashboard/admin.py`
- Connects to API at `JOB_TRACKER_API_URL` env var (defaults to `http://localhost:8001/api`)

### 3. Scrapers (`app/scrapers/`)
- **150+ scrapers**, one file per company (e.g. `app/scrapers/salesforce.py`)
- Each exposes `get_{company}_jobs(roles, days)` returning `Dict[role_name, List[job_dict]]`
- `BaseScraper` in `app/scrapers/base.py` provides helpers; scrapers mostly use `requests`/`aiohttp` directly against company career APIs
- `app/scrapers/__init__.py` exports `get_all_scrapers()` — discovers scrapers by listing the module

### 4. Scheduler (`app/scheduler/jobs.py`)
- Uses APScheduler `BackgroundScheduler`
- Runs all scrapers hourly 9–19 via `run_all_scrapers()` → `run_scraper(name)`
- `run_scraper` dynamically imports `app.scrapers.{name}` and calls `get_{name}_jobs()`
- `COMPANY_NAMES` dict maps module name → display name used when writing to DB

### Database (`app/db/`)
- SQLAlchemy ORM; PostgreSQL in prod, SQLite in tests
- Models: `Job`, `Role`, `ScraperRun`, `User`, `UserJob` (all in `app/db/models.py`)
- `Job` deduplicated on `(job_id, company)` unique constraint
- `app/db/crud.py`: `upsert_jobs()`, `mark_inactive_jobs()` — core write path
- Alembic handles schema migrations; `python run.py update_db` wraps it

## Adding a New Scraper

1. Create `app/scrapers/{company}.py` with function `get_{company}_jobs(roles, days) -> Dict[str, List[dict]]`
2. Each job dict needs at minimum: `job_id`, `job_title`, `job_url`, `location`, `date_posted`
3. Add company to `COMPANY_NAMES` in `app/scheduler/jobs.py`
4. The scheduler auto-discovers it via `get_all_scrapers()` — no registration needed

## Key Config

- `app/config.py`: reads `.env`, sets `SQLALCHEMY_DATABASE_URL`, `ENVIRONMENT`
- `ENVIRONMENT=test` skips DB init and scheduler startup in `main.py`
- API always binds port **8001** (not 8000); dashboard binds **8501**
