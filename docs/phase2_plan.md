# Phase 2 Execution Plan

## Objectives
- Deliver production-grade multi-account execution with dynamic lot allocation, fan-out orchestration, and execution telemetry.
- Expand analytics to cover strategy equity curves, broker/account PnL, exposure heatmaps, and RMS incident timelines.
- Harden strategy automation with webhook connectors, scheduling, and workflow observability.
- Elevate RMS with automated remediation (auto hedge/scaleout), configurable guardrail templates, and proactive notifications.

## Workstreams
1. **Execution & Accounts**
   - Account registry: tagging, lot allocation policies, execution priorities.
   - Multi-account order router (synchronous + async fan-out, failure handling, rollback).
   - Execution telemetry: per account/order lifecycle events, latency benchmarks, audit storage.
   - UI updates: broker/account matrix, fan-out controls, live execution feed.

2. **Analytics & Reporting**
   - Time-series service for equity/Gamma/PCR analytics (Timescale-ready schema, caching layer).
   - Dashboards: strategy equity curve, broker/account PnL, RMS incidents, execution SLA metrics.
   - Export engine: CSV/PDF pipeline with scheduled delivery and compliance headers.

3. **Strategy Automation**
   - Webhook connector manager (TradingView, Amibroker, MT4/5, Excel, custom HTTP).
   - Strategy scheduler (cron-style triggers, manual reruns, concurrency guardrails).
   - Workflow observability (run timelines, state transitions, log streaming, alerting rules).

4. **Risk Management & Alerts**
   - Guardrail templates (e.g., intraday scalper, positional) with override workflows.
   - Automated responses (auto hedge, throttle orders, square-off by group, SMS/Telegram alerts).
   - Incident timeline and playbook builder for compliance sign-off.

5. **Infrastructure & DevOps**
   - Postgres migration path (dev/staging), Timescale/ClickHouse evaluation, Pydantic/ORM updates.
   - Background worker autoscaling (Celery/Arq) with Prometheus metrics and Grafana dashboards.
   - GitHub Actions upgrades: parallel test matrix, Playwright UI regression suite, security scans.

## Milestones & Timeline (Draft)
- **Month 4:** Multi-account core (backend), execution UI controls, initial strategy telemetry.
- **Month 5:** Analytics expansion, webhook connectors, RMS templates, Postgres rollout.
- **Month 6:** Automated RMS responses, export engine, infra hardening (autoscaling + observability), production readiness review.

## Data & Test Strategy
- Seed datasets: multi-account users, sample strategies, webhook payloads.
- Add fixture factories for accounts, execution routes, RMS incidents.
- Integration suites: fan-out execution tests, webhook replay, analytics snapshot comparisons, RMS guardrail simulations.
- UI regression via Playwright covering dashboards, broker fan-out, strategy runs, RMS configuration.

## Dependencies & Risks
- Postgres/Timescale availability, secret management for connectors, messaging layer for fan-out.
- Coordination with compliance and ops teams for RMS templates and incident workflows.
- User education: updated docs, in-app walkthroughs for new execution mechanics.

## Next Steps
1. Stand up Postgres or managed Timescale for dev/staging; migrate from SQLite.
2. Implement account registry models, migrations, and API endpoints.
3. Extend broker service with fan-out orchestration and telemetry.
4. Wire dashboards to new analytics endpoints; add Playwright baseline tests.
5. Schedule regular steering reviews aligned with milestone cadence.
