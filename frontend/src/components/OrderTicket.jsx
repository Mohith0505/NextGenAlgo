import { useEffect, useState } from "react";

const defaultForm = {
  symbol: "NIFTY24SEP24000CE",
  quantity: 1,
  side: "BUY",
  orderType: "MARKET",
  price: "",
  takeProfit: "",
  stopLoss: "",
};

function OrderTicket({
  value,
  onChange,
  onSubmit,
  submitting = false,
  submitLabel = "Submit",
  subtitle = "Enter order details and submit to send it to the broker.",
  title = "Order Ticket",
  quantityLabel = "Quantity (lots)",
  showLotSize = false,
}) {
  const [internalState, setInternalState] = useState(value ?? defaultForm);

  useEffect(() => {
    if (value) {
      setInternalState(value);
    }
  }, [value]);

  const formState = value ?? internalState;

  function setField(field, rawValue) {
    const next = { ...formState, [field]: rawValue };
    if (onChange) {
      onChange(next);
    } else {
      setInternalState(next);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit?.(formState);
  }

  return (
    <form className="order-ticket" onSubmit={handleSubmit}>
      <header>
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </header>
      <label>
        Symbol
        <input
          type="text"
          value={formState.symbol}
          onChange={(event) => setField("symbol", event.target.value)}
          required
        />
      </label>
      <div className="inline-grid">
        <label>
          Exchange (optional)
          <input
            type="text"
            placeholder="e.g., NSE"
            value={formState.exchange ?? ""}
            onChange={(e) => setField("exchange", e.target.value)}
          />
        </label>
        <label>
          Symbol Token (optional)
          <input
            type="text"
            placeholder="e.g., 3045"
            value={formState.symbolToken ?? ""}
            onChange={(e) => setField("symbolToken", e.target.value)}
          />
        </label>
      </div>
      <label>
        {quantityLabel}
        <input
          type="number"
          min="1"
          value={formState.quantity}
          onChange={(event) =>
            setField(
              "quantity",
              event.target.value === "" ? "" : Number(event.target.value)
            )
          }
          required
        />
      </label>
      {showLotSize && (
        <label>
          Lot Size
          <input
            type="number"
            min="1"
            value={formState.lotSize ?? ""}
            onChange={(event) =>
              setField(
                "lotSize",
                event.target.value === "" ? "" : Number(event.target.value)
              )
            }
            required
          />
        </label>
      )}
      <label>
        Side
        <select value={formState.side} onChange={(event) => setField("side", event.target.value)}>
          <option value="BUY">Buy</option>
          <option value="SELL">Sell</option>
        </select>
      </label>
      <label>
        Order Type
        <select
          value={formState.orderType}
          onChange={(event) => setField("orderType", event.target.value)}
        >
          <option value="MARKET">Market</option>
          <option value="LIMIT">Limit</option>
        </select>
      </label>
      {formState.orderType === "LIMIT" && (
        <label>
          Limit Price
          <input
            type="number"
            step="0.05"
            value={formState.price}
            onChange={(event) => setField("price", event.target.value)}
            required
          />
        </label>
      )}
      <label>
        Take Profit (optional)
        <input
          type="number"
          step="0.05"
          value={formState.takeProfit}
          onChange={(event) => setField("takeProfit", event.target.value)}
        />
      </label>
      <label>
        Stop Loss (optional)
        <input
          type="number"
          step="0.05"
          value={formState.stopLoss}
          onChange={(event) => setField("stopLoss", event.target.value)}
        />
      </label>
      <button className="btn primary" type="submit" disabled={submitting}>
        {submitting ? "Submitting..." : submitLabel}
      </button>
    </form>
  );
}

export default OrderTicket;
