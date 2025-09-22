# 04 – Frontend Components (React)

The **Next-Gen Algo Terminal** frontend will be component-driven.  
Each component is reusable, responsive, and optimized for real-time trading updates.  

---

## 🧩 Component Categories

1. **Navigation & Layout**
2. **Data Display (Tables, Charts, Cards)**
3. **Trading Components**
4. **Forms & Modals**
5. **Notifications & Alerts**
6. **Utility Components**

---

## 1. Navigation & Layout
### Header
- Logo (Aditya Fin Technologies).
- Navigation links (Dashboard, Option Chain, Strategies, RMS, Admin).
- User menu (Profile, Settings, Logout).

### Sidebar
- Collapsible menu with icons.
- Broker status indicators.
- Quick shortcuts (QTP, Open Positions).

### Footer
- Version info.
- Links to Privacy Policy, T&C, Support.

---

## 2. Data Display

### DataTable
- Custom table component with:
  - Sorting, filtering.
  - Sticky header.
  - Pagination / infinite scroll.
  - Dynamic coloring (e.g., red for falling LTP, green for rising LTP).

### CandlestickChart
- Realtime OHLC chart.
- Timeframe selector (1m, 5m, 15m, 1h, 1D).
- Overlays (SMA, EMA, VWAP).
- Markers for Buy/Sell signals.

### OptionChainTable
- Specialized DataTable for CE/PE strikes.
- ATM highlighting.
- Color-coded OI build-up.
- Clickable cells → trade ticket.

### Card
- Small widget for quick stats:
  - “Daily PnL”
  - “Margin Used”
  - “Open Trades”
  - “Broker Session Status”

---

## 3. Trading Components

### OrderTicket
- Modal with fields:
  - Instrument, strike, type (CE/PE).
  - Qty/lots.
  - Order type (Market/Limit).
  - TP, SL, Trailing SL.
- Submit button (routes to backend API).

### MultiLegBuilder
- UI to build complex strategies:
  - Straddles, Strangles, Spreads, Iron Condors.
- Drag-and-drop strikes into builder.
- Preview margin, payoff diagram.
- One-click execute.

### QuickTradeButtons
- Large “Buy” / “Sell” buttons.
- Configurable hotkeys.
- Reverse / Square-off all.

---

## 4. Forms & Modals

### LoginForm
- Email, password, TOTP input.
- Error validation.

### SubscriptionForm
- Plan selection (Trial, Monthly, Yearly).
- Payment integration.
- Billing history table.

### BrokerConnectModal
- Dropdown of brokers.
- Login via OAuth/TOTP.
- Connection status feedback.

### StrategyConfigModal
- Parameters input (entry time, SL %, TP target).
- Backtest or deploy toggle.
- Save/Cancel buttons.

---

## 5. Notifications & Alerts

### ToastAlert
- Small top-right notifications for:
  - Order placed.
  - Broker session expired.
  - RMS alert triggered.

### TradeConfirmationPopup
- Modal after placing an order:
  - “Order executed @ LTP: 512.50”
  - Success/failure color.

### RMSAlertBanner
- Persistent red/green banner:
  - “Max daily loss reached – Auto square-off enabled.”

---

## 6. Utility Components

### Loader
- Spinner for API calls.

### ErrorBoundary
- Catches UI crashes, displays fallback message.

### Tooltip
- Hover tooltips with extra info (e.g., “Delta measures sensitivity…”).

### DateRangePicker
- Used in reports, backtests, analytics.

---

## 🔄 Component Integration

- **Pages use Components**:
  - Dashboard → Card + DataTable + CandlestickChart.
  - Option Chain → OptionChainTable + OrderTicket + MultiLegBuilder.
  - QTP → QuickTradeButtons + OrderTicket.
  - Strategies → DataTable + StrategyConfigModal.
  - RMS Panel → RMSAlertBanner + Card.

---

## ✅ Summary
The component library ensures **consistency and reusability** across the entire terminal.  
By isolating logic (API calls, WebSocket updates) inside components, the frontend remains **modular and scalable**.

---
