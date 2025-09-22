# Utility Scripts

This directory contains helper utilities used during early-phase execution.

## Requirements
- Activate the backend virtual environment (`backend/.venv`) or use its interpreter directly.
- Set `DATABASE_URL` before running scripts (defaults point to `db/dev.db`).

## Available Scripts

### Backend / Frontend Runners
- `start_backend.ps1` – launches Uvicorn with hot reload. Example:
  ```powershell
  scripts\start_backend.ps1
  # or specify a different database
  scripts\start_backend.ps1 -DatabaseUrl "sqlite+pysqlite:///C:/tmp/test.db"
  ```
- `start_frontend.ps1` – starts the Vite dev server:
  ```powershell
  scripts\start_frontend.ps1
  scripts\start_frontend.ps1 -ApiBaseUrl "http://localhost:8080"
  ```

### Seed & Smoke Utilities
- `seed_user.py` – creates the default owner account if none exists.
- `smoke_test.py` – hits health/status endpoints to ensure the backend boots.
- `phase1_flow.py` – exercises broker connect + order placement via the paper adapter.
- `phase1_strategy_flow.py` – covers strategy CRUD and lifecycle calls.

Run Python scripts with:
```powershell
$env:DATABASE_URL = "sqlite+pysqlite:///E:/AdityaFin_NextGenAlgo_DPR/db/dev.db"
backend\.venv\Scripts\python.exe scripts\phase1_flow.py
```

Update credentials or database URLs as you promote to staging/production environments.
