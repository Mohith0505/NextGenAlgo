import { useEffect, useState } from "react";
import StatCard from "../components/StatCard";
import DataTable from "../components/DataTable";
import NotificationBanner from "../components/NotificationBanner";
import Loader from "../components/Loader";
import { api } from "../api";
import { formatCurrency, formatNumber } from "../utils/formatters";

const configFields = [
  { key: "max_daily_loss", label: "Max Daily Loss" },
  { key: "max_daily_lots", label: "Max Daily Lots" },
  { key: "exposure_limit", label: "Exposure Limit" },
  { key: "margin_buffer_pct", label: "Margin Buffer %" },
];

function RiskManagement() {
  const [config, setConfig] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [updating, setUpdating] = useState(false);
  const [formState, setFormState] = useState({});

  async function loadData() {
    try {
      setLoading(true);
      const [configRes, statusRes] = await Promise.all([
        api.getRmsConfig(),
        api.getRmsStatus(),
      ]);
      setConfig(configRes);
      setStatus(statusRes);
      setFormState({
        max_daily_loss: configRes?.max_daily_loss ?? "",
        max_daily_lots: configRes?.max_daily_lots ?? "",
        exposure_limit: configRes?.exposure_limit ?? "",
        margin_buffer_pct: configRes?.margin_buffer_pct ?? "",
      });
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
      const payload = Object.fromEntries(
        Object.entries(formState).filter(([, value]) => value !== "" && value !== null)
      );
      Object.keys(payload).forEach((key) => {
        const numeric = Number(payload[key]);
        if (!Number.isNaN(numeric)) {
          payload[key] = numeric;
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

  const alertRows = (status?.alerts ?? []).map((alert, index) => ({
    index: index + 1,
    message: alert,
  }));

  const alertColumns = [
    { key: "index", label: "#" },
    { key: "message", label: "Alert" },
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
      ]
    : [];

  return (
    <section className="page">
      <h1>Risk Management (RMS)</h1>
      <p>Live guardrails protecting capital, with configurable thresholds per environment.</p>

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
                {configFields.map((field) => (
                  <label key={field.key} className="form-control">
                    <span>{field.label}</span>
                    <input
                      type="number"
                      step="0.01"
                      value={formState[field.key] ?? ""}
                      onChange={(event) =>
                        setFormState((prev) => ({
                          ...prev,
                          [field.key]: event.target.value,
                        }))
                      }
                    />
                  </label>
                ))}
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
            </div>
          </div>

          <h2>Alerts</h2>
          <DataTable
            columns={alertColumns}
            data={alertRows}
            emptyMessage="RMS has not raised alerts yet."
          />
        </>
      )}
    </section>
  );
}

export default RiskManagement;
