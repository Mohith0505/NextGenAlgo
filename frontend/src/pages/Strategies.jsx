import { useEffect, useMemo, useRef, useState } from "react";
import DataTable from "../components/DataTable";
import NotificationBanner from "../components/NotificationBanner";
import Loader from "../components/Loader";
import { api } from "../api";
import { formatCurrency, formatDateTime } from "../utils/formatters";

const ORDER_SIDES = ["BUY", "SELL"];
const ORDER_TYPES = ["MARKET", "LIMIT"];

const defaultParams = {
  symbol: "NIFTY",
  side: "BUY",
  lots: 1,
  total_lots: 1,
  lot_size: 1,
  lotSize: 1,
  order_type: "MARKET",
  orderType: "MARKET",
};

const defaultStartForm = {
  executionGroupId: "",
  symbol: "NIFTY",
  side: "BUY",
  lots: "1",
  lotSize: "1",
  orderType: "MARKET",
  price: "",
  takeProfit: "",
  stopLoss: "",
};

function normalizeStrategyParams(raw) {
  if (!raw) {
    return {};
  }
  if (typeof raw === "string") {
    try {
      const parsed = JSON.parse(raw);
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? { ...parsed } : {};
    } catch (error) {
      return {};
    }
  }
  if (typeof raw === "object" && !Array.isArray(raw)) {
    return { ...raw };
  }
  return {};
}

function buildExecutionParamsFromForm(form) {
  const payload = {};
  if (form.executionGroupId) {
    payload.execution_group_id = form.executionGroupId;
    payload.executionGroupId = form.executionGroupId;
    payload.group_id = form.executionGroupId;
  }
  if (form.symbol) {
    payload.symbol = form.symbol;
  }
  if (form.side) {
    payload.side = form.side.toUpperCase();
  }
  const lotsValue = Number(form.lots);
  if (Number.isFinite(lotsValue) && lotsValue > 0) {
    const lotsInt = Math.round(lotsValue);
    payload.lots = lotsInt;
    payload.total_lots = lotsInt;
  }
  const lotSizeValue = Number(form.lotSize);
  if (Number.isFinite(lotSizeValue) && lotSizeValue > 0) {
    const lotSizeInt = Math.round(lotSizeValue);
    payload.lot_size = lotSizeInt;
    payload.lotSize = lotSizeInt;
  }
  if (form.orderType) {
    const orderType = form.orderType.toUpperCase();
    payload.order_type = orderType;
    payload.orderType = orderType;
  }
  const priceValue = Number(form.price);
  if (form.price && Number.isFinite(priceValue) && priceValue > 0) {
    payload.price = priceValue;
  }
  const takeProfitValue = Number(form.takeProfit);
  if (form.takeProfit && Number.isFinite(takeProfitValue) && takeProfitValue > 0) {
    payload.take_profit = takeProfitValue;
    payload.takeProfit = takeProfitValue;
  }
  const stopLossValue = Number(form.stopLoss);
  if (form.stopLoss && Number.isFinite(stopLossValue) && stopLossValue > 0) {
    payload.stop_loss = stopLossValue;
    payload.stopLoss = stopLossValue;
  }
  return payload;
}

function buildExecutionConfiguration(strategy, overrides, executionGroups) {
  const params = normalizeStrategyParams(strategy.params);
  const configuration = { ...params, source: "ui" };
  if (overrides) {
    Object.assign(configuration, buildExecutionParamsFromForm(overrides));
  }

  let groupId =
    configuration.execution_group_id || configuration.executionGroupId || configuration.group_id || "";
  if (!groupId && executionGroups.length === 1) {
    groupId = executionGroups[0].id;
  }
  const errors = [];
  if (!groupId) {
    errors.push("Choose an execution group before starting the strategy.");
  } else {
    const exists = executionGroups.length === 0 || executionGroups.some((group) => group.id === groupId);
    if (!exists) {
      errors.push("The selected execution group is no longer available.");
    }
  }
  if (groupId) {
    configuration.execution_group_id = groupId;
    configuration.executionGroupId = groupId;
    configuration.group_id = groupId;
  }

  const symbol = configuration.symbol;
  if (!symbol) {
    errors.push("Symbol is required for execution.");
  } else {
    configuration.symbol = symbol.toUpperCase();
  }

  const sideValue = (configuration.side || "BUY").toString().toUpperCase();
  if (!ORDER_SIDES.includes(sideValue)) {
    errors.push("Order side must be BUY or SELL.");
  } else {
    configuration.side = sideValue;
  }

  const lotsValue = Number(configuration.lots ?? configuration.total_lots);
  if (!Number.isFinite(lotsValue) || lotsValue <= 0) {
    errors.push("Lots must be a positive number.");
  } else {
    const lotsInt = Math.round(lotsValue);
    configuration.lots = lotsInt;
    configuration.total_lots = lotsInt;
  }

  const lotSizeValue = Number(configuration.lot_size ?? configuration.lotSize ?? 1);
  if (!Number.isFinite(lotSizeValue) || lotSizeValue <= 0) {
    errors.push("Lot size must be a positive number.");
  } else {
    const lotSizeInt = Math.round(lotSizeValue);
    configuration.lot_size = lotSizeInt;
    configuration.lotSize = lotSizeInt;
  }

  const orderTypeValue = (configuration.order_type || configuration.orderType || "MARKET").toString().toUpperCase();
  if (!ORDER_TYPES.includes(orderTypeValue)) {
    errors.push("Order type must be MARKET or LIMIT.");
  }
  configuration.order_type = orderTypeValue;
  configuration.orderType = orderTypeValue;

  if (configuration.price !== undefined) {
    const priceValue = Number(configuration.price);
    if (!Number.isFinite(priceValue) || priceValue <= 0) {
      errors.push("Price must be a positive number when provided.");
    } else {
      configuration.price = priceValue;
    }
  }
  if (configuration.take_profit !== undefined || configuration.takeProfit !== undefined) {
    const takeProfitValue = Number(configuration.take_profit ?? configuration.takeProfit);
    if (!Number.isFinite(takeProfitValue) || takeProfitValue <= 0) {
      errors.push("Take profit must be a positive number when provided.");
    } else {
      configuration.take_profit = takeProfitValue;
      configuration.takeProfit = takeProfitValue;
    }
  }
  if (configuration.stop_loss !== undefined || configuration.stopLoss !== undefined) {
    const stopLossValue = Number(configuration.stop_loss ?? configuration.stopLoss);
    if (!Number.isFinite(stopLossValue) || stopLossValue <= 0) {
      errors.push("Stop loss must be a positive number when provided.");
    } else {
      configuration.stop_loss = stopLossValue;
      configuration.stopLoss = stopLossValue;
    }
  }

  return { configuration, errors };
}

function Strategies() {
  const [strategies, setStrategies] = useState([]);
  const [executionGroups, setExecutionGroups] = useState([]);
  const [executionGroupsError, setExecutionGroupsError] = useState("");
  const [executionGroupsLoading, setExecutionGroupsLoading] = useState(true);
  const [startForm, setStartForm] = useState(defaultStartForm);
  const [startMode, setStartMode] = useState("paper");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [creating, setCreating] = useState(false);
  const [formState, setFormState] = useState({
    name: "Opening Range Breakout",
    type: "built-in",
    params: JSON.stringify(defaultParams, null, 2),
  });
  const [selectedStrategyId, setSelectedStrategyId] = useState(null);
  const [detailsRefreshKey, setDetailsRefreshKey] = useState(0);
  const [logsState, setLogsState] = useState({ loading: false, entries: [], error: "" });
  const [perfState, setPerfState] = useState({ loading: false, data: null, error: "" });
  const prefetchedStrategyId = useRef(null);

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

  async function loadExecutionGroups() {
    try {
      setExecutionGroupsLoading(true);
      setExecutionGroupsError("");
      const groups = await api.getExecutionGroups();
      setExecutionGroups(groups ?? []);
    } catch (err) {
      setExecutionGroups([]);
      setExecutionGroupsError(err.message);
    } finally {
      setExecutionGroupsLoading(false);
    }
  }


  useEffect(() => {
    loadExecutionGroups();
  }, []);

  useEffect(() => {
    if (executionGroups.length === 0) {
      return;
    }
    setStartForm((prev) =>
      prev.executionGroupId ? prev : { ...prev, executionGroupId: executionGroups[0].id },
    );
  }, [executionGroups]);

  useEffect(() => {
    if (!selectedStrategyId) {
      return;
    }
    const strategy = strategies.find((item) => item.id === selectedStrategyId);
    if (!strategy) {
      return;
    }
    const params = normalizeStrategyParams(strategy.params);
    setStartForm((prev) => {
      if (prefetchedStrategyId.current === strategy.id && prev.executionGroupId) {
        return prev;
      }
      prefetchedStrategyId.current = strategy.id;
      const lotsValue = Number(params.lots ?? params.total_lots ?? prev.lots ?? defaultStartForm.lots);
      const lotSizeValue = Number(
        params.lot_size ?? params.lotSize ?? prev.lotSize ?? defaultStartForm.lotSize,
      );
      return {
        executionGroupId:
          params.execution_group_id ||
          params.executionGroupId ||
          params.group_id ||
          prev.executionGroupId ||
          executionGroups[0]?.id ||
          "",
        symbol: params.symbol || prev.symbol || defaultStartForm.symbol,
        side: (params.side || prev.side || defaultStartForm.side).toString().toUpperCase(),
        lots: String(Number.isFinite(lotsValue) && lotsValue > 0 ? lotsValue : 1),
        lotSize: String(Number.isFinite(lotSizeValue) && lotSizeValue > 0 ? lotSizeValue : 1),
        orderType: (
          params.order_type ||
          params.orderType ||
          prev.orderType ||
          defaultStartForm.orderType
        )
          .toString()
          .toUpperCase(),
        price:
          params.price !== undefined && params.price !== null
            ? String(params.price)
            : prev.price || defaultStartForm.price,
        takeProfit:
          params.take_profit !== undefined && params.take_profit !== null
            ? String(params.take_profit)
            : params.takeProfit !== undefined && params.takeProfit !== null
              ? String(params.takeProfit)
              : prev.takeProfit || defaultStartForm.takeProfit,
        stopLoss:
          params.stop_loss !== undefined && params.stop_loss !== null
            ? String(params.stop_loss)
            : params.stopLoss !== undefined && params.stopLoss !== null
              ? String(params.stopLoss)
              : prev.stopLoss || defaultStartForm.stopLoss,
      };
    });
  }, [selectedStrategyId, strategies, executionGroups]);

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
      let paramsObject = { ...buildExecutionParamsFromForm(startForm) };
      if (formState.params.trim()) {
        let parsed;
        try {
          parsed = JSON.parse(formState.params);
        } catch (err) {
          throw new Error("Params must be valid JSON.");
        }
        if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
          throw new Error("Params must be a JSON object.");
        }
        paramsObject = { ...paramsObject, ...parsed };
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
    const overrides = selectedStrategyId === strategy.id ? startForm : null;
    const { configuration, errors: configErrors } = buildExecutionConfiguration(
      strategy,
      overrides,
      executionGroups,
    );
    if (configErrors.length > 0) {
      setError(configErrors.join(" "));
      return;
    }
    try {
      await api.startStrategy(strategy.id, {
        mode: startMode,
        configuration,
      });
      setMessage(`Started ${strategy.name} in ${startMode} mode.`);
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
              <button
                className="btn primary small"
                type="button"
                onClick={() => handleStart(row)}
                disabled={executionGroupsLoading || executionGroups.length === 0}
              >
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
            <span>Default Start Mode</span>
            <select value={startMode} onChange={(event) => setStartMode(event.target.value)}>
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
              <h3>Execution Settings</h3>
              {executionGroupsError && (
                <NotificationBanner type="danger" message={executionGroupsError} />
              )}
              {executionGroupsLoading ? (
                <Loader label="Loading execution groups" />
              ) : executionGroups.length === 0 ? (
                <p className="muted">Create an execution group to enable live or paper runs.</p>
              ) : null}
              <div className="form-grid" style={{ marginTop: "1rem" }}>
                <label className="form-control">
                  <span>Execution Group</span>
                  <select
                    value={startForm.executionGroupId}
                    onChange={(event) =>
                      setStartForm((prev) => ({ ...prev, executionGroupId: event.target.value }))
                    }
                    disabled={executionGroupsLoading || executionGroups.length === 0}
                  >
                    <option value="">Select group...</option>
                    {executionGroups.map((group) => (
                      <option key={group.id} value={group.id}>
                        {group.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="form-control">
                  <span>Symbol</span>
                  <input
                    type="text"
                    value={startForm.symbol}
                    onChange={(event) =>
                      setStartForm((prev) => ({ ...prev, symbol: event.target.value.toUpperCase() }))
                    }
                  />
                </label>
                <label className="form-control">
                  <span>Side</span>
                  <select
                    value={startForm.side}
                    onChange={(event) =>
                      setStartForm((prev) => ({ ...prev, side: event.target.value }))
                    }
                  >
                    {ORDER_SIDES.map((side) => (
                      <option key={side} value={side}>
                        {side}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="form-control">
                  <span>Lots</span>
                  <input
                    type="number"
                    min="1"
                    value={startForm.lots}
                    onChange={(event) =>
                      setStartForm((prev) => ({ ...prev, lots: event.target.value }))
                    }
                  />
                </label>
                <label className="form-control">
                  <span>Lot Size</span>
                  <input
                    type="number"
                    min="1"
                    value={startForm.lotSize}
                    onChange={(event) =>
                      setStartForm((prev) => ({ ...prev, lotSize: event.target.value }))
                    }
                  />
                </label>
                <label className="form-control">
                  <span>Order Type</span>
                  <select
                    value={startForm.orderType}
                    onChange={(event) =>
                      setStartForm((prev) => ({ ...prev, orderType: event.target.value }))
                    }
                  >
                    {ORDER_TYPES.map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="form-control">
                  <span>Price (limit)</span>
                  <input
                    type="number"
                    min="0"
                    step="0.05"
                    value={startForm.price}
                    onChange={(event) =>
                      setStartForm((prev) => ({ ...prev, price: event.target.value }))
                    }
                    placeholder="Optional"
                  />
                </label>
                <label className="form-control">
                  <span>Take Profit</span>
                  <input
                    type="number"
                    min="0"
                    step="0.05"
                    value={startForm.takeProfit}
                    onChange={(event) =>
                      setStartForm((prev) => ({ ...prev, takeProfit: event.target.value }))
                    }
                    placeholder="Optional"
                  />
                </label>
                <label className="form-control">
                  <span>Stop Loss</span>
                  <input
                    type="number"
                    min="0"
                    step="0.05"
                    value={startForm.stopLoss}
                    onChange={(event) =>
                      setStartForm((prev) => ({ ...prev, stopLoss: event.target.value }))
                    }
                    placeholder="Optional"
                  />
                </label>
                <label className="form-control">
                  <span>Run Mode</span>
                  <select value={startMode} onChange={(event) => setStartMode(event.target.value)}>
                    <option value="paper">Paper</option>
                    <option value="backtest">Backtest</option>
                    <option value="live">Live</option>
                  </select>
                </label>
              </div>

              <h3 style={{ marginTop: "1.5rem" }}>Latest Run</h3>
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

