
# Angel One (SmartAPI) — Complete Integration Guide (Updated)

> **Purpose:** This document gives Codex everything needed to wire Angel One’s **SmartAPI** into our terminal: authentication (login/logout), order placement, modification, cancellation, SL/TP updates, books, websockets, and troubleshooting.  
> **Place in repo:** `docs/AngelOne.md`

---

## 0) Quick Start (TL;DR)

- **Base URL:** `https://apiconnect.angelone.in`  
- **Auth endpoint:** `POST /rest/auth/angelbroking/user/v1/loginByPassword`  
- **Headers (all calls):**
  - `Accept: application/json`
  - `Content-Type: application/json`
  - `X-UserType: USER`
  - `X-SourceID: WEB`
  - `X-PrivateKey: <API_KEY>`
  - Recommended (avoid edge/WAF blocks): `X-ClientLocalIP`, `X-ClientPublicIP`, `X-MACAddress`
- **Auth body:** `{ "clientcode": "<ID>", "password": "<PIN or Password>", "totp": "<6-digit>" }`
- Returns: `jwtToken`, `refreshToken`, `feedToken` (keep secure).  
- **Send `Authorization: Bearer <jwtToken>` on all secure endpoints.**

---

## 1) Prerequisites

- Angel One **client code** and **trading PIN/password**.  
- **SmartAPI key** (from SmartAPI dashboard).  
- **TOTP enabled** (Authenticator app). You generate a 6‑digit code per login.  
- Our terminal must keep secrets (API key, PIN, TOTP secret) **outside Git**.

---

## 2) Authentication Flow

### 2.1 Sequence
1. User supplies: `api_key`, `client_code`, `pin/password`, **current TOTP** (6 digits).  
2. `POST /rest/auth/angelbroking/user/v1/loginByPassword` with headers in §0.  
3. On success, store `jwtToken`, `refreshToken`, `feedToken`.  
4. Optional sanity: call `GET /rest/secure/angelbroking/user/v1/getProfile`.  
5. Use `Authorization: Bearer <jwtToken>` for all secure routes.  
6. When session expires, re‑login with TOTP (or SDK’s refresh if available).  
7. Logout: `POST /rest/secure/angelbroking/user/v1/logout` (optional).

### 2.2 Minimal tests (PowerShell)
```powershell
$body = @{
  clientcode = "<CLIENT_CODE>"
  password   = "<PIN_OR_PASSWORD>"
  totp       = "<CURRENT_6_DIGIT_TOTP>"
} | ConvertTo-Json

$headers = @{
  "Accept"           = "application/json"
  "Content-Type"     = "application/json"
  "X-UserType"       = "USER"
  "X-SourceID"       = "WEB"
  "X-PrivateKey"     = "<API_KEY>"
  "X-ClientLocalIP"  = "127.0.0.1"
  "X-ClientPublicIP" = "127.0.0.1"
  "X-MACAddress"     = "AA-BB-CC-DD-EE-FF"
}

Invoke-RestMethod -Uri "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword" `
  -Method POST -Headers $headers -Body $body
```

### 2.3 SDK option (preferred if available)

**Node (smartapi-javascript)** — handles routes, tokens & websockets
```js
const { SmartAPI, WebSocketClient } = require('smartapi-javascript');

const smart = new SmartAPI({ api_key: process.env.ANGEL_API_KEY });

const session = await smart.generateSession(
  process.env.ANGEL_CLIENT,
  process.env.ANGEL_PIN,      // or password
  process.env.ANGEL_TOTP      // 6-digit current code
);

// sanity
const profile = await smart.getProfile();
```

**Python (smartapi-python)** — simple login & token handling
```python
from SmartApi import SmartConnect
import pyotp, os

smart = SmartConnect(os.environ["ANGEL_API_KEY"])
totp  = pyotp.TOTP(os.environ["ANGEL_TOTP_SECRET"]).now()
data  = smart.generateSession(os.environ["ANGEL_CLIENT"], os.environ["ANGEL_PIN"], totp)

jwt   = data["data"]["jwtToken"]
feed  = smart.getfeedToken()
```

> Sessions typically remain valid until early next day; handle expiry hooks and re‑login gracefully in the adapter.

---

## 3) Core REST Endpoints (secure routes)

Use `Authorization: Bearer <jwtToken>` + headers from §0.

- **Profile**: `GET /rest/secure/angelbroking/user/v1/getProfile`
- **RMS**: `GET /rest/secure/angelbroking/user/v1/getRMS`
- **Place order**: `POST /rest/secure/angelbroking/order/v1/placeOrder`
- **Modify order**: `POST /rest/secure/angelbroking/order/v1/modifyOrder`
- **Cancel order**: `POST /rest/secure/angelbroking/order/v1/cancelOrder`
- **Order book**: `GET /rest/secure/angelbroking/order/v1/getOrderBook`
- **Trade book**: `GET /rest/secure/angelbroking/order/v1/getTradeBook`
- **Positions**: `GET /rest/secure/angelbroking/order/v1/getPosition`
- **LTP**: `POST /rest/secure/angelbroking/order/v1/getLtpData`

> Rate limits exist per endpoint (per‑second and per‑minute). Build retries/backoff and never spam login.

---

## 4) Normalized Order Model → SmartAPI

| Our Field                | SmartAPI Field     | Example / Notes |
|---|---|---|
| `symbol`                | `tradingsymbol`    | `"SBIN-EQ"` |
| `symbolToken`           | `symboltoken`      | e.g., `"3045"` from instrument master |
| `side`                  | `transactiontype`  | `"BUY"` / `"SELL"` |
| `exchange`              | `exchange`         | `"NSE"`, `"BSE"`, `"NFO"`, ... |
| `type`                  | `ordertype`        | `"MARKET"`, `"LIMIT"`, `"SL"`, `"SL-M"` |
| `product`               | `producttype`      | `"CNC"`, `"INTRADAY"`, `"MARGIN"`, `"NRML"` |
| `qty`                   | `quantity`         | integer |
| `price`                | `price`            | for LIMIT/SL |
| `triggerPrice`         | `triggerprice`     | for `SL`/`SL-M` |
| `duration`             | `duration`         | `"DAY"` typical |
| `squareOff` (target)   | `squareoff`        | if supported for your variety |
| `stopLoss`             | `stoploss`         | SL price/points based on context |

### 4.1 Place
```js
await smart.placeOrder({
  variety: "NORMAL",
  tradingsymbol: "SBIN-EQ",
  symboltoken: "3045",
  transactiontype: "BUY",
  exchange: "NSE",
  ordertype: "LIMIT",
  producttype: "INTRADAY",
  duration: "DAY",
  price: "780.50",
  triggerprice: "0",
  stoploss: "0",
  squareoff: "0",
  quantity: "10"
});
```

### 4.2 Modify (price/qty/SL/TP)
```js
await smart.modifyOrder({
  orderid: "20250922000123",
  variety: "NORMAL",
  tradingsymbol: "SBIN-EQ",
  symboltoken: "3045",
  exchange: "NSE",
  ordertype: "LIMIT",
  producttype: "INTRADAY",
  duration: "DAY",
  price: "781.00",
  quantity: "10",
  stoploss: "775.00",
  squareoff: "790.00"
});
```

### 4.3 Cancel / Close
```js
await smart.cancelOrder({ variety: "NORMAL", orderid: "20250922000123" });
```
- **Cancel** pending orders via API above.  
- **Close** an executed position by placing a **counter MARKET** order (SELL for long / BUY for short) or by modifying target/SL legs where applicable.

### 4.4 Update SL/TP after Fill
- If bracket/robo legs exist, **modify** the SL/TP child order(s).  
- If no child legs, **submit new SL/SL‑M** (and/or target) with correct product/exchange and keep **only one active SL** per position to avoid rejects.

---

## 5) Instruments & Symbols

- Most order endpoints require `symboltoken`. Keep an **instrument master** (CSV/DB) and map from human symbol → token + exchange.  
- Validate symbols before placing orders to reduce failures.  
- Use `getLtpData` to fetch quick prices for guards (optional).

---

## 6) WebSockets (ticks & order updates)

- **Market data (old/new)** websockets accept `feed_token` or `jwtToken` depending on client.  
- **Order updates**: use the **order feed** socket and update our local order/position state machine.

**New JS order feed sample**
```js
const { WebSocketClient } = require('smartapi-javascript');

const ws = new WebSocketClient({
  clientcode: process.env.ANGEL_CLIENT,
  jwttoken:   jwtToken,
  apikey:     process.env.ANGEL_API_KEY,
  feedtype:   "order_feed"
});

await ws.connect();
await ws.fetchData("subscribe", "order_feed");
ws.on("tick", (msg) => broker.handleOrderEvent(JSON.parse(msg)));
```

---

## 7) Adapter Skeleton (TypeScript)

```ts
export interface AngelOneConfig {
  apiKey: string;
  clientCode: string;
  pinOrPassword: string;
  totpSecret?: string; // if we generate locally
  jwt?: string;
  refreshToken?: string;
}

export interface Broker {
  login(cfg: AngelOneConfig): Promise<void>;
  logout(): Promise<void>;
  place(o: PlaceOrder): Promise<string>;
  modify(o: ModifyOrder): Promise<void>;
  cancel(orderId: string, variety?: string): Promise<void>;
  squareOff(pos: Position): Promise<void>;
  setSLTP(posId: string, sl?: number, tp?: number): Promise<void>;
  orders(): Promise<Order[]>;
  trades(): Promise<Trade[]>;
  positions(): Promise<Position[]>;
  subscribeOrderFeed(cb: (evt: OrderEvent) => void): Promise<void>;
}
```

**Login helper (Node)**
```ts
import { SmartAPI } from "smartapi-javascript";
import * as otp from "otplib";

export async function login(cfg: AngelOneConfig) {
  const client = new SmartAPI({ api_key: cfg.apiKey });
  const totp = cfg.totpSecret ? otp.authenticator.generate(cfg.totpSecret) : process.env.ANGEL_TOTP!;
  const session = await client.generateSession(cfg.clientCode, cfg.pinOrPassword, totp);
  return { client, jwt: session.data.jwtToken, refresh: session.data.refreshToken };
}
```

---

## 8) Common Errors & Fixes

### “Request Rejected” (HTML page)
- Almost always **wrong host** (use `apiconnect.angelone.in`), **missing headers**, or corporate **WAF** rules.  
- Ensure all headers in §0 are present, and Content‑Type is `application/json`.  
- If you proxy through another service, pass headers unmodified.

### “Invalid Token” on secure endpoints
- You didn’t include `Authorization: Bearer <jwtToken>` or token expired.  
- Regenerate session (fresh TOTP) and retry.

### 4xx on order APIs
- Duplicated exits (multiple SLs), banned scrips, insufficient funds/margins.  
- Surface the **API message** to the user; don’t hide broker error text.

### Rate‑limit errors
- Add exponential backoff and **never** loop login. Cache tokens in memory.  
- Space out market‑data and order book calls.

### 2025 policy notes
- Some features may require **static IP allow‑listing** for production. If blocked unexpectedly post‑login, check your SmartAPI portal announcements and configure an allow‑listed IP where required.

---

## 9) Security & Compliance

- Never log API keys, PIN, or TOTP secrets.  
- Store TOTP seed in a secure vault/keychain and generate at runtime.  
- Rotate API keys periodically; segregate **paper** vs **live** creds.  
- HTTPS only; validate TLS certs; pin hosts where feasible.

---

## 10) Test Checklist (do these in paper/sandbox first)

- [ ] Login succeeds and `getProfile` returns user details.  
- [ ] Place LIMIT order — appears in **Order Book**.  
- [ ] Modify price/qty on **pending** order.  
- [ ] Cancel pending order.  
- [ ] After **filled**, update SL/TP (modify child leg or submit fresh exit).  
- [ ] Order updates stream on **order_feed** socket and update UI.  
- [ ] Handle token expiry → re‑login without user-visible errors.

---

## 11) Troubleshooting Snippets

**Python httpx — robust JSON guard**
```python
import httpx, json

BASE  = "https://apiconnect.angelone.in"
LOGIN = "/rest/auth/angelbroking/user/v1/loginByPassword"

headers = {
  "Accept": "application/json",
  "Content-Type": "application/json",
  "X-UserType": "USER",
  "X-SourceID": "WEB",
  "X-PrivateKey": API_KEY,
  "X-ClientLocalIP": "127.0.0.1",
  "X-ClientPublicIP": "127.0.0.1",
  "X-MACAddress": "AA-BB-CC-DD-EE-FF",
}

r = httpx.post(f"{BASE}{LOGIN}", json={
  "clientcode": CLIENT,
  "password": PIN_OR_PWD,
  "totp": TOTP_6_DIGIT,
}, headers=headers, timeout=10.0)

if "application/json" not in (r.headers.get("content-type","").lower()):
    raise RuntimeError(f"Non-JSON response: {r.status_code} {r.text[:200]}")

data = r.json()
if not data.get("status", False):
    raise RuntimeError(f"Login failed: {data}")
```

**Node axios — place order**
```js
import axios from "axios";

const BASE = "https://apiconnect.angelone.in";
const PATH = "/rest/secure/angelbroking/order/v1/placeOrder";

const headers = {
  "Accept": "application/json",
  "Content-Type": "application/json",
  "X-UserType": "USER",
  "X-SourceID": "WEB",
  "X-PrivateKey": process.env.ANGEL_API_KEY,
  "Authorization": `Bearer ${jwt}`,
};

await axios.post(`${BASE}${PATH}`, {
  variety: "NORMAL",
  tradingsymbol: "SBIN-EQ",
  symboltoken: "3045",
  transactiontype: "BUY",
  exchange: "NSE",
  ordertype: "LIMIT",
  producttype: "INTRADAY",
  duration: "DAY",
  price: "780.50",
  triggerprice: "0",
  squareoff: "0",
  stoploss: "0",
  quantity: "10"
}, { headers });
```

---

## 12) Appendix — Useful Links

- SmartAPI JS SDK (methods & websockets)  
- SmartAPI Python SDK (routes in source)  
- SmartAPI Knowledge Center & Forum for endpoint/headers/rate-limits  
- SmartAPI TOTP & login notes

---

**End of document.**
