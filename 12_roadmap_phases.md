# 12 – Roadmap & Phases

The **Next-Gen Algo Terminal** will be delivered in **phases**, ensuring stability, user adoption, and feature completeness.  
Each phase builds upon the previous one, moving from **core MVP** to **full institutional-grade platform**.

---

## 📌 Phase 1 – Core MVP

### Objectives
- Deliver a working product with **basic algo bridge features**.
- Onboard early users with free trials.
- Validate latency, broker connectivity, and RMS.

### Features
1. **Frontend**
   - Landing Page (Signup/Login, Pricing, Trial).
   - Dashboard (LTP, positions, PnL).
   - Broker Management (link Angel One + Zerodha).
   - Quick Trade Panel (QTP).
   - Option Chain (ATM ±5, OI, ChgOI, IV, Delta).

2. **Backend**
   - Auth (JWT, RBAC).
   - Broker Adapters (Angel One, Zerodha).
   - Orders, Positions, Trades.
   - Basic RMS (max loss/day, max lots).
   - Subscription engine (19-day trial, monthly plan).

3. **Database**
   - Users, brokers, accounts, orders, trades, RMS rules, subscriptions.
   - Ticks & option chain storage (Timescale).

4. **Infra**
   - Docker Compose (dev).
   - Cloud deployment (staging + production).
   - Basic monitoring (Prometheus + Grafana).

---

## 📌 Phase 2 – Advanced Features

### Objectives
- Expand to multi-account, multi-user, and advanced options strategies.
- Improve analytics and RMS.
- Add connectors for external signals.

### Features
1. **Frontend**
   - Multi-leg option builder (Straddle, Strangle, Iron Condor).
   - Strategies page (start/stop, parameters, logs).
   - RMS Panel (profit lock, trailing SL).
   - PnL dashboard (trade-wise, strategy-wise).
   - Admin Panel (user list, payments, logs).

2. **Backend**
   - Multi-account execution.
   - Strategy Engine (Backtest → Paper → Live).
   - Expanded broker support (10–15 brokers).
   - RMS upgrades (profit lock, drawdown limit).
   - Option bias detection (confidence scoring).

3. **Database**
   - Strategy logs.
   - RMS logs.
   - Performance reports.

4. **Infra**
   - Kubernetes deployment (scalable workers).
   - CI/CD pipelines (GitHub Actions/GitLab).
   - ELK/Loki for centralized logging.

---

## 📌 Phase 3 – Ecosystem & Scaling

### Objectives
- Become the **institutional-grade algo trading SaaS** in India.
- Support all 70+ brokers.
- Add global markets + marketplace.

### Features
1. **Frontend**
   - Full-featured analytics suite (OI heatmap, Gamma regime, PCR).
   - Strategy marketplace (share/buy/sell strategies).
   - Advanced reports & exports (PDF, CSV).
   - Compliance dashboards.

2. **Backend**
   - 70+ broker adapters live.
   - Connectors: TradingView, Amibroker, MT4/5, Excel, Telegram.
   - Institutional features: user workspaces, role hierarchy, portfolio-level RMS.
   - Global market connectors (Delta Exchange, Binance Futures).

3. **Database**
   - Long-term data storage (7+ years).
   - Compliance-ready audit trail.
   - Institutional reporting.

4. **Infra**
   - Multi-region deployment (India + backup region).
   - Auto-scaling clusters.
   - DDoS protection & enterprise SLAs.
   - Full disaster recovery system.

---

## ✅ End State

At the end of Phase 3, the **Next-Gen Algo Terminal** will be:
- Fully **web-native** (no EXE/VPS).
- Supporting **70+ brokers** + global connectors.
- Providing **advanced RMS, analytics, and strategies**.
- SaaS-ready with **subscriptions, admin panel, compliance**.
- Scalable, secure, and institutional-grade.

This completes the **full project roadmap**.

---
---

## Execution Timeline (Draft)
- **Phase 1 (Months 0-3)**: Harden MVP feature set, onboard pilot users, validate broker/RMS flows before scaling traffic.
- **Phase 2 (Months 3-6)**: Roll out advanced strategies, multi-account execution, and analytics dashboards while expanding broker coverage.
- **Phase 3 (Months 6-12)**: Deliver institutional capabilities, marketplace features, and multi-region infrastructure with compliance sign-off.

## Readiness Checklist
- ? Technical groundwork for core modules (frontend, backend, RMS, analytics) is documented in Steps 1-10.
- ?? Define ownership, budgets, and KPIs for each phase ahead of execution kickoff.
- ?? Establish steering cadence (bi-weekly) and milestone reviews tied to the above timeline.
