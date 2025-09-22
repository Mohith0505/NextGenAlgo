# Postgres Development Setup

This project now targets Postgres (and future Timescale) as the primary database for Phase 2 features. Use the steps below to run a local instance and point the backend at it.

## 1. Start Postgres (Docker Compose)

```
cd infra
# Starts Postgres on localhost:5432 with default credentials
# (postgres/postgres) and persists data in the `db-data` volume
docker compose up db -d
```

If Docker is not available, install Postgres locally and create a database named `nextgen_algo` with the same username/password.

## 2. Configure Environment

Copy the sample env file and adjust if needed:

```
cp .env.example .env
```

Update `DATABASE_URL` if you changed credentials or database name, e.g.

```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/nextgen_algo
```

## 3. Apply Database Migrations

The backend PowerShell helper will run Alembic automatically when `DATABASE_URL` is provided:

```
./scripts/start_backend.ps1 -DatabaseUrl "postgresql+psycopg://postgres:postgres@localhost:5432/nextgen_algo"
```

You can also run Alembic directly:

```
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

## 4. Seed Demo Data (Optional)

```
cd backend
.\.venv\Scripts\python.exe ..\scripts\seed_user.py
```

This creates the `owner@example.com` demo account against the new Postgres database.

## Troubleshooting

- Ensure port `5432` is not in use before starting the container.
- Confirm the backend virtualenv has `psycopg[binary]` installed (listed in `backend/requirements.txt`).
- If migrations fail, drop and recreate the database, then rerun `alembic upgrade head`.
