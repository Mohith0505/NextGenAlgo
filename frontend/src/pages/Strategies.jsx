import { useEffect, useMemo, useState } from "react";
import DataTable from "../components/DataTable";
import NotificationBanner from "../components/NotificationBanner";
import Loader from "../components/Loader";
import { api } from "../api";
import { formatCurrency, formatDateTime } from "../utils/formatters";

const defaultParams = {
  symbol: "NIFTY",
};

function Strategies() {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [creating, setCreating] = useState(false);
  const [formState, setFormState] = useState({
    name: "Opening Range Breakout",
    type: "built-in",
    params: JSON.stringify(defaultParams, null, 2),
    startMode: "paper",
  });
  const [selectedStrategyId, setSelectedStrategyId] = useState(null);
  const [detailsRefreshKey, setDetailsRefreshKey] = useState(0);
  const [logsState, setLogsState] = useState({ loading: false, entries: [], error: "" });
  const [perfState, setPerfState] = useState({ loading: false, data: null, error: "" });

  async function loadStrategies() {
    try {
      setLoading(true);
      setError("");
      const response = await api.getStrategies();
      const list = response?.strategies ?? response ?? [];
      setStrategies(list);
      if (selectedStrategyId && !list.some((strategy) => strategy.id === selectedStrategyId)) {
        setSelectedStrategyId(null);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadStrategies();
  }, []);

  useEffect(() => {
    let cancelled = false;

    if (!selectedStrategyId) {
      setLogsState({ loading: false, entries: [], error: "" });
      setPerfState({ loading: false, data: null, error: "" });
      return;
    }

    async function fetchDetails(strategyId) {
      setLogsState({ loading: true, entries: [], error: "" });
      setPerfState((prev) => ({ ...prev, loading: true, error: "" }));
      try {
        const [logsResponse, perfResponse] = await Promise.all([
          api.getStrategyLogs(strategyId),
          api.getStrategyPerformance(strategyId),
        ]);
        if (cancelled) {
          return;
        }
        setLogsState({
          loading: false,
          entries: logsResponse?.logs ?? [],
          error: "",
        });
        setPerfState({
          loading: false,
          data: perfResponse ?? null,
          error: "",
        });
      } catch (err) {
        if (cancelled) {
          return;
        }
        const messageText = err.message || "Failed to load strategy details";
        setLogsState({ loading: false, entries: [], error: messageText });
        setPerfState({ loading: false, data: null, error: messageText });
      }
    }

    fetchDetails(selectedStrategyId);

    return () => {
      cancelled = true;
    };
  }, [selectedStrategyId, detailsRefreshKey]);

  async function handleCreate(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    setCreating(true);
    try {
      let paramsObject = {};
      if (formState.params.trim()) {
        try {
          paramsObject = JSON.parse(formState.params);
        } catch (err) {
          throw new Error("Params must be valid JSON.");
        }
      }
      await api.createStrategy({
        name: formState.name,
        type: formState.type,
        params: paramsObject,
      });
      setMessage("Strategy created successfully.");
      await loadStrategies();
    } catch (err) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  }

  async function handleStart(strategy) {
    setError("");
    setMessage("");
    try {
      await api.startStrategy(strategy.id, {
        mode: formState.startMode,
        configuration: { source: "ui" },
      });
      setMessage(`Started ${strategy.name} in ${formState.startMode} mode.`);
      await loadStrategies();
      if (selectedStrategyId === strategy.id) {
        setDetailsRefreshKey((key) => key + 1);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleStop(strategy) {
    setError("");
    setMessage("");
    try {
      await api.stopStrategy(strategy.id, { reason: "Stopped from UI" });
      setMessage(`Stopped ${strategy.name}.`);
      await loadStrategies();
      if (selectedStrategyId === strategy.id) {
        setDetailsRefreshKey((key) => key + 1);
      }
    } catch (err) {
      setError(err.message);
    }
  }

  function handleSelectDetails(strategyId) {
    if (selectedStrategyId === strategyId) {
      setSelectedStrategyId(null);
      return;
    }
    setSelectedStrategyId(strategyId);
    setDetailsRefreshKey((key) => key + 1);
  }

  function handleRefreshDetails() {
    if (selectedStrategyId) {
      setDetailsRefreshKey((key) => key + 1);
    }
  }

  const columns = [
    {
      key: "name",
      label: "Strategy",
      render: (row) => (
        <div>
          <strong>{row.name}</strong>
          <div className="muted small">{row.type}</div>
        </div>
      ),
    },
    {
      key: "status",
      label: "Status",
      render: (row) => row.status?.toUpperCase() ?? "-",
    },
    {
      key: "last_mode",
      label: "Last Run",
      render: (row) => (
        <div>
          <div>{row.latest_run?.mode ?? "-"}</div>
          <div className="muted small">
            {row.latest_run ? formatDateTime(row.latest_run.started_at) : ""}
          </div>
        </div>
      ),
    },
    {
      key: "pnl",
      label: "Lifetime PnL",
      render: (row) => {
        const pnl = row.latest_run?.result_metrics?.pnl;
        return pnl !== undefined ? formatCurrency(pnl) : "-";
      },
    },
    {
      key: "actions",
      label: "Actions",
      render: (row) => {
        const isSelected = selectedStrategyId === row.id;
        return (
          <div className="table-actions">
            {row.status === "active" ? (
              <button className="btn secondary small" type="button" onClick={() => handleStop(row)}>
                Stop
              </button>
            ) : (
              <button className="btn primary small" type="button" onClick={() => handleStart(row)}>
                Start
              </button>
            )}
            <button
              className="btn ghost small"
              type="button"
              onClick={() => handleSelectDetails(row.id)}
            >
              {isSelected ? "Hide" : "Details"}
            </button>
          </div>
        );
      },
    },
  ];

  const selectedStrategy = useMemo(
    () => strategies.find((strategy) => strategy.id === selectedStrategyId) || null,
    [strategies, selectedStrategyId],
  );

  const latestMetrics = selectedStrategy?.latest_run?.result_metrics ?? {};

  return (
    <section className="page">
      <h1>Strategies Workspace</h1>
      <p>Create, monitor, and control strategies using the paper trading environment.</p>

      {error && <NotificationBanner type="danger" message={error} />}
      {message && <NotificationBanner type="info" message={message} />}

      <div className="card">
        <h2>Create Strategy</h2>
        <form className="form-grid" onSubmit={handleCreate}>
          <label className="form-control">
            <span>Name</span>
            <input
              type="text"
              value={formState.name}
              onChange={(event) => setFormState((prev) => ({ ...prev, name: event.target.value }))}
              required
            />
          </label>
          <label className="form-control">
            <span>Type</span>
            <select
              value={formState.type}
              onChange={(event) => setFormState((prev) => ({ ...prev, type: event.target.value }))}
            >
              <option value="built-in">Built-in</option>
              <option value="custom">Custom</option>
              <option value="connector">Connector</option>
            </select>
          </label>
          <label className="form-control">
            <span>Parameters (JSON)</span>
            <textarea
              rows={4}
              value={formState.params}
              onChange={(event) => setFormState((prev) => ({ ...prev, params: event.target.value }))}
            />
          </label>
          <label className="form-control">
            <span>Start Mode</span>
            <select
              value={formState.startMode}
              onChange={(event) => setFormState((prev) => ({ ...prev, startMode: event.target.value }))}
            >
              <option value="paper">Paper</option>
              <option value="backtest">Backtest</option>
              <option value="live">Live</option>
            </select>
          </label>
          <button className="btn primary" type="submit" disabled={creating}>
            {creating ? "Creating..." : "Create Strategy"}
          </button>
        </form>
      </div>

      {loading ? (
        <Loader label="Loading strategies" />
      ) : (
        <DataTable
          columns={columns}
          data={strategies}
          emptyMessage="Create a strategy to get started."
        />
      )}

      {selectedStrategy && (
        <div className="card" style={{ marginTop: "2rem" }}>
          <div className="card-header">
            <h2>{selectedStrategy.name}</h2>
            <div className="card-actions">
              <button
                className="btn secondary small"
                type="button"
                onClick={handleRefreshDetails}
                disabled={logsState.loading || perfState.loading}
              >
                {logsState.loading || perfState.loading ? "Refreshing" : "Refresh"}
              </button>
              <button className="btn ghost small" type="button" onClick={() => setSelectedStrategyId(null)}>
                Close
              </button>
            </div>
          </div>

          <div className="grid two" style={{ marginTop: "1.5rem" }}>
            <div>
              <h3>Latest Run</h3>
              {selectedStrategy.latest_run ? (
                <dl className="description-list">
                  <div>
                    <dt>Status</dt>
                    <dd>{selectedStrategy.latest_run.status?.toUpperCase()}</dd>
                  </div>
                  <div>
                    <dt>Mode</dt>
                    <dd>{selectedStrategy.latest_run.mode}</dd>
                  </div>
                  <div>
                    <dt>Started</dt>
                    <dd>{formatDateTime(selectedStrategy.latest_run.started_at)}</dd>
                  </div>
                  <div>
                    <dt>Finished</dt>
                    <dd>
                      {selectedStrategy.latest_run.finished_at
                        ? formatDateTime(selectedStrategy.latest_run.finished_at)
                        : "-"}
                    </dd>
                  </div>
                  {latestMetrics.execution_run_id && (
                    <div>
                      <dt>Execution Run</dt>
                      <dd>{latestMetrics.execution_run_id}</dd>
                    </div>
                  )}
                  {latestMetrics.pnl !== undefined && (
                    <div>
                      <dt>PnL</dt>
                      <dd>{formatCurrency(Number(latestMetrics.pnl) || 0)}</dd>
                    </div>
                  )}
                  {latestMetrics.orders !== undefined && (
                    <div>
                      <dt>Orders</dt>
                      <dd>{latestMetrics.orders}</dd>
                    </div>
                  )}
                  {latestMetrics.total_lots !== undefined && (
                    <div>
                      <dt>Total Lots</dt>
                      <dd>{latestMetrics.total_lots}</dd>
                    </div>
                  )}
                  {latestMetrics.latency_ms !== undefined && (
                    <div>
                      <dt>Avg Latency</dt>
                      <dd>{`${Number(latestMetrics.latency_ms).toFixed(2)} ms`}</dd>
                    </div>
                  )}
                </dl>
              ) : (
                <p className="muted">No runs recorded yet.</p>
              )}

              <h3 style={{ marginTop: "1.5rem" }}>Performance</h3>
              {perfState.error && <NotificationBanner type="danger" message={perfState.error} />}
              {perfState.loading ? (
                <Loader label="Loading performance" />
              ) : perfState.data ? (
                <dl className="description-list">
                  <div>
                    <dt>Lifetime PnL</dt>
                    <dd>{formatCurrency(perfState.data.lifetime_pnl)}</dd>
                  </div>
                  <div>
                    <dt>Total Trades</dt>
                    <dd>{perfState.data.total_trades}</dd>
                  </div>
                  <div>
                    <dt>Last Run Status</dt>
                    <dd>{perfState.data.last_run?.status?.toUpperCase() ?? "-"}</dd>
                  </div>
                </dl>
              ) : (
                <p className="muted">Performance metrics will appear after your first run.</p>
              )}
            </div>

            <div>
              <h3>Recent Logs</h3>
              {logsState.error && <NotificationBanner type="danger" message={logsState.error} />}
              {logsState.loading ? (
                <Loader label="Fetching logs" />
              ) : logsState.entries.length === 0 ? (
                <p className="muted">No logs recorded for this strategy yet.</p>
              ) : (
                <ul className="log-list">
                  {logsState.entries.map((log) => (
                    <li key={log.id} className={`log-entry level-${log.level}`}>
                      <header>
                        <span className="badge">{log.level.toUpperCase()}</span>
                        <time>{formatDateTime(log.created_at)}</time>
                      </header>
                      <p>{log.message}</p>
                      {log.context && Object.keys(log.context).length > 0 && (
                        <pre className="context">{JSON.stringify(log.context, null, 2)}</pre>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

export default Strategies;

