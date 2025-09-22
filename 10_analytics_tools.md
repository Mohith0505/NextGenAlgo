# 10 – Analytics & Tools

The **Next-Gen Algo Terminal** includes advanced analytics to help traders identify trends, support/resistance zones, volatility regimes, and PnL performance.  
These tools run in real time using live option chain, OI, IV, and tick data.

---

## 📊 Analytics Categories

1. **Market Bias & Confidence**
2. **Option Chain Analysis**
3. **Open Interest (OI) Analytics**
4. **Greeks & Volatility Tools**
5. **PnL Dashboards**
6. **Custom Reports & Exports**

---

## 1. Market Bias & Confidence

### Bias Detection
- Input: Option Chain (ATM ± 5 strikes).
- Metrics:
  - OI buildup (CE vs PE).
  - OI Change vs Total OI.
  - Delta spread (ATM ±1).
  - IV comparison (CE vs PE).
- Output:  
  - Bias = Bullish / Bearish / Neutral.  
  - Confidence Score (0–100%).

### Confidence Boosts
- High PCR (Put/Call Ratio).  
- Strong OI imbalance at ATM.  
- Consistent Delta spread signal.  

---

## 2. Option Chain Analysis

### Option Chain Table (Frontend)
- Columns: OI, ChgOI, IV, Delta, LTP (CE & PE).  
- ATM auto-detection.  
- Highlight support/resistance zones:
  - **High Put OI below LTP → Support**.
  - **High Call OI above LTP → Resistance**.
- Built-in strategy triggers (straddles, spreads).

### OI Heatmap
- Visual heatmap of OI by strike.  
- Color-coded for resistance (CE heavy) and support (PE heavy).

---

## 3. Open Interest (OI) Analytics

### OI Map
- Aggregated OI across strikes.
- Shows buildup vs unwinding.

### PCR (Put/Call Ratio)
- Formula: `Total Put OI / Total Call OI`.
- Interpretation:
  - >1 = Bullish.
  - <1 = Bearish.

### OI Shifts
- Track ChgOI intraday.
- Alerts for large build-up/unwinding.

---

## 4. Greeks & Volatility Tools

### Greeks (per strike)
- Delta → directional sensitivity.
- Gamma → speed of Delta change.
- Theta → time decay.
- Vega → sensitivity to IV.
- Rho → sensitivity to interest rates.

### IV (Implied Volatility)
- Calculated separately for CE & PE.
- Average IV across ATM ±5 strikes.
- IV Rank/Percentile:
  - IV Rank = position of current IV vs 1Y range.
  - Helps decide when to sell (high IV) or buy (low IV).

### Volatility Regime (Gamma Exposure)
- Gamma regime signals:
  - **Positive Gamma** → stable, mean-reverting.
  - **Negative Gamma** → volatile, trending.

---

## 5. PnL Dashboards

### Trade-wise PnL
- Every trade’s entry, exit, realized PnL.

### Strategy PnL
- Aggregated PnL per strategy.
- Equity curve plot.

### Account PnL
- Consolidated across all brokers/accounts.
- Daily/weekly/monthly stats.

### RMS-linked PnL
- RMS rules (max loss/profit lock) visualized.
- Alerts when nearing thresholds.

---

## 6. Custom Reports & Exports

### Reports
- Daily PnL summary.
- Weekly market review (OI trends, PCR, bias stats).
- Strategy performance.

### Export Formats
- CSV → Excel import.
- PDF → formatted reports with charts.
- JSON → for API users.

---

## 🔄 Data Flow for Analytics

1. Live option chain & tick data streamed into Redis/Kafka.  
2. Analytics service processes in real time.  
3. Results stored in Postgres (summaries) + Timescale (raw data).  
4. Frontend pulls via REST + WebSocket.  

---

## ✅ Summary
Analytics in the Next-Gen Algo Terminal will provide:
- **Bias & confidence scoring** for directional view.  
- **OI heatmaps & Greeks** for intraday decisions.  
- **PnL dashboards** for traders & admins.  
- **Reports & exports** for compliance and performance review.  

This ensures traders can make **data-driven decisions** with institutional-grade tools.

---
