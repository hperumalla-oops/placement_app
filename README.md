# Placement Portal Backend

FastAPI + PostgreSQL (Supabase) backend for the college placement portal. MVP-1 scope only — see spec section 39 for explicitly deferred features.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # then fill in real values
```

Required environment variables (see `.env.example`): Supabase URL/anon key, JWT JWKS URL + key id, `DATABASE_URL` (asyncpg format), plus `ENVIRONMENT`, `LOG_LEVEL`, `CORS_ORIGINS`.

## Run locally

```bash
uvicorn app.main:app --reload
```

- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## Tests

```bash
pytest tests/unit -v
```

Integration tests (`tests/integration/`) require a running database and are not yet implemented — see Known Gaps below.

## Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

The database schema already exists in Supabase; only run migrations for future schema changes, not to (re)create the current schema.

## Architecture

Modular monolith, layered by responsibility: