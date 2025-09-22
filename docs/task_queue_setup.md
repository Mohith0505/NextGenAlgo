# Task Queue & Worker Setup

Phase 2 automation relies on a Celery worker backed by Redis. Follow these steps to get the queue running locally:

## 1. Start Redis

If you already have Redis running via docker-compose:

```
cd infra
docker compose up redis -d
```

Otherwise install Redis locally and ensure it is reachable at `redis://localhost:6379/0`.

## 2. Configure Environment

Update `.env` (or use the defaults in `.env.example`):

```
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

If you are running Redis on another host/port, update these URLs accordingly.

## 3. Install Dependencies

Celery (with Redis extras) is already listed in `backend/requirements.txt`. Ensure the virtualenv has the latest dependencies:

```
cd backend
.\.venv\Scripts\pip.exe install -r requirements.txt
```

## 4. Start the Worker

Use the helper script to start a Celery worker in a separate terminal:

```
./scripts/start_worker.ps1 -DatabaseUrl "postgresql+psycopg://postgres:postgres@localhost:5432/nextgen_algo" -RedisUrl "redis://localhost:6379/0"
```

This launches Celery with the `app.celery_app` module and listens on the `strategy` queue.

## 5. Triggering Jobs

API calls to `/api/scheduler/jobs/{id}/trigger` or webhook events now enqueue Celery tasks. Monitor the worker output for dispatched strategy runs. Currently the task logs the dispatch stub; upcoming milestones will hook it into the real strategy execution engine.

