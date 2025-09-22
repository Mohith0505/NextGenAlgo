# 05 – Backend APIs (FastAPI)

The **Next-Gen Algo Terminal** backend will be built on **FastAPI**.  
It exposes REST + WebSocket APIs for frontend and workers, with JWT-based authentication and role-based access.

---

## 🔑 API Categories

1. **Auth & Users**
2. **Brokers & Accounts**
3. **Orders & Trades**
4. **Positions & Portfolio**
5. **Strategies**
6. **Risk Management (RMS)**
7. **Option Chain & Market Data**
8. **Subscriptions & Payments**
9. **Admin APIs**
10. **Utility APIs**

---

## 1. Auth & Users

### POST `/api/auth/register`
- Input: name, email, phone, password
- Output: user created + JWT token

### POST `/api/auth/login`
- Input: email, password
- Output: JWT token + refresh token

### POST `/api/auth/refresh`
- Input: refresh token
- Output: new JWT

### GET `/api/users/me`
- Output: profile, roles, subscriptions

### PATCH `/api/users/{id}`
- Update user info, role, status

---

## 2. Brokers & Accounts

### POST `/api/brokers/connect`
- Input: broker_id, credentials (OAuth/TOTP/keys)
- Output: account linked, session token stored

### GET `/api/brokers/accounts`
- List of linked accounts + status

### DELETE `/api/brokers/{account_id}`
- Remove broker account

### POST `/api/brokers/{account_id}/refresh`
- Re-login to broker session

---

## 3. Orders & Trades

### POST `/api/orders`
- Input: account_id, symbol, side (BUY/SELL), qty, order_type, TP, SL
- Output: order placed

### GET `/api/orders/{order_id}`
- Order details

### GET `/api/orders`
- List user orders (filters: date, account, status)

### POST `/api/orders/bulk`
- Place multi-leg strategy orders

### DELETE `/api/orders/{order_id}`
- Cancel order

---

## 4. Positions & Portfolio

### GET `/api/positions`
- Live positions (account-wise, consolidated)

### POST `/api/positions/squareoff`
- Square-off all open positions

### GET `/api/portfolio`
- Holdings, realized/unrealized PnL

---

## 5. Strategies

### POST `/api/strategies`
- Create new strategy (upload code or webhook config)

### GET `/api/strategies`
- List all strategies

### GET `/api/strategies/{id}`
- Strategy details (params, status)

### POST `/api/strategies/{id}/start`
- Run strategy (backtest/paper/live)

### POST `/api/strategies/{id}/stop`
- Stop running strategy

---

## 6. Risk Management (RMS)

### GET `/api/rms/config`
- Fetch user RMS settings

### POST `/api/rms/config`
- Update RMS settings (max loss, max lots, profit lock)

### GET `/api/rms/status`
- Live RMS monitor (PnL, margin, exposures)

### POST `/api/rms/squareoff`
- Trigger RMS-based auto square-off

---

## 7. Option Chain & Market Data

### GET `/api/option-chain`
- Params: symbol, expiry
- Output: strikes with CE/PE OI, ChgOI, IV, Greeks

### GET `/api/ltp/{symbol}`
- Live LTP (index, stock, futures)

### WS `/ws/market-data`
- Live WebSocket feed for tick updates

---

## 8. Subscriptions & Payments

### GET `/api/subscriptions/plans`
- Available plans (Trial, Monthly, Yearly)

### POST `/api/subscriptions/start`
- Start subscription (via Razorpay payment)

### GET `/api/subscriptions/history`
- Billing history

### POST `/api/subscriptions/cancel`
- Cancel plan

---

## 9. Admin APIs

### GET `/api/admin/users`
- List all users + roles + active brokers

### GET `/api/admin/payments`
- Subscription & payment reports

### GET `/api/admin/logs`
- System logs (auth, trades, RMS)

### POST `/api/admin/users/{id}/deactivate`
- Block user account

---

## 10. Utility APIs

### GET `/api/health`
- Health check (DB, brokers, services)

### GET `/api/version`
- Current app version

### GET `/api/notifications`
- User notifications (trade confirmations, RMS alerts)

---

## 🔒 Security & Auth
- **JWT Auth** for all user routes.  
- **Role-based access** (User, Trader, Admin).  
- **Rate limiting** for APIs (per plan).  
- **Encrypted broker sessions** in DB.

---

## ✅ Summary
The backend APIs cover the full lifecycle:
- User auth → Broker connect → Place orders → RMS checks → Analytics → Admin control.  
All routes are documented via **FastAPI Swagger UI** (`/docs`), ensuring frontend and workers can integrate seamlessly.

---
