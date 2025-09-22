# 08 – Risk Management System (RMS)

The **Risk Management System (RMS)** is the safety backbone of the Next-Gen Algo Terminal.  
It ensures traders never exceed predefined **losses, exposures, or regulatory limits**.  
RMS operates at three levels: **Pre-trade, In-trade, Post-trade**.

---

## 🎯 Objectives
- Protect capital from runaway losses.
- Enforce compliance with trading limits.
- Provide real-time alerts and auto-actions.
- Support both **retail risk limits** and **institutional mandates**.

---

## 🛠️ RMS Levels

### 1. Pre-Trade Checks
- Validate before order goes to broker.
- Rules:
  - **Max Order Size** → limit lots per order.
  - **Max Daily Lots** → cap on total lots/day.
  - **Margin Check** → block if margin insufficient.
  - **Circuit Filter** → reject if outside price bands.
  - **Strike Filter** → only ATM ± N allowed.

### 2. In-Trade Monitoring
- Active monitoring after order placement.
- Rules:
  - **Max Daily Loss** → auto-square-off when hit.
  - **Profit Lock** → lock profits after threshold.
  - **Trailing Stop** → move SL as profit grows.
  - **Drawdown Limit** → auto-stop if equity drawdown too high.
  - **Exposure Cap** → block trades beyond % of capital.

### 3. Post-Trade Audits
- After trades close, system logs for compliance.
- Rules:
  - **PnL Logging** → realized + unrealized.
  - **Trade Trail** → who placed what, when.
  - **SEBI Reports** → exportable logs for audits.
  - **Daily Report** → auto-email of PnL, exposure.

---

## 🔄 RMS Workflow

1. **Order Request** → `/api/orders`
2. **Pre-Trade RMS Check**
   - If ✅ → go to broker.
   - If ❌ → reject with error (`RMS_MAX_LOTS`, `RMS_MARGIN_FAIL`).
3. **Execution**
   - Order fills.
4. **In-Trade RMS**
   - Monitor PnL, margin, exposure.
   - Trigger auto-SL or square-off if limits breached.
5. **Post-Trade**
   - Log into DB.
   - Send notifications to user.

---

## 📊 RMS Config API

### GET `/api/rms/config`
- Fetch current RMS rules.

### POST `/api/rms/config`
- Input: max loss, max lots, profit lock, trailing stop.

### GET `/api/rms/status`
- Current exposure, margin, PnL, alerts.

### POST `/api/rms/squareoff`
- Trigger full square-off (all accounts).

---

## 📢 Notifications

- **Web Alerts** → toast + RMS banner.
- **Email Alerts** → daily loss/profit notifications.
- **Telegram Alerts** → RMS-triggered messages.
- **UI Banner** → red/green strip on dashboard.

---

## 🔒 Safety Features

- RMS **always runs before broker call**.  
- Configurable per-user, per-account, or global.  
- RMS cannot be bypassed (enforced at backend).  
- Auto-square-off ensures positions are closed if rules break.  

---

## ✅ Summary
The RMS ensures trading is:
- **Safe** (no runaway losses),
- **Controlled** (daily & order limits),
- **Compliant** (logs for SEBI audits).  

It works seamlessly with strategies, manual trading, and multi-account execution.

---
