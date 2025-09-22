import { useEffect, useState } from "react";
import StatCard from "../components/StatCard";
import DataTable from "../components/DataTable";
import NotificationBanner from "../components/NotificationBanner";
import Loader from "../components/Loader";
import { api } from "../api";
import { formatCurrency, formatNumber } from "../utils/formatters";

const configFields = [
  { key: "max_loss", label: "Max Loss (Cumulative)", type: "number", step: "0.01" },
  { key: "max_lots", label: "Max Lots / Order", type: "number", step: "1" },
  { key: "profit_lock", label: "Profit Lock", type: "number", step: "0.01" },
  { key: "trailing_sl", label: "Trailing Stop", type: "number", step: "0.01" },
  { key: "max_daily_loss", label: "Max Daily Loss", type: "number", step: "0.01" },
  { key: "max_daily_lots", label: "Max Daily Lots", type: "number", step: "1" },
  { key: "drawdown_limit", label: "Drawdown Limit", type: "number", step: "0.01" },
  { key: "exposure_limit", label: "Exposure Limit", type: "number", step: "0.01" },
  { key: "margin_buffer_pct", label: "Margin Buffer %", type: "number", step: "0.01" },
  { key: "auto_square_off_enabled", label: "Auto Square-Off", type: "boolean" },
  { key: "auto_square_off_buffer_pct", label: "Square-Off Buffer %", type: "number", step: "0.01" },
  { key: "auto_hedge_enabled", label: "Auto Hedge", type: "boolean" },
  { key: "auto_hedge_ratio", label: "Hedge Ratio", type: "number", step: "0.01" },
  { key: "notify_email", label: "Email Alerts", type: "boolean" },
  { key: "notify_telegram", label: "Telegram Alerts", type: "boolean" },
];

function RiskManagement() {
  const [config, setConfig] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [updating, setUpdating] = useState(false);
  const [formState, setFormState] = useState({});
  const [automationRunning, setAutomationRunning] = useState(false);
  const [automationResult, setAutomationResult] = useState([]);
  const [hasRunAutomations, setHasRunAutomations] = useState(false);

  async function loadData() {
    try {
      setLoading(true);
      const [configRes, statusRes] = await Promise.all([
        api.getRmsConfig(),
        api.getRmsStatus(),
      ]);
      setConfig(configRes);
      setStatus(statusRes);
      const nextState = {};
      configFields.forEach(({ key, type }) => {
        const value = configRes?.[key];
        if (type === "boolean") {
          nextState[key] = Boolean(value);
        } else {
          nextState[key] = value ?? "";
        }
      });
      setFormState(nextState);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    setUpdating(true);
    try {
      const payload = {};
      configFields.forEach(({ key, type }) => {
        const value = formState[key];
        if (type === "boolean") {
          if (value !== undefined) {
            payload[key] = Boolean(value);
          }
        } else if (value !== "" && value !== null && value !== undefined) {
          const numeric = Number(value);
          if (!Number.isNaN(numeric)) {
            payload[key] = numeric;
          }
        }
      });
      const response = await api.updateRmsConfig(payload);
      setConfig(response);
      setMessage("RMS configuration updated.");
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setUpdating(false);
    }
  }

  async function handleRunAutomations() {
    setError("");
    setMessage("");
    setAutomationRunning(true);
    try {
      const response = await api.enforceRms();
      const actions = response?.actions ?? [];
      setAutomationResult(actions);
      setHasRunAutomations(true);
      setMessage(actions.length ? "Automations executed." : "No automations triggered.");
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setAutomationRunning(false);
    }
  }

  const alertRows = (status?.alerts ?? []).map((alert, index) => ({
    index: index + 1,
    message: alert,
  }));

  const automationRows = (status?.automations ?? []).map((entry, index) => ({
    index: index + 1,
    message: entry,
  }));

  const tableColumns = [
    { key: "index", label: "#" },
    { key: "message", label: "Detail" },
  ];

  const statusCards = status
    ? [
        { label: "Day PnL", value: formatCurrency(status.day_pnl) },
        {
          label: "Lots Traded Today",
          value: formatNumber(status.total_lots_today, { maximumFractionDigits: 0 }),
        },
        { label: "Notional Exposure", value: formatCurrency(status.notional_exposure) },
        { label: "Available Margin", value: formatCurrency(status.available_margin) },
        status.loss_remaining != null
          ? { label: "Loss Remaining", value: formatCurrency(status.loss_remaining) }
          : null,
        status.lots_remaining != null
          ? {
              label: "Lots Remaining",
              value: formatNumber(status.lots_remaining, { maximumFractionDigits: 0 }),
            }
          : null,
      ].filter(Boolean)
    : [];

  return (
    <section className="page">
      <h1>Risk Management (RMS)</h1>
      <p>
        Configure automated guardrails that defend capital before, during, and after every trade. Update thresholds
        and trigger one-touch automations when needed.
      </p>

      {error && <NotificationBanner type="danger" message={error} />}
      {message && <NotificationBanner type="info" message={message} />}

      {loading ? (
        <Loader label="Loading RMS data" />
      ) : (
        <>
          <div className="card-grid">
            <div className="card">
              <h2>Configuration</h2>
              <form className="form-grid" onSubmit={handleSubmit}>
                {configFields.map((field) => {
                  const fieldValue = formState[field.key];
                  if (field.type === "boolean") {
                    return (
                      <label key={field.key} className="form-control toggle">
                        <span>{field.label}</span>
                        <input
                          type="checkbox"
                          checked={Boolean(fieldValue)}
                          onChange={(event) =>
                            setFormState((prev) => ({
                              ...prev,
                              [field.key]: event.target.checked,
                            }))
                          }
                        />
                      </label>
                    );
                  }

                  return (
                    <label key={field.key} className="form-control">
                      <span>{field.label}</span>
                      <input
                        type="number"
                        step={field.step ?? "0.01"}
                        value={fieldValue ?? ""}
                        onChange={(event) =>
                          setFormState((prev) => ({
                            ...prev,
                            [field.key]: event.target.value,
                          }))
                        }
                      />
                    </label>
                  );
                })}
                <button className="btn primary" type="submit" disabled={updating}>
                  {updating ? "Saving..." : "Save Settings"}
                </button>
              </form>
            </div>
            <div className="card">
              <h2>Current Status</h2>
              <div className="stat-grid compact">
                {statusCards.map((card) => (
                  <StatCard key={card.label} {...card} />
                ))}
              </div>
              <div className="automation-actions">
                <button
                  className="btn secondary"
                  type="button"
                  onClick={handleRunAutomations}
                  disabled={automationRunning}
                >
                  {automationRunning ? "Running..." : "Run Automations"}
                </button>
                {hasRunAutomations ? (
                  automationResult.length ? (
                    <ul className="automation-list">
                      {automationResult.map((entry, index) => (
                        <li key={index}>{entry}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="muted">Automations ran cleanly; no action required.</p>
                  )
                ) : (
                  <p className="muted">Automations have not been executed in this session.</p>
                )}
              </div>
            </div>
          </div>

          <h2>Active Alerts</h2>
          <DataTable
            columns={tableColumns}
            data={alertRows}
            emptyMessage="RMS has not raised alerts yet."
          />

          <h2>Automation Signals</h2>
          <DataTable
            columns={tableColumns}
            data={automationRows}
            emptyMessage="No automation triggers are active."
          />
        </>
      )}
    </section>
  );
}

export default RiskManagement;
