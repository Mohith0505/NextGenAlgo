import { useEffect, useMemo, useState } from "react";
import Sparkline from "../components/Sparkline";
import BarChart from "../components/BarChart";
import HeatmapGrid from "../components/HeatmapGrid";
import DataTable from "../components/DataTable";
import Loader from "../components/Loader";
import NotificationBanner from "../components/NotificationBanner";
import { api, getAuthToken, API_BASE_URL } from "../api";
import { formatCurrency, formatNumber } from "../utils/formatters";

function buildHeatmapCells(dailyPnl = []) {
  return dailyPnl.map((point) => ({
    label: new Date(point.date).toLocaleDateString(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
    }),
    value: point.realized_pnl ?? 0,
  }));
}

function buildLatencySeries(summary) {
  if (!summary) return [];
  const fields = [
    { label: "Average", value: summary.avg_execution_latency_ms },
    { label: "P50", value: summary.p50_execution_latency_ms },
    { label: "P95", value: summary.p95_execution_latency_ms },
  ];
  return fields.filter((field) => typeof field.value === "number" && Number.isFinite(field.value));
}

function buildLegStatusRows(summary) {
  if (!summary) return [];
  const entries = Object.entries(summary.execution_leg_status_counts ?? {});
  return entries.map(([status, count]) => ({
    status: status.replace(/_/g, " ").replace(/\w/g, (char) => char.toUpperCase()),
    count,
  }));
}

const reportCards = [
  {
    title: "Daily PnL Snapshot",
    description: "Export day-level realised PnL with trade counts for compliance or investor briefings.",
    cta: "Download CSV",
    endpoint: "/api/analytics/exports/daily-pnl",
    filename: "daily_pnl.csv",
    format: "csv",
  },
  {
    title: "Latency Audit",
    description: "Summarise execution wait times by percentile to validate broker SLAs each week.",
    cta: "Download Summary",
    endpoint: "/api/analytics/exports/latency-summary",
    filename: "latency_summary.json",
    format: "json",
  },
  {
    title: "Leg Outcome Review",
    description: "Break down leg status distribution and identify brokers with frequent retries or failures.",
    cta: "Download JSON",
    endpoint: "/api/analytics/exports/leg-status",
    filename: "leg_status.json",
    format: "json",
  },
];

function AnalyticsInsights() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dashboard, setDashboard] = useState(null);
  const [exportMessage, setExportMessage] = useState("");

  useEffect(() => {
    let cancelled = false;
    let timer;

    async function load() {
      try {
        setLoading(true);
        setError("");
        const response = await api.getAnalyticsDashboard();
        if (!cancelled) {
          setDashboard(response);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    timer = window.setInterval(() => {
      load();
    }, 30000);

    return () => {
      cancelled = true;
      if (timer) {
        window.clearInterval(timer);
      }
    };
  }, []);

  const summary = dashboard?.summary;

  const sparklineData = useMemo(() => buildHeatmapCells(dashboard?.daily_pnl), [dashboard]);
  const latencySeries = useMemo(() => buildLatencySeries(summary), [summary]);
  const legStatusRows = useMemo(() => buildLegStatusRows(summary), [summary]);

  const legStatusColumns = [
    { key: "status", label: "Leg Status" },
    { key: "count", label: "Count" },
  ];

  async function handleExport(card) {
    try {
      setExportMessage(`Preparing ${card.title}...`);
      const token = getAuthToken();
      const response = await fetch(`${API_BASE_URL}${card.endpoint}`, {
        headers: {
          Accept: card.format === "csv" ? "text/csv" : "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      });
      if (!response.ok) {
        throw new Error(`Export failed with status ${response.status}`);
      }

      if (card.format === "csv") {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = card.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        const json = await response.json();
        const blob = new Blob([JSON.stringify(json, null, 2)], { type: "application/json" });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = card.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }

      setExportMessage(`${card.title} ready (${card.filename})`);
    } catch (err) {
      setExportMessage(err.message || 'Failed to prepare export');
    }
  }

  return (
    <section className="page">
      <h1>Analytics Insights</h1>
      <p>
        Prototype dashboards layering raw metrics, percentile telemetry, and exportable reports. These views help align
        execution performance with the Phase 2 analytics roadmap.
      </p>

      {error && <NotificationBanner type="danger" message={error} />}
      {exportMessage && !error && (
        <NotificationBanner type="info" message={exportMessage} />
      )}

      {loading ? (
        <Loader label="Loading analytics" />
      ) : (
        <>
          <div className="chart-grid">
            <div className="chart-card">
              <h2>Daily PnL Heatmap</h2>
              <HeatmapGrid
                cells={sparklineData}
                formatValue={(value) => formatCurrency(value)}
              />
              <p className="muted small">Warmer tiles indicate stronger realised PnL contribution.</p>
            </div>
            <div className="chart-card">
              <h2>PnL Sparkline</h2>
              <Sparkline data={sparklineData.map((cell, index) => ({ x: index, y: cell.value }))} height={120} />
              <p className="muted small">Visualises recent PnL momentum at a glance.</p>
            </div>
            <div className="chart-card">
              <h2>Latency Percentiles</h2>
              <BarChart
                data={latencySeries}
                formatValue={(value) => `${value.toFixed(1)} ms`}
              />
              <p className="muted small">Compare average, median, and tail latency across execution runs.</p>
            </div>
          </div>

          <div className="chart-card" style={{ marginTop: "2rem" }}>
            <h2>Leg Outcome Overview</h2>
            <DataTable
              columns={legStatusColumns}
              data={legStatusRows.map((row) => ({
                status: row.status,
                count: formatNumber(row.count, { maximumFractionDigits: 0 }),
              }))}
              emptyMessage="No leg outcomes available."
            />
          </div>

          <div className="chart-card" style={{ marginTop: "2rem" }}>
            <h2>Reports & Exports</h2>
            <div className="report-grid">
              {reportCards.map((card) => (
                <article key={card.title} className="report-card">
                  <h3>{card.title}</h3>
                  <p className="muted">{card.description}</p>
                  <button
                    className="btn small secondary"
                    type="button"
                    onClick={() => handleExport(card)}
                  >
                    {card.cta}
                  </button>
                </article>
              ))}
            </div>
          </div>
        </>
      )}
    </section>
  );
}

export default AnalyticsInsights;

