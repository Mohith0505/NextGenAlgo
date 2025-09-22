import { useEffect, useMemo, useState } from "react";
import NotificationBanner from "../components/NotificationBanner";
import StatCard from "../components/StatCard";
import DataTable from "../components/DataTable";
import Loader from "../components/Loader";
import { api } from "../api";
import { useAuth } from "../hooks/useAuth";
import { formatCurrency, formatNumber } from "../utils/formatters";

function formatStatusLabel(value) {
  if (!value) {
    return "-";
  }
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const { user } = useAuth();
  const displayName = (user?.name && user.name.trim()) || user?.email || "Trader";

  useEffect(() => {
    let mounted = true;
    let timer;

    async function load() {
      try {
        setLoading(true);
        const response = await api.getAnalyticsDashboard();
        if (mounted) setAnalytics(response);
      } catch (err) {
        if (mounted) setError(err.message);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    load();
    timer = window.setInterval(() => {
      load();
    }, 30000);

    return () => {
      mounted = false;
      if (timer) {
        window.clearInterval(timer);
      }
    };
  }, []);

  const summary = analytics?.summary;
  const legStatusSummary = useMemo(() => {
    if (!summary) {
      return "N/A";
    }
    const entries = Object.entries(summary.execution_leg_status_counts ?? {});
    if (!entries.length) {
      return "N/A";
    }
    return entries
      .map(([status, count]) => `${formatStatusLabel(status)}: ${count}`)
      .join(" / ");
  }, [summary]);

  const legStatusRows = useMemo(() => {
    if (!summary) {
      return [];
    }
    const entries = Object.entries(summary.execution_leg_status_counts ?? {});
    return entries.map(([status, count]) => ({
      status: formatStatusLabel(status),
      count,
    }));
  }, [summary]);

  const legStatusColumns = [
    { key: "status", label: "Leg Status" },
    { key: "count", label: "Count" },
  ];

  const dailyPnlSparkData = useMemo(() => {
    const points = analytics?.daily_pnl ?? [];
    if (!points.length) {
      return [];
    }
    return points.map((point, index) => ({
      x: index,
      y: point.realized_pnl ?? 0,
      label: point.date,
    }));
  }, [analytics]);

  const latencyBarData = useMemo(() => {
    if (!summary) {
      return [];
    }
    const entries = [
      { label: "Average", value: summary.avg_execution_latency_ms },
      { label: "P50", value: summary.p50_execution_latency_ms },
      { label: "P95", value: summary.p95_execution_latency_ms },
    ].filter((item) => typeof item.value === "number" && Number.isFinite(item.value));
    return entries;
  }, [summary]);

  const legStatusChartData = useMemo(() =>
    legStatusRows.map((row) => ({ label: row.status, value: row.count })),
  [legStatusRows]);

  const stats = summary
    ? [
        {
          label: "Realised PnL",
          value: formatCurrency(summary.realized_pnl),
        },
        {
          label: "Unrealised PnL",
          value: formatCurrency(summary.unrealized_pnl),
        },
        {
          label: "Today's PnL",
          value: formatCurrency(summary.today_realized_pnl),
        },
        {
          label: "Open Positions",
          value: formatNumber(summary.open_positions, { maximumFractionDigits: 0 }),
        },
        {
          label: "Execution Runs",
          value: formatNumber(summary.execution_run_count, { maximumFractionDigits: 0 }),
        },
        {
          label: "Failed Runs",
          value: formatNumber(summary.failed_execution_runs, { maximumFractionDigits: 0 }),
        },
        {
          label: "Avg Exec Latency",
          value:
            typeof summary.avg_execution_latency_ms === "number"
              ? `${summary.avg_execution_latency_ms.toFixed(1)} ms`
              : "N/A",
        },
        {
          label: "P50 Exec Latency",
          value:
            typeof summary.p50_execution_latency_ms === "number"
              ? `${summary.p50_execution_latency_ms.toFixed(1)} ms`
              : "N/A",
        },
        {
          label: "P95 Exec Latency",
          value:
            typeof summary.p95_execution_latency_ms === "number"
              ? `${summary.p95_execution_latency_ms.toFixed(1)} ms`
              : "N/A",
        },
        {
          label: "Leg Outcomes",
          value: legStatusSummary,
        },
      ]
    : [];

  const positionColumns = [
    { key: "symbol", label: "Instrument" },
    { key: "qty", label: "Qty" },
    { key: "avg_price", label: "Avg Price" },
    { key: "pnl", label: "PnL" },
    { key: "updated_at", label: "Updated" },
  ];

  const openPositions = (analytics?.open_positions ?? []).map((position) => ({
    symbol: position.symbol,
    qty: position.qty,
    avg_price: formatCurrency(position.avg_price),
    pnl: formatCurrency(position.pnl),
    updated_at: position.updated_at ? new Date(position.updated_at).toLocaleTimeString() : "-",
  }));

  return (
    <section className="page">
      <h1>Welcome, {displayName}!</h1>
      <p>
        Central hub summarising live accounts, analytics, and positions. Data below reflects the
        seeded Phase 1 environment.
      </p>

      {error && <NotificationBanner type="danger" message={error} />}
      {!error && analytics && (
        <NotificationBanner
          type="info"
          message="Analytics sourced from the local paper trading run."
        />
      )}

      {loading ? (
        <Loader label="Loading analytics" />
      ) : (
        <>
          <h2>Dashboard Overview</h2>
          <div className="stat-grid">
            {stats.map((stat) => (
              <StatCard key={stat.label} {...stat} />
            ))}
          </div>

          {summary && (
            <div className="chart-grid">
              <div className="chart-card">
                <h2>Daily PnL Trend</h2>
                <Sparkline data={dailyPnlSparkData} height={120} />
                <p className="muted small">
                  {dailyPnlSparkData.length ? `Showing ${dailyPnlSparkData.length} sessions of realised PnL` : 'No PnL history available.'}
                </p>
              </div>
              <div className="chart-card">
                <h2>Execution Latency (ms)</h2>
                <BarChart
                  data={latencyBarData}
                  formatValue={(value) => `${value.toFixed(1)} ms`}
                />
                <p className="muted small">Captured from recent execution runs.</p>
              </div>
              <div className="chart-card">
                <h2>Leg Status Distribution</h2>
                <BarChart
                  data={legStatusChartData}
                  formatValue={(value) => formatNumber(value, { maximumFractionDigits: 0 })}
                />
                <p className="muted small">Counts aggregated from execution leg outcomes.</p>
              </div>
            </div>
          )}

          <h2>Open Positions</h2>
          <DataTable
            columns={positionColumns}
            data={openPositions}
            emptyMessage="No active positions."
          />

          <h2>Execution Leg Outcomes</h2>
          <DataTable
            columns={legStatusColumns}
            data={legStatusRows}
            emptyMessage="No execution legs recorded."
          />
        </>
      )}
    </section>
  );
}

export default Dashboard;



