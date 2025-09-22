# 03 – Frontend Pages (React)

The **Next-Gen Algo Terminal** frontend will be built using **React** (with Tailwind + ShadCN for UI components).  
Each page will be modular, responsive, and connected to the backend via REST and WebSockets.  

---

## 🌐 Pages Overview
1. **Landing Page (Public)**
2. **Auth & Subscription**
3. **Dashboard**
4. **Broker Management**
5. **Quick Trade Panel (QTP)**
6. **Option Chain**
7. **Strategies**
8. **Risk Management**
9. **Admin Panel**
10. **Error/Utility Pages**

---

## 1. Landing Page (Public)
- **Purpose**: First impression, product info, sign-up flow.  
- **Sections**:
  - Hero banner with product name (**Next-Gen Algo Terminal**).
  - Features overview (multi-broker, RMS, option chain, connectors).
  - Pricing plans (free trial, monthly, yearly).
  - Supported brokers logos (Angel One, Zerodha, Fyers, etc.).
  - Testimonials/Case studies (optional).
  - Footer with contact, support, T&C, privacy policy.
- **Actions**:
  - "Sign Up" → registration.
  - "Login" → existing users.
  - "Start Free Trial" → subscription setup.

---

## 2. Auth & Subscription
- **Login Page**:
  - Email + password + 2FA (TOTP/OTP).
  - Forgot password → reset via email.
- **Register Page**:
  - Name, email, phone, password.
  - Choose subscription plan (trial auto-selected).
- **Subscription Page**:
  - Plan selection (Trial, Monthly, Yearly).
  - Payment gateway integration (Razorpay).
  - Billing history.
  - Upgrade/Downgrade plan.

---

## 3. Dashboard
- **Purpose**: Central hub after login.  
- **Widgets**:
  - Live ticker (NIFTY, BANKNIFTY, FINNIFTY, MCX).
  - Account summary (linked brokers, margins, PnL).
  - Open positions & trades.
  - Daily PnL graph.
  - Notifications panel (errors, RMS alerts, trade fills).
- **Actions**:
  - Quick navigation to Option Chain, QTP, Strategies.
  - "Square off all" button.

---

## 4. Broker Management
- **Purpose**: Manage broker connections.  
- **Sections**:
  - Add broker (select from list of 70+).
  - OAuth/TOTP login flow.
  - Linked accounts list (status, margin, positions).
  - Re-login / session refresh.
  - Remove account.
- **Actions**:
  - Enable/disable broker participation in strategies.
  - Allocate lots per account.

---

## 5. Quick Trade Panel (QTP)
- **Purpose**: Manual trading at lightning speed.  
- **Features**:
  - Buy/Sell buttons for selected instrument.
  - Pre-configured lot size.
  - TP/SL input fields.
  - Reverse position button.
  - Square-off all button.
  - Hotkeys (e.g., `B` for Buy, `S` for Sell).
- **UI Layout**:
  - Left: Instrument selection (search box).
  - Center: Buy/Sell panel.
  - Right: Positions summary.

---

## 6. Option Chain
- **Purpose**: Professional-grade options trading interface.  
- **Table Columns**:
  - Call OI, Call ChgOI, Call IV, Call Delta, Call LTP.
  - Strike Price.
  - Put LTP, Put Delta, Put IV, Put ChgOI, Put OI.
- **Highlights**:
  - ATM auto-detection.
  - Color-coded support/resistance (OI-based).
  - Click-to-trade (click LTP → order ticket).
  - Multi-leg builder:
    - Straddle, Strangle, Iron Condor, Butterfly, Spreads.
  - Greeks visualization panel.
- **Actions**:
  - Filter strikes (ATM ± 5, ± 10).
  - Export option chain to Excel/PDF.

---

## 7. Strategies
- **Purpose**: Manage automated strategies.  
- **Sections**:
  - Strategy List (built-in + user-uploaded).
  - Strategy Details (parameters, logs, PnL).
  - Start/Stop toggle.
- **Features**:
  - Backtest (historical).
  - Paper trade.
  - Live execution.
- **Built-in Strategies**:
  - Breakout (first-hour, NY/London sessions).
  - Straddle/Strangle.
  - Scalping.
  - Arbitrage (Index futures vs options).

---

## 8. Risk Management (RMS Panel)
- **Purpose**: Monitor and control risks in real time.  
- **Sections**:
  - Daily profit/loss caps.
  - Max lots per trade/day.
  - Exposure per account.
  - Auto-square-off toggle.
  - Real-time RMS alerts.
- **Actions**:
  - Set limits (profit lock, max loss).
  - Enable trailing stop logic.
  - View RMS logs.

---

## 9. Admin Panel
- **Purpose**: Management interface for Aditya Fin Technologies.  
- **Sections**:
  - User management (list, roles, subscriptions).
  - Broker health monitor.
  - Payment reports.
  - Usage analytics (active accounts, trades).
  - System logs.
- **Actions**:
  - Activate/deactivate users.
  - Reset broker sessions.
  - View compliance logs.

---

## 10. Error/Utility Pages
- **404 Page** → Page not found.  
- **500 Page** → Internal server error.  
- **Maintenance Page** → For downtime.  

---

## ✅ Summary
The frontend will contain **10 core pages**, each with clear navigation and modular components.  
Pages are linked via a top navigation bar + sidebar.  
Every page communicates with backend via REST APIs and WebSockets, ensuring **real-time updates** for traders.

---
