# 06 – Broker Integrations

The **Next-Gen Algo Terminal** must support **70+ Indian brokers** across NSE, NFO, BSE, MCX, and global derivatives (via APIs).  
This is achieved through a **Broker Adapter Layer** which standardizes all broker APIs under a single contract.

---

## 🧩 Design Approach

- **Broker Adapter Pattern**  
  - Each broker has a dedicated adapter (e.g., `AngelAdapter`, `ZerodhaAdapter`, `FyersAdapter`).  
  - All adapters implement a **common interface**:  
    - `connect()` → login/session  
    - `get_ltp(symbol)` → latest price  
    - `place_order(params)` → place an order  
    - `modify_order(order_id, params)` → modify existing order  
    - `cancel_order(order_id)` → cancel order  
    - `get_positions()` → open positions  
    - `get_holdings()` → portfolio  
    - `get_margin()` → margin status  

- **Session Management**  
  - Sessions stored encrypted in DB.  
  - Auto-refresh if expired.  
  - Alerts on failed login/session timeout.  

- **Execution Flow**  



---

## 🔑 Broker Categories

1. **Top Retail Brokers (NSE/NFO/MCX)**  
 - Angel One  
 - Zerodha (Kite Connect)  
 - Fyers  
 - Dhan  
 - Alice Blue  
 - Upstox  
 - 5Paisa  
 - ICICI Direct  
 - HDFC Securities  
 - Kotak Neo  
 - Axis Direct  

2. **Discount / API-first Brokers**  
 - Samco  
 - Shoonya (Finvasia)  
 - Prostoxx  
 - Trustline  

3. **Banks & Institutions**  
 - Yes Securities  
 - Motilal Oswal  
 - Edelweiss  
 - IIFL Securities  

4. **Crypto / Global Extensions (Phase 3)**  
 - Delta Exchange (Crypto Derivatives)  
 - Binance Futures (via connector)  

---

## ⚙️ Execution Logic

### Place Order
- Input: `{symbol, side, qty, order_type, TP, SL}`
- Steps:
1. Request received at backend `/api/orders`.
2. RMS check performed (limits, exposure, SL/TP validation).
3. Order routed to **Broker Adapter**.
4. Adapter converts to broker’s format and sends to API.
5. Execution response logged in DB.
6. Notification pushed to frontend.

### Modify Order
- Input: `{order_id, new_params}`
- Adapter sends modify request to broker API.
- DB + UI updated with latest status.

### Cancel Order
- Input: `{order_id}`
- Adapter calls broker cancel API.
- Confirmation logged and notified.

---

## 📡 Market Data Integration
- For brokers with **WebSocket APIs** (Zerodha, Angel One, Fyers, Dhan):  
- Subscribe via adapter.  
- Route ticks into Redis/Kafka → frontend.  

- For brokers without WebSocket:  
- Use vendor feed (TrueData/GDFL).  
- Map tokens to broker symbols.  

---

## 🔄 Multi-Account Execution
- One order → replicated across all linked accounts (fan-out).  
- Each adapter runs independently but reports back to central **Execution Manager**.  
- Lot allocation per account:  
- Equal distribution (e.g., 10 lots split into 2 accounts).  
- Custom allocation (defined by user).  

---

## 🛡️ Error Handling & Resilience
- Retry logic for network/API failures.  
- Circuit breaker (pause broker if repeated failures).  
- Fallback mode: if broker API is down → alert user.  
- Unified error codes returned to frontend (e.g., `BROKER_SESSION_EXPIRED`, `ORDER_REJECTED`).

---

## 📊 Example – Angel One Adapter

```python
class AngelAdapter(BaseBrokerAdapter):
  def connect(self, credentials):
      # Handle TOTP-based login
      return session_token

  def get_ltp(self, symbol):
      # Fetch LTP using Angel One API
      return price

  def place_order(self, params):
      # Convert params → Angel format
      # Call SmartAPI
      return order_id

  def get_positions(self):
      # Fetch open positions
      return positions
