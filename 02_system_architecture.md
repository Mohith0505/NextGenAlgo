# 02 – System Architecture

## 🏗️ High-Level Architecture

The **Next-Gen Algo Terminal** is designed as a **modular, web-native, full-stack system**.  
It consists of four main layers:

1. **Frontend (React + WebSockets)**  
   - User interface for traders, admins, and institutions.  
   - Displays dashboards, charts, option chain, strategies, and risk monitoring.  
   - Communicates with backend via REST + WebSockets.

2. **Backend (FastAPI + Workers)**  
   - Handles business logic, broker adapters, RMS, strategy engine, and subscriptions.  
   - Provides REST APIs for frontend.  
   - Uses background workers for live trading, market data, and risk monitoring.

3. **Database Layer (Postgres + Timescale/ClickHouse)**  
   - Stores users, accounts, trades, subscriptions, audit logs.  
   - Timescale/ClickHouse stores tick & option chain data.  
   - Alembic handles migrations.

4. **Infrastructure (Docker + Kubernetes)**  
   - Containerized microservices for frontend, backend, workers, and DB.  
   - Scalable deployment with Kubernetes.  
   - Monitoring, logging, and CI/CD pipelines ensure reliability.

---

## 🔄 Data Flow Overview

1. **Market Data**  
   - Broker/vendor WebSocket → Backend Data Worker → Redis/Kafka → Frontend live updates.

2. **Orders**  
   - User action (UI or strategy trigger) → Backend API → RMS validation → Broker Adapter → Broker API.  
   - Execution response → Backend → Database log → Frontend UI update.

3. **Strategies**  
   - Strategy Runner subscribes to market data events.  
   - On signal → order request → RMS → Broker Adapter → Broker API.  
   - Execution result logged and displayed in UI.

4. **Risk Management**  
   - Runs in backend worker.  
   - Monitors trades, exposure, PnL, margins in real time.  
   - Can auto-square-off or block orders.

5. **Subscriptions & Admin**  
   - User signup → Payment Gateway (Razorpay) → Subscription table update.  
   - Feature flags enabled based on plan.  
   - Admin panel can view/manage users & payments.

---

## ⚙️ Components

### Frontend
- React + Vite/CRA
- Tailwind + ShadCN for UI
- WebSocket for live LTP
- Pages: Landing, Dashboard, Option Chain, Strategies, RMS, Admin

### Backend
- FastAPI (REST + WebSockets)
- Services:
  - Auth & Users
  - Broker Adapters
  - Orders & Positions
  - Strategy Engine
  - RMS
  - Subscription & Payments
- Background Workers:
  - Market Data Processor
  - Strategy Runner
  - Risk Monitor
  - Notifications (Telegram/Email)

### Database
- **Postgres** → users, accounts, orders, strategies, subscriptions, logs  
- **Timescale/ClickHouse** → ticks, option chain, greeks  
- **Redis/Kafka** → caching + streaming

### Infrastructure
- Dockerized microservices
- Kubernetes for scaling
- CI/CD pipelines (GitHub Actions, GitLab CI, or Jenkins)
- Monitoring with Prometheus + Grafana
- Logging with ELK (Elasticsearch, Logstash, Kibana) or Loki
- Secrets with Vault/KMS

---

## 📊 High-Level Diagram (Mermaid)

```mermaid
flowchart TD
    subgraph UI [Frontend - React]
        LP[Landing Page]
        DB[Dashboard]
        OC[Option Chain]
        STR[Strategies]
        RMS[Risk Mgmt Panel]
        ADM[Admin Panel]
    end

    subgraph BE [Backend - FastAPI]
        AUTH[Auth Service]
        BROK[Broker Adapters]
        ORD[Orders Service]
        STRAT[Strategy Engine]
        RISK[RMS Engine]
        SUBS[Subscriptions]
        API[REST + WS API Layer]
    end

    subgraph DBL [Database Layer]
        PG[(Postgres)]
        TS[(Timescale/ClickHouse)]
        RD[(Redis/Kafka)]
    end

    subgraph INF [Infrastructure]
        DOC[Docker]
        K8S[Kubernetes]
        MON[Monitoring]
        LOG[Logging]
        SEC[Secrets Mgmt]
    end

    UI <--> API
    API --> AUTH
    API --> BROK
    API --> ORD
    API --> STRAT
    API --> RISK
    API --> SUBS

    BE --> PG
    BE --> TS
    BE --> RD
    BE --> INF
