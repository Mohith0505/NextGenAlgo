# Phase 1 Validation Playbook

This guide walks through the manual checks that confirm the Phase 1 backend and frontend are wired correctly against the paper trading environment.

## 1. Prerequisites
- Python virtual environment bootstrapped at `backend/.venv` (per project setup).
- Node.js 20+ and npm installed.
- SQLite dev database present at `db/dev.db` (created during backend planning).

## 2. Start the Backend
```powershell
cd E:\AdityaFin_NextGenAlgo_DPR\backend
$env:DATABASE_URL = "sqlite+pysqlite:///E:/AdityaFin_NextGenAlgo_DPR/db/dev.db"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe ..\scripts\seed_user.py
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```
Leave the server running.

## 3. Start the Frontend
```powershell
cd E:\AdityaFin_NextGenAlgo_DPR\frontend
$env:VITE_API_BASE_URL = "http://localhost:8000"
npm install   # first time only
npm run dev
```
Open the printed URL (normally `http://localhost:5173`).

## 4. Smoke Scripts (Optional)
In another shell:
```powershell
cd E:\AdityaFin_NextGenAlgo_DPR
$env:DATABASE_URL = "sqlite+pysqlite:///E:/AdityaFin_NextGenAlgo_DPR/db/dev.db"
backend\.venv\Scripts\python.exe scripts\phase1_flow.py
backend\.venv\Scripts\python.exe scripts\phase1_strategy_flow.py
```
Both scripts should finish with HTTP 200 responses and display paper-broker orders/strategy runs.

## 5. Manual UI Walkthrough
1. **Dashboard** – verify cards render numeric values and positions table loads (may be empty initially).
2. **Broker Management** – use the default form to link the paper trading broker (client code `demo`), confirm it appears in the table.
3. **Quick Trade Panel** – place a market BUY; confirm success banner and the order appears in the Latest Orders table.
4. **Strategies** – create a “Opening Range Breakout” strategy, start/stop it, and review status updates.
5. **Risk Management** – view status metrics, optionally adjust limits and save the configuration.

## 6. Troubleshooting
- If API calls fail, check the backend console for stack traces.
- Ensure `DATABASE_URL` and `VITE_API_BASE_URL` environment variables are set in the shells running backend/frontend.
- Regenerate the dev database by deleting `db/dev.db` and rerunning the Alembic + seed steps above.

Keep this playbook updated as new features land in later phases.
> **Tip:** Use the seeded credentials (`owner@example.com` / `StrongPass123`) on the Sign-In page once the frontend loads. Successful login unlocks the left-hand navigation.
