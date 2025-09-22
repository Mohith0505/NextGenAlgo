# Database Scaffolding

Alembic migrations live here. Metadata is sourced from `backend/app/models`.

## Commands
```bash
# From project root
cd db
$env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/nextgen_algo"
# For local dry-runs without Postgres, point DATABASE_URL to sqlite
alembic upgrade head
```

## Current State
- Baseline revision `5e470f33fbe2_create_core_tables.py` creates users, brokers, accounts, orders, strategies, RMS, subscriptions, logs, trades, and positions tables.
- `migrations/env.py` injects the backend package into `PYTHONPATH` and reflects `DATABASE_URL` from environment variables supplied to Pydantic settings.

Set `DATABASE_URL` before running alembic commands to target the correct database.
