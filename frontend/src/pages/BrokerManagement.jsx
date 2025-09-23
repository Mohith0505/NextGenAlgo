import { useCallback, useEffect, useMemo, useState } from "react";
import DataTable from "../components/DataTable";
import Loader from "../components/Loader";
import NotificationBanner from "../components/NotificationBanner";
import { api } from "../api";
import { formatCurrency, formatDateTime, formatNumber } from "../utils/formatters";

const structuredBrokerFields = {
  angel_one: [
    {
      key: "api_key",
      label: "API Key",
      type: "text",
      autoComplete: "off",
    },
    {
      key: "password",
      label: "Password / PIN",
      type: "password",
      autoComplete: "current-password",
    },
    {
      key: "totp_secret",
      label: "TOTP Secret (Base32)",
      type: "password",
      autoComplete: "one-time-code",
      helper: "Paste the 32-character base32 seed from SmartAPI. It is stored encrypted for reuse.",
    },
  ],
};

const jsonCredentialDefaults = {
  paper_trading: () => ({ client_code: "demo" }),
};

const brokerClientCodeDefaults = {
  paper_trading: "demo",
};

const DEFAULT_BROKER = "paper_trading";

function buildStructuredState() {
  return Object.entries(structuredBrokerFields).reduce((acc, [broker, fields]) => {
    acc[broker] = fields.reduce((inner, field) => {
      inner[field.key] = "";
      return inner;
    }, {});
    return acc;
  }, {});
}

function buildFormStateForBroker(brokerName) {
  const hasStructured = Boolean(structuredBrokerFields[brokerName]);
  const credentialsFactory = jsonCredentialDefaults[brokerName];
  return {
    broker_name: brokerName,
    client_code: brokerClientCodeDefaults[brokerName] ?? "",
    credentials: hasStructured
      ? ""
      : JSON.stringify(credentialsFactory ? credentialsFactory() : {}, null, 2),
  };
}

function BrokerManagement() {
  const [supported, setSupported] = useState([]);
  const [brokers, setBrokers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formState, setFormState] = useState(() => buildFormStateForBroker(DEFAULT_BROKER));
  const [structuredCredentials, setStructuredCredentials] = useState(buildStructuredState);
  const [activePortfolioBrokerId, setActivePortfolioBrokerId] = useState(null);
  const [positionsData, setPositionsData] = useState({ net: [], day: [] });
  const [holdingsData, setHoldingsData] = useState({ holdings: [], summary: null });
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [portfolioError, setPortfolioError] = useState("");
  const [convertDraft, setConvertDraft] = useState(null);
  const [convertSubmitting, setConvertSubmitting] = useState(false);
  const [convertMessage, setConvertMessage] = useState("");
  const [convertError, setConvertError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        setLoading(true);
        const [supportedRes, brokersRes] = await Promise.all([
          api.getSupportedBrokers(),
          api.getBrokers(),
        ]);
        if (!mounted) return;
        setSupported(supportedRes ?? []);
        setBrokers(brokersRes?.brokers ?? brokersRes ?? []);
      } catch (err) {
        if (mounted) setError(err.message);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (supported.length === 0) return;
    setFormState((prev) => {
      if (supported.includes(prev.broker_name)) {
        return prev;
      }
      const fallback = supported.includes(DEFAULT_BROKER) ? DEFAULT_BROKER : supported[0];
      return buildFormStateForBroker(fallback);
    });
  }, [supported]);

  const connectedBrokers = useMemo(
    () => (brokers ?? []).filter((item) => (item.status ?? "").toLowerCase() === "connected"),
    [brokers]
  );

  useEffect(() => {
    if (connectedBrokers.length === 0) {
      setActivePortfolioBrokerId(null);
      setPositionsData({ net: [], day: [] });
      setHoldingsData({ holdings: [], summary: null });
      setPortfolioLoading(false);
      setPortfolioError("");
      setConvertDraft(null);
      return;
    }
    if (
      !activePortfolioBrokerId ||
      !connectedBrokers.some((item) => item.id === activePortfolioBrokerId)
    ) {
      setActivePortfolioBrokerId(connectedBrokers[0].id);
    }
  }, [connectedBrokers, activePortfolioBrokerId]);

  useEffect(() => {
    setConvertDraft(null);
    setConvertMessage("");
    setConvertError("");
  }, [activePortfolioBrokerId]);

  const loadPortfolio = useCallback(
    async (brokerId, { silent = false } = {}) => {
      if (!brokerId) return;
      if (!silent) setPortfolioLoading(true);
      setPortfolioError("");
      try {
        const [positionsRes, holdingsRes] = await Promise.all([
          api.getBrokerPositions(brokerId),
          api.getBrokerHoldings(brokerId),
        ]);
        setPositionsData({
          net: Array.isArray(positionsRes?.net) ? positionsRes.net : [],
          day: Array.isArray(positionsRes?.day) ? positionsRes.day : [],
        });
        setHoldingsData({
          holdings: Array.isArray(holdingsRes?.holdings) ? holdingsRes.holdings : [],
          summary: holdingsRes?.summary ?? null,
        });
      } catch (err) {
        setPortfolioError(err?.message ?? "Failed to load portfolio data");
      } finally {
        if (!silent) setPortfolioLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    if (!activePortfolioBrokerId) {
      return;
    }
    loadPortfolio(activePortfolioBrokerId);
  }, [activePortfolioBrokerId, loadPortfolio]);

  const usingStructuredFields = Boolean(structuredBrokerFields[formState.broker_name]);
  const activeStructuredFields = structuredBrokerFields[formState.broker_name] ?? [];
  const activeStructuredValues = structuredCredentials[formState.broker_name] ?? {};

  const selectedPortfolioBroker =
    connectedBrokers.find((item) => item.id === activePortfolioBrokerId) ?? null;

  async function refreshConnectedBrokers() {
    const brokersRes = await api.getBrokers();
    setBrokers(brokersRes?.brokers ?? brokersRes ?? []);
  }

  function resetStructuredValues(brokerName) {
    const fields = structuredBrokerFields[brokerName];
    if (!fields) return;
    setStructuredCredentials((prev) => ({
      ...prev,
      [brokerName]: fields.reduce((acc, field) => {
        acc[field.key] = "";
        return acc;
      }, {}),
    }));
  }

  function handleBrokerChange(value) {
    setStatusMessage("");
    setError("");
    setFormState(buildFormStateForBroker(value));
  }

  function handleStructuredInputChange(key, value) {
    const brokerName = formState.broker_name;
    setStructuredCredentials((prev) => ({
      ...prev,
      [brokerName]: {
        ...(prev[brokerName] ?? {}),
        [key]: value,
      },
    }));
  }

  function handlePortfolioBrokerChange(event) {
    const value = event.target.value;
    setActivePortfolioBrokerId(value ? value : null);
  }

  async function handleRefreshPortfolio() {
    if (!activePortfolioBrokerId) return;
    setConvertMessage("");
    setConvertError("");
    await loadPortfolio(activePortfolioBrokerId);
  }

  function beginConversionForPosition(position) {
    if (!position) return;
    const productRaw = position.product_type ?? position.producttype ?? "";
    const productUpper = typeof productRaw === "string" ? productRaw.toUpperCase() : String(productRaw || "");
    const netQtyValue = Number(position.net_qty ?? position.netqty ?? position.quantity ?? 0);
    const fallbackQty = Number(position.quantity ?? 1);
    const quantityCandidate =
      Number.isFinite(netQtyValue) && Math.abs(netQtyValue) > 0
        ? Math.abs(netQtyValue)
        : Number.isFinite(fallbackQty) && Math.abs(fallbackQty) > 0
        ? Math.abs(fallbackQty)
        : 1;
    const transactionType = Number.isFinite(netQtyValue) && netQtyValue < 0 ? "SELL" : "BUY";
    setConvertDraft({
      exchange: position.exchange ?? "",
      tradingsymbol: position.tradingsymbol ?? "",
      symbol_token: position.symbol_token ?? position.symboltoken ?? "",
      symbol_name: position.symbol_name ?? position.symbolname ?? "",
      instrument_type: position.instrument_type ?? position.instrumenttype ?? "",
      old_product_type: productUpper || "DELIVERY",
      new_product_type: productUpper === "DELIVERY" ? "INTRADAY" : productUpper || "INTRADAY",
      transaction_type: transactionType,
      quantity: Math.max(1, Math.trunc(quantityCandidate)),
      type: "DAY",
    });
    setConvertMessage("");
    setConvertError("");
  }

  function handleConvertFieldChange(key, value) {
    setConvertDraft((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  function cancelConvertDraft() {
    setConvertDraft(null);
    setConvertError("");
    setConvertMessage("");
  }

  async function handleConvertSubmit(event) {
    event.preventDefault();
    if (!convertDraft || !activePortfolioBrokerId) return;
    setConvertSubmitting(true);
    setConvertError("");
    setConvertMessage("");
    try {
      const quantityValue = Number(convertDraft.quantity);
      if (!Number.isFinite(quantityValue) || quantityValue <= 0) {
        throw new Error("Quantity must be greater than zero");
      }
      const payload = {
        exchange: convertDraft.exchange,
        symboltoken: convertDraft.symbol_token,
        tradingsymbol: convertDraft.tradingsymbol,
        oldproducttype: convertDraft.old_product_type,
        newproducttype: convertDraft.new_product_type,
        transactiontype: convertDraft.transaction_type,
        quantity: Math.trunc(Math.abs(quantityValue)),
      };
      if (convertDraft.symbol_name) payload.symbolname = convertDraft.symbol_name;
      if (convertDraft.instrument_type) payload.instrumenttype = convertDraft.instrument_type;
      if (convertDraft.type) payload.type = convertDraft.type;
      await api.convertBrokerPosition(activePortfolioBrokerId, payload);
      setConvertMessage("Position conversion request submitted successfully.");
      setConvertDraft(null);
      await loadPortfolio(activePortfolioBrokerId, { silent: true });
    } catch (err) {
      setConvertError(err?.message ?? "Failed to convert position");
    } finally {
      setConvertSubmitting(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setStatusMessage("");
    setSubmitting(true);
    try {
      let credentialsObject = {};
      if (usingStructuredFields) {
        const currentValues = structuredCredentials[formState.broker_name] ?? {};
        const missingField = activeStructuredFields.find((field) => !currentValues[field.key]?.trim());
        if (missingField) {
          throw new Error(`Please provide ${missingField.label}.`);
        }
        credentialsObject = activeStructuredFields.reduce((acc, field) => {
          const raw = currentValues[field.key] ?? "";
          acc[field.key] = field.key === "totp_secret" ? raw.replace(/\s+/g, "").toUpperCase() : raw.trim();
          return acc;
        }, {});
      } else {
        try {
          credentialsObject = JSON.parse(formState.credentials || "{}");
        } catch (err) {
          throw new Error("Credentials must be valid JSON.");
        }
      }

      const payload = {
        broker_name: formState.broker_name,
        client_code: formState.client_code,
        credentials: credentialsObject,
      };
      await api.connectBroker(payload);
      await refreshConnectedBrokers();
      setStatusMessage(`Broker ${formState.broker_name.replace(/_/g, " ")} connected.`);
      resetStructuredValues(formState.broker_name);
      setFormState(buildFormStateForBroker(formState.broker_name));
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleLogin(broker) {
    if (!broker?.id) return;
    try {
      setError("");
      setStatusMessage("");
      await api.loginBroker(broker.id);
      await refreshConnectedBrokers();
      setStatusMessage(`${broker.broker_name.replace(/_/g, " ")} logged in.`);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleLogout(broker) {
    if (!broker?.id) return;
    const confirmLogout = window.confirm(`Log out from ${broker.broker_name.replace(/_/g, " ")}?`);
    if (!confirmLogout) return;
    try {
      setError("");
      setStatusMessage("");
      await api.logoutBroker(broker.id);
      await refreshConnectedBrokers();
      setStatusMessage(`${broker.broker_name.replace(/_/g, " ")} logged out.`);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(broker) {
    if (!broker?.id) return;
    const confirmDelete = window.confirm(
      `This will remove ${broker.broker_name.replace(/_/g, " ")} from your workspace. Continue?`
    );
    if (!confirmDelete) return;
    try {
      setError("");
      setStatusMessage("");
      await api.deleteBroker(broker.id);
      await refreshConnectedBrokers();
      setStatusMessage(`${broker.broker_name.replace(/_/g, " ")} removed.`);
    } catch (err) {
      setError(err.message);
    }
  }

  const netPositions = positionsData.net ?? [];
  const dayPositions = positionsData.day ?? [];
  const holdingsRows = holdingsData.holdings ?? [];
  const holdingSummary = holdingsData.summary;

  const summaryPnLPercent = holdingSummary
    ? (() => {
        const value = holdingSummary.total_pnl_percentage ?? holdingSummary.totalpnlpercentage;
        const formatted = formatNumber(value);
        return formatted === "-" ? "-" : `${formatted}%`;
      })()
    : "-";

  const netPositionColumns = [
    { key: 'tradingsymbol', label: 'Symbol' },
    { key: 'exchange', label: 'Exchange' },
    {
      key: 'product_type',
      label: 'Product',
      render: (row) => (row.product_type ?? row.producttype ?? '-'),
    },
    {
      key: 'net_qty',
      label: 'Net Qty',
      render: (row) => formatNumber(row.net_qty ?? row.netqty ?? 0, { maximumFractionDigits: 0 }),
    },
    {
      key: 'buy_avg_price',
      label: 'Buy Avg',
      render: (row) => formatCurrency(row.buy_avg_price ?? row.buyavgprice ?? row.avgnetprice),
    },
    {
      key: 'net_price',
      label: 'Net Price',
      render: (row) => formatCurrency(row.net_price ?? row.netprice ?? row.avgnetprice),
    },
    {
      key: 'net_value',
      label: 'Net Value',
      render: (row) => formatCurrency(row.net_value ?? row.netvalue),
    },
    {
      key: 'actions',
      label: 'Action',
      render: (row) => {
        const hasToken = Boolean(row.symbol_token ?? row.symboltoken);
        return (
          <button
            className="btn tiny primary"
            type="button"
            onClick={() => beginConversionForPosition(row)}
            disabled={!hasToken}
          >
            Convert
          </button>
        );
      },
    },
  ];

  const dayPositionColumns = [
    { key: 'tradingsymbol', label: 'Symbol' },
    { key: 'exchange', label: 'Exchange' },
    {
      key: 'net_qty',
      label: 'Net Qty',
      render: (row) => formatNumber(row.net_qty ?? row.netqty ?? 0, { maximumFractionDigits: 0 }),
    },
    {
      key: 'buy_amount',
      label: 'Buy Amount',
      render: (row) => formatCurrency(row.buy_amount ?? row.buyamount),
    },
    {
      key: 'sell_amount',
      label: 'Sell Amount',
      render: (row) => formatCurrency(row.sell_amount ?? row.sellamount),
    },
  ];

  const holdingsColumns = [
    { key: 'tradingsymbol', label: 'Symbol' },
    { key: 'exchange', label: 'Exchange' },
    {
      key: 'quantity',
      label: 'Qty',
      render: (row) => formatNumber(row.quantity ?? row.qty ?? 0, { maximumFractionDigits: 0 }),
    },
    {
      key: 'average_price',
      label: 'Avg Price',
      render: (row) => formatCurrency(row.average_price ?? row.averageprice),
    },
    {
      key: 'ltp',
      label: 'LTP',
      render: (row) => formatCurrency(row.ltp),
    },
    {
      key: 'profit_and_loss',
      label: 'P&L',
      render: (row) => formatCurrency(row.profit_and_loss ?? row.profitandloss),
    },
    {
      key: 'pnl_percentage',
      label: 'PnL %',
      render: (row) => {
        const value = row.pnl_percentage ?? row.pnlpercentage;
        const formatted = formatNumber(value);
        return formatted === '-' ? '-' : `${formatted}%`;
      },
    },
  ];

  const brokerRows = useMemo(
    () =>
      brokers.map((broker) => {
        const marginTotal = (broker.accounts ?? []).reduce(
          (sum, account) => sum + Number(account.margin ?? 0),
          0
        );
        return {
          ...broker,
          display_status: broker.status?.replace(/_/g, " ") ?? "-",
          margin: formatCurrency(marginTotal),
          linked_at: formatDateTime(broker.created_at),
          account_count: broker.accounts?.length ?? 0,
        };
      }),
    [brokers]
  );

  const columns = [
    { key: "broker_name", label: "Broker" },
    { key: "client_code", label: "Client Code" },
    { key: "display_status", label: "Status" },
    { key: "account_count", label: "Accounts" },
    { key: "margin", label: "Margin" },
    {
      key: "linked_at",
      label: "Linked",
    },
    {
      key: "actions",
      label: "Actions",
      render: (row) => {
        const isConnected = row.status === "connected";
        const hasSavedCredentials = Boolean(row.has_saved_credentials);
        const loginLabel = hasSavedCredentials ? "Login" : "Relink";
        return (
          <div className="table-actions">
            {isConnected ? (
              <button className="btn small secondary" type="button" onClick={() => handleLogout(row)}>
                Logout
              </button>
            ) : (
              <button
                className="btn small primary"
                type="button"
                onClick={() => handleLogin(row)}
                disabled={!hasSavedCredentials}
                title={hasSavedCredentials ? undefined : "Provide credentials again to relink"}
              >
                {loginLabel}
              </button>
            )}
            <button className="btn small danger" type="button" onClick={() => handleDelete(row)}>
              Delete
            </button>
          </div>
        );
      },
    },
  ];

  return (
    <section className="page">
      <h1>Broker Management</h1>
      <p>
        Link adapters, review session status, and monitor account exposure. See <strong>docs/AngelOne.md</strong> for
        SmartAPI-specific onboarding guidance.
      </p>

      {error && <NotificationBanner type="danger" message={error} />}
      {statusMessage && <NotificationBanner type="info" message={statusMessage} />}

      <div className="card-grid">
        <div className="card">
          <h2>Link Broker</h2>
          <form className="form-grid" onSubmit={handleSubmit}>
            <label className="form-control">
              <span>Broker</span>
              <select
                value={formState.broker_name}
                onChange={(event) => handleBrokerChange(event.target.value)}
              >
                {supported.map((broker) => (
                  <option key={broker} value={broker}>
                    {broker.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </label>
            <label className="form-control">
              <span>Client Code</span>
              <input
                type="text"
                value={formState.client_code}
                onChange={(event) =>
                  setFormState((prev) => ({ ...prev, client_code: event.target.value }))
                }
                required
                autoComplete="username"
              />
            </label>
            {usingStructuredFields ? (
              <div >
                <p className="muted small">
                  Credentials are encrypted and stored for reuse. Delete the broker link to remove them.
                </p>
                {activeStructuredFields.map((field) => (
                  <label key={field.key} className="form-control">
                    <span>{field.label}</span>
                    <input
                      type={field.type}
                      value={activeStructuredValues[field.key] ?? ""}
                      onChange={(event) => handleStructuredInputChange(field.key, event.target.value)}
                      required
                      autoComplete={field.autoComplete}
                      maxLength={field.key === "totp_secret" ? 64 : undefined}
                    />
                    {field.helper && <small className="muted">{field.helper}</small>}
                  </label>
                ))}
              </div>
            ) : (
              <label className="form-control">
                <span>Credentials (JSON)</span>
                <textarea
                  rows={6}
                  value={formState.credentials}
                  onChange={(event) =>
                    setFormState((prev) => ({ ...prev, credentials: event.target.value }))
                  }
                />
                <small className="muted">
                  Provide broker-specific keys in JSON format. Defaults are supplied where applicable.
                </small>
              </label>
            )}
            <button className="btn primary" type="submit" disabled={submitting}>
              {submitting ? "Linking..." : "Link Broker"}
            </button>
          </form>
        </div>
        <div className="card">
          <h2>Supported Brokers</h2>
          <ul className="bullet-list">
            {supported.map((broker) => (
              <li key={broker}>{broker.replace(/_/g, " ")}</li>
            ))}
          </ul>
        </div>
      </div>


      <div className="card">
        <div className="card-header">
          <h2>Portfolio Snapshot{selectedPortfolioBroker ? ` - ${selectedPortfolioBroker.broker_name.replace(/_/g, " ")} (${selectedPortfolioBroker.client_code})` : ""}</h2>
          <div className="card-actions">
            <select
              value={activePortfolioBrokerId ?? ""}
              onChange={handlePortfolioBrokerChange}
              disabled={connectedBrokers.length === 0}
            >
              {connectedBrokers.length === 0 ? (
                <option value="">No connected brokers</option>
              ) : (
                connectedBrokers.map((broker) => (
                  <option key={broker.id} value={broker.id}>
                    {broker.broker_name.replace(/_/g, " ")} ({broker.client_code})
                  </option>
                ))
              )}
            </select>
            <button
              className="btn small secondary"
              type="button"
              onClick={handleRefreshPortfolio}
              disabled={!activePortfolioBrokerId || portfolioLoading}
            >
              {portfolioLoading ? "Refreshing..." : "Refresh"}
            </button>
          </div>
        </div>
        {connectedBrokers.length === 0 ? (
          <p className="muted">Connect a broker to view live holdings and positions.</p>
        ) : (
          <>
            {portfolioError && <NotificationBanner type="danger" message={portfolioError} />}
            {convertError && <NotificationBanner type="danger" message={convertError} />}
            {convertMessage && <NotificationBanner type="success" message={convertMessage} />}
            {portfolioLoading ? (
              <Loader label="Loading portfolio data" />
            ) : (
              <>
                <h3>Net Positions</h3>
                <DataTable
                  columns={netPositionColumns}
                  data={netPositions}
                  emptyMessage="No net positions for the selected broker."
                />
                <h3>Day Positions</h3>
                <DataTable
                  columns={dayPositionColumns}
                  data={dayPositions}
                  emptyMessage="No day positions recorded today."
                />
                <h3>Holdings</h3>
                {holdingSummary && (
                  <div className="stat-grid compact">
                    <div className="stat-card">
                      <span>Total Value</span>
                      <strong>
                        {formatCurrency(
                          holdingSummary.total_holding_value ?? holdingSummary.totalholdingvalue
                        )}
                      </strong>
                    </div>
                    <div className="stat-card">
                      <span>Invested Value</span>
                      <strong>
                        {formatCurrency(
                          holdingSummary.total_investment_value ?? holdingSummary.totalinvvalue
                        )}
                      </strong>
                    </div>
                    <div className="stat-card">
                      <span>Total P&amp;L</span>
                      <strong>
                        {formatCurrency(
                          holdingSummary.total_profit_and_loss ?? holdingSummary.totalprofitandloss
                        )}
                      </strong>
                    </div>
                    <div className="stat-card">
                      <span>PnL %</span>
                      <strong>{summaryPnLPercent}</strong>
                    </div>
                  </div>
                )}
                <DataTable
                  columns={holdingsColumns}
                  data={holdingsRows}
                  emptyMessage="No holdings for the selected broker."
                />
              </>
            )}
            {convertDraft && (
              <form className="form-grid compact" onSubmit={handleConvertSubmit}>
                <h3>Convert Position: {convertDraft.tradingsymbol}</h3>
                <label className="form-control">
                  <span>Exchange</span>
                  <input
                    type="text"
                    value={convertDraft.exchange}
                    onChange={(event) => handleConvertFieldChange('exchange', event.target.value)}
                    required
                  />
                </label>
                <label className="form-control">
                  <span>Tradingsymbol</span>
                  <input
                    type="text"
                    value={convertDraft.tradingsymbol}
                    onChange={(event) => handleConvertFieldChange('tradingsymbol', event.target.value)}
                    required
                  />
                </label>
                <label className="form-control">
                  <span>Symbol Token</span>
                  <input
                    type="text"
                    value={convertDraft.symbol_token}
                    onChange={(event) => handleConvertFieldChange('symbol_token', event.target.value)}
                    required
                  />
                </label>
                <label className="form-control">
                  <span>Old Product</span>
                  <input
                    type="text"
                    value={convertDraft.old_product_type}
                    onChange={(event) => handleConvertFieldChange('old_product_type', event.target.value)}
                    required
                  />
                </label>
                <label className="form-control">
                  <span>New Product</span>
                  <input
                    type="text"
                    value={convertDraft.new_product_type}
                    onChange={(event) => handleConvertFieldChange('new_product_type', event.target.value)}
                    required
                  />
                </label>
                <label className="form-control">
                  <span>Transaction</span>
                  <select
                    value={convertDraft.transaction_type}
                    onChange={(event) => handleConvertFieldChange('transaction_type', event.target.value)}
                    required
                  >
                    <option value="BUY">BUY</option>
                    <option value="SELL">SELL</option>
                  </select>
                </label>
                <label className="form-control">
                  <span>Quantity</span>
                  <input
                    type="number"
                    min="1"
                    value={convertDraft.quantity}
                    onChange={(event) => handleConvertFieldChange('quantity', event.target.value)}
                    required
                  />
                </label>
                <label className="form-control">
                  <span>Duration</span>
                  <input
                    type="text"
                    value={convertDraft.type ?? 'DAY'}
                    onChange={(event) => handleConvertFieldChange('type', event.target.value)}
                  />
                </label>
                <div className="form-actions">
                  <button
                    className="btn secondary"
                    type="button"
                    onClick={cancelConvertDraft}
                    disabled={convertSubmitting}
                  >
                    Cancel
                  </button>
                  <button className="btn primary" type="submit" disabled={convertSubmitting}>
                    {convertSubmitting ? "Converting..." : "Submit Conversion"}
                  </button>
                </div>
              </form>
            )}
          </>
        )}
      </div>

      {loading ? (
        <Loader label="Loading broker accounts" />
      ) : (
        <DataTable
          columns={columns}
          data={brokerRows}
          emptyMessage="Link your first broker to begin."
        />
      )}
    </section>
  );
}

export default BrokerManagement;
