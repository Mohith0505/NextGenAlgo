# Aditya Fin Technologies – Next-Gen Algo Terminal  
**Master Development Guide for Codex**

---

## 📘 Introduction
This document is the **master control file** for building the project **Next-Gen Algo Terminal** by **Aditya Fin Technologies**.  
It explains the exact order in which Codex (or any developer) must read the detailed DPR chunks and generate code.  
The goal is to ensure a **production-grade algo bridge** with 70+ broker integrations, option chain trading, RMS, connectors, subscriptions, and admin modules.

---

## ⚡ Development Workflow

Codex must **follow these steps in order**.  
At the end of each step, Codex must:  
- ✅ Confirm the step is complete.  
- 📂 Show the updated project folder structure.  
- ▶️ Run the app (if applicable) to confirm it works before moving on.

---

### Step 1 → Project Setup
- Read: `01_intro_vision.md` and `02_system_architecture.md`  
- Create **project scaffolding**:  
  - `backend/` → FastAPI base project  
  - `frontend/` → React base project  
  - `db/` → Database migrations/config  
  - `infra/` → Docker + K8s setup  
- Run `uvicorn backend.app.main:app --reload` and `npm start` for frontend.  
- Confirm both backend and frontend run with **Hello World**.

---

### Step 2 → Frontend Pages
- Read: `03_frontend_pages.md`  
- Build basic React pages:  
  - Landing Page  
  - Auth & Subscription  
  - Dashboard  
  - Broker Management  
  - Quick Trade Panel (QTP)  
  - Option Chain  
  - Strategies  
  - Risk Management  
  - Admin Panel  
- Implement navigation between pages.  
- Confirm app runs with all routes accessible.

---

### Step 3 → Frontend Components
- Read: `04_frontend_components.md`  
- Build reusable components: tables, charts, order ticket, multi-leg builder, modals, alerts.  
- Connect components into the pages.  
- Confirm UI renders correctly.

---

### Step 4 → Backend APIs
- Read: `05_backend_apis.md`  
- Implement FastAPI routes for:  
  - Auth (JWT)  
  - Users & Workspaces  
  - Brokers & Accounts  
  - Orders, Positions, Trades  
  - Strategies  
  - Risk checks  
  - Subscriptions & Payments  
- Test with `/docs` (Swagger) to confirm endpoints.

---

### Step 5 → Database Schema
- Read: `09_database_schema.md`  
- Create Postgres database schema with SQLAlchemy + Alembic migrations.  
- Confirm all tables are created.  
- Show ERD (Entity Relationship Diagram).

---

### Step 6 → Broker Integrations
- Read: `06_broker_integrations.md`  
- Implement adapters for brokers (start with Angel One, Zerodha, Fyers).  
- Add multi-account execution logic.  
- Confirm paper trades can be placed.

---

### Step 7 → Strategy Engine
- Read: `07_strategy_engine.md`  
- Add support for strategies (built-in + custom).  
- Implement backtest → paper → live parity.  
- Confirm one test strategy runs.

---

### Step 8 → Risk Management
- Read: `08_risk_management.md`  
- Add RMS checks:  
  - Max loss/day, max lots  
  - Auto-SL, Trailing SL  
  - Profit lock, auto square-off  
- Confirm limits are enforced in trades.

---

### Step 9 → Analytics & Tools
- Read: `10_analytics_tools.md`  
- Add analytics:  
  - Option Chain Greeks & IV  
  - OI, ChgOI, PCR  
  - Delta Spread, Gamma Regime  
  - Bias detection with confidence  
- Confirm analytics display in dashboard.

---

### Step 10 → Infra, DevOps & Security
- Read: `11_infra_devops_security.md`  
- Add Docker/K8s setup, CI/CD pipeline.  
- Add monitoring (Prometheus/Grafana).  
- Implement security best practices (secrets, encryption, SEBI compliance).  
- Confirm system runs in Docker containers.

---

### Step 11 → Roadmap
- Read: `12_roadmap_phases.md`  
- Review phased rollout:  
  - **Phase 1:** Core MVP (single broker, QTP, basic RMS)  
  - **Phase 2:** Multi-account, option strategies, subscriptions  
  - **Phase 3:** Scaling, marketplace, ecosystem integrations  

---

## ✅ Completion Criteria
When all steps are done:  
- Backend runs (FastAPI) with all services.  
- Frontend runs (React) with all pages & components.  
- Database stores trades, users, accounts, subscriptions.  
- Brokers execute real & paper trades.  
- Strategies + RMS + Analytics work.  
- Admin panel + Subscriptions functional.  
- System deployed via Docker/K8s with monitoring.

---

## 📌 Notes for Codex
- Always **read the referenced DPR chunk** before coding.  
- Maintain **consistent naming** across backend, frontend, DB.  
- After each step, **show folder tree** and confirm app runs.  
- Never skip a step.

---
