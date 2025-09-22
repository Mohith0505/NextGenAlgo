# 07 – Strategy Engine

The **Strategy Engine** is the core module that powers **automated trading** in the Next-Gen Algo Terminal.  
It allows traders to use **built-in strategies**, upload **custom strategies**, or connect via **external signals** (TradingView, Amibroker, MT4/5, Excel, Telegram).

---

## 🎯 Objectives
- Run strategies in **three modes**: Backtest → Paper → Live.
- Ensure **broker-agnostic execution** through adapters.
- Provide **real-time monitoring** (logs, trades, PnL).
- Allow **safe experimentation** without risking capital.

---

## 🔄 Strategy Lifecycle

1. **Backtest Mode**
   - Uses historical 1m/5m data from Timescale/ClickHouse.
   - Calculates PnL, win rate, drawdown, Sharpe ratio.
   - Displays charts with entry/exit markers.

2. **Paper Trading Mode**
   - Uses live market data.
   - Executes trades in a **virtual account** (no broker).
   - Logs trades + PnL in DB.

3. **Live Trading Mode**
   - Real execution via broker adapters.
   - RMS guardrails enforced before sending orders.
   - Multi-account fan-out supported.

---

## 🛠️ Components

### Strategy Manager
- CRUD operations for strategies.
- Stores metadata: name, type, parameters, owner, status.

### Strategy Runner
- Worker that subscribes to market data streams.
- Applies strategy logic.
- Emits trade signals (BUY/SELL).
- Routes signals → RMS → Broker Adapters.

### Strategy Sandbox
- Isolated environment for user-uploaded strategies.
- Restricts unsafe operations (security sandboxing).
- Exposes limited API (fetch_data, place_order, log_event).

### Signal Connectors
- Accepts external triggers:
  - **TradingView** → Webhook → Strategy Runner.
  - **Amibroker** → AFL bridge → Strategy Runner.
  - **Excel** → WebSocket link.
  - **MT4/MT5** → Bridge adapter.
  - **Telegram Bot** → Signal execution.

---

## 📦 Built-in Strategies (Phase 1–2)

1. **Breakout Strategies**
   - Daily first-hour high/low breakout.
   - London/NY session breakout.
   - 15-min opening range breakout.

2. **Options Strategies**
   - ATM straddle/strangle.
   - Iron condor.
   - Bull call spread.
   - Protective put.

3. **Trend/Channel Strategies**
   - Support/resistance bounce.
   - Parallel channel breakout.
   - ATR-based trailing breakout.

4. **Arbitrage**
   - Index futures vs synthetic spot.
   - NIFTY vs BANKNIFTY pair trading.

---

## 🖥️ API Endpoints (from Backend)

- `POST /api/strategies` → create strategy.
- `GET /api/strategies` → list strategies.
- `POST /api/strategies/{id}/start` → start strategy in mode (backtest/paper/live).
- `POST /api/strategies/{id}/stop` → stop strategy.
- `GET /api/strategies/{id}/logs` → fetch execution logs.
- `GET /api/strategies/{id}/pnl` → performance metrics.

---

## 📊 Monitoring & Reporting

- **Live Logs Panel** → every entry/exit decision with reason.
- **Performance Dashboard**:
  - Total trades, win rate.
  - Current PnL (per strategy, per account).
  - Drawdown %.
- **Charts**:
  - Trade markers on candlestick charts.
  - Strategy equity curve.

---

## 🔒 Safety Features

- All signals pass through **RMS** before reaching brokers.  
- Daily max-loss & exposure checks prevent runaway losses.  
- Strategy auto-stops if errors exceed threshold.  
- Sandboxed execution for user strategies.

---

## ✅ Summary
The Strategy Engine enables traders to:
- Use **ready-made strategies**,
- Upload **custom code**,
- Or connect via **external signals**.  

It ensures strategies are **safe, monitored, and broker-agnostic**, running seamlessly across backtest, paper, and live environments.

---
