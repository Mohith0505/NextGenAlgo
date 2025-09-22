# 09 – Database Schema (Postgres + Timescale/ClickHouse)

The **Next-Gen Algo Terminal** uses a hybrid data layer:
- **Postgres (SQLAlchemy ORM)** → structured data (users, brokers, orders, strategies, subscriptions, logs).
- **Timescale/ClickHouse** → high-frequency market data (ticks, option chain, greeks).
- **Redis/Kafka** → caching + streaming.

---

## 🏗️ Core Tables (Postgres)

### 1. users
| Column        | Type        | Notes |
|---------------|------------|-------|
| id (PK)       | UUID       | Unique user ID |
| name          | VARCHAR    | Full name |
| email         | VARCHAR    | Unique, login |
| phone         | VARCHAR    | Optional |
| password_hash | VARCHAR    | Encrypted |
| role          | ENUM       | [owner, admin, trader, viewer] |
| status        | ENUM       | [active, inactive, blocked] |
| created_at    | TIMESTAMP  | Default now |
| updated_at    | TIMESTAMP  | Auto-update |

---

### 2. workspaces
| Column        | Type        | Notes |
|---------------|------------|-------|
| id (PK)       | UUID       | Workspace ID |
| name          | VARCHAR    | Workspace name |
| owner_id (FK) | UUID → users.id | Owner |
| created_at    | TIMESTAMP  | |

---

### 3. brokers
| Column        | Type        | Notes |
|---------------|------------|-------|
| id (PK)       | UUID       | Broker account ID |
| user_id (FK)  | UUID → users.id | Owner |
| broker_name   | VARCHAR    | e.g., "Angel One" |
| client_code   | VARCHAR    | Broker login ID |
| session_token | VARCHAR    | Encrypted |
| status        | ENUM       | [connected, expired, error] |
| created_at    | TIMESTAMP  | |

---

### 4. accounts
| Column        | Type        | Notes |
|---------------|------------|-------|
| id (PK)       | UUID       | Account ID |
| broker_id (FK)| UUID → brokers.id | Broker |
| margin        | DECIMAL    | Current margin |
| currency      | VARCHAR    | e.g., INR |
| created_at    | TIMESTAMP  | |

---

### 5. orders
| Column        | Type        | Notes |
|---------------|------------|-------|
| id (PK)       | UUID       | Order ID |
| account_id (FK)| UUID → accounts.id | Account |
| strategy_id (FK)| UUID → strategies.id (nullable) | Linked strategy |
| symbol        | VARCHAR    | e.g., NIFTY23SEP25000CE |
| side          | ENUM       | [BUY, SELL] |
| qty           | INT        | Lots |
| order_type    | ENUM       | [MARKET, LIMIT] |
| price         | DECIMAL    | Order price |
| status        | ENUM       | [PENDING, FILLED, CANCELLED, REJECTED] |
| broker_order_id | VARCHAR | Broker ref |
| tp_price      | DECIMAL    | Take profit |
| sl_price      | DECIMAL    | Stop loss |
| created_at    | TIMESTAMP  | |
| updated_at    | TIMESTAMP  | |

---

### 6. trades
| Column        | Type        | Notes |
|---------------|------------|-------|
| id (PK)       | UUID       | Trade ID |
| order_id (FK) | UUID → orders.id | Linked order |
| fill_price    | DECIMAL    | Execution price |
| qty           | INT        | Filled qty |
| pnl           | DECIMAL    | Realized PnL |
| timestamp     | TIMESTAMP  | |

---

### 7. positions
| Column        | Type        | Notes |
|---------------|------------|-------|
| id (PK)       | UUID       | Position ID |
| account_id (FK)| UUID → accounts.id | Account |
| symbol        | VARCHAR    | e.g., BANKNIFTY FUT |
| qty           | INT        | Current net qty |
| avg_price     | DECIMAL    | Average entry |
| pnl           | DECIMAL    | Running PnL |
| updated_at    | TIMESTAMP  | |

---

### 8. strategies
| Column        | Type        | Notes |
|---------------|------------|-------|
| id (PK)       | UUID       | Strategy ID |
| user_id (FK)  | UUID → users.id | Owner |
| name          | VARCHAR    | Strategy name |
| type          | ENUM       | [built-in, custom, connector] |
| params        | JSONB      | Config params |
| status        | ENUM       | [active, stopped] |
| created_at    | TIMESTAMP  | |

---

### 9. rms_rules
| Column        | Type        | Notes |
|---------------|------------|-------|
| id (PK)       | UUID       | RMS ID |
| user_id (FK)  | UUID → users.id | Owner |
| max_loss      | DECIMAL    | Daily max loss |
| max_lots      | INT        | Max lots allowed |
| profit_lock   | DECIMAL    | Lock-in profit |
| trailing_sl   | DECIMAL    | TSL in points |
| created_at    | TIMESTAMP  | |

---

### 10. subscriptions
| Column        | Type        | Notes |
|---------------|------------|-------|
| id (PK)       | UUID       | Subscription ID |
| user_id (FK)  | UUID → users.id | Subscriber |
| plan          | ENUM       | [trial, monthly, yearly] |
| start_date    | DATE       | |
| end_date      | DATE       | |
| status        | ENUM       | [active, expired, cancelled] |
| payment_ref   | VARCHAR    | Razorpay ref |

---

### 11. logs
| Column        | Type        | Notes |
|---------------|------------|-------|
| id (PK)       | UUID       | Log ID |
| user_id (FK)  | UUID → users.id | |
| type          | ENUM       | [auth, order, rms, broker, system] |
| message       | TEXT       | Details |
| created_at    | TIMESTAMP  | |

---

## 📊 Market Data Tables (Timescale/ClickHouse)

### ticks
| Column     | Type        | Notes |
|------------|------------|-------|
| id (PK)    | BIGSERIAL   | Auto ID |
| symbol     | VARCHAR     | NIFTY, BANKNIFTY |
| ltp        | DECIMAL     | Last price |
| bid        | DECIMAL     | Bid |
| ask        | DECIMAL     | Ask |
| volume     | BIGINT      | |
| timestamp  | TIMESTAMP   | |

### option_chain
| Column     | Type        | Notes |
|------------|------------|-------|
| id (PK)    | BIGSERIAL   | Auto ID |
| symbol     | VARCHAR     | NIFTY, BANKNIFTY |
| expiry     | DATE        | Expiry date |
| strike     | DECIMAL     | Strike price |
| call_oi    | BIGINT      | Call OI |
| call_chgoi | BIGINT      | Call change OI |
| call_iv    | DECIMAL     | Call IV |
| call_delta | DECIMAL     | Call Delta |
| call_ltp   | DECIMAL     | Call LTP |
| put_oi     | BIGINT      | Put OI |
| put_chgoi  | BIGINT      | Put change OI |
| put_iv     | DECIMAL     | Put IV |
| put_delta  | DECIMAL     | Put Delta |
| put_ltp    | DECIMAL     | Put LTP |
| timestamp  | TIMESTAMP   | |

---

## ✅ Summary
- **Postgres** → structured relational data (users, orders, trades, strategies, RMS, subscriptions).  
- **Timescale/ClickHouse** → high-frequency tick + option chain storage.  
- **Redis/Kafka** → real-time streams + caching.  

This hybrid schema supports **fast execution + deep analytics + compliance logging**.

---
