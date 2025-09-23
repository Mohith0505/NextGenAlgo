import { useEffect, useMemo, useState } from "react";
import QuickTradeButtons from "../components/QuickTradeButtons";
import OrderTicket from "../components/OrderTicket";
import NotificationBanner from "../components/NotificationBanner";
import DataTable from "../components/DataTable";
import Loader from "../components/Loader";
import { api } from "../api";
import { formatDateTime } from "../utils/formatters";

const initialTicket = {
  symbol: "NIFTY24SEP24000CE",
  quantity: 1,
  side: "BUY",
  orderType: "MARKET",
  price: "",
  takeProfit: "",
  stopLoss: "",
};

const initialGroupTicket = {
  symbol: "NIFTY24SEP24000CE",
  quantity: 1,
  lotSize: 50,
  side: "BUY",
  orderType: "MARKET",
  price: "",
  takeProfit: "",
  stopLoss: "",
};

function QuickTradePanel() {
  const [formState, setFormState] = useState(initialTicket);
  const [groupFormState, setGroupFormState] = useState(initialGroupTicket);
  const [brokers, setBrokers] = useState([]);
  const [executionGroups, setExecutionGroups] = useState([]);
  const [selectedBrokerId, setSelectedBrokerId] = useState("");
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [squareOffMessage, setSquareOffMessage] = useState("");
  const [groupPreview, setGroupPreview] = useState([]);
  const [groupAllocations, setGroupAllocations] = useState([]);
  const [groupStatusMessage, setGroupStatusMessage] = useState("");
  const [groupError, setGroupError] = useState("");
  const [groupSubmitting, setGroupSubmitting] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        setLoading(true);
        const [brokersRes, ordersRes, groupsRes] = await Promise.all([
          api.getBrokers(),
          api.getOrders(),
          api.getExecutionGroups(),
        ]);
        if (!mounted) return;
        const brokerList = brokersRes?.brokers ?? brokersRes ?? [];
        setBrokers(brokerList);
        if (!selectedBrokerId && brokerList.length > 0) {
          setSelectedBrokerId(brokerList[0].id);
        }
        const orderList = ordersRes?.orders ?? [];
        setOrders(orderList);
        const groupsList = Array.isArray(groupsRes)
          ? groupsRes
          : groupsRes?.items ?? groupsRes?.execution_groups ?? [];
        setExecutionGroups(groupsList);
        if (!selectedGroupId && groupsList.length > 0) {
          setSelectedGroupId(groupsList[0].id);
        }
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
  }, [selectedBrokerId, selectedGroupId]);

  const brokerOptions = useMemo(
    () =>
      brokers.map((broker) => ({
        id: broker.id,
        label: `${broker.broker_name} \u2022 ${broker.client_code}`,
      })),
    [brokers]
  );

  const groupOptions = useMemo(
    () =>
      executionGroups.map((group) => ({
        id: group.id,
        label: group.name ?? "Unnamed Group",
      })),
    [executionGroups]
  );

  const brokerLookup = useMemo(() => {
    const map = new Map();
    brokers.forEach((broker) => {
      map.set(broker.id, broker);
    });
    return map;
  }, [brokers]);

  const groupPreviewRows = useMemo(() => {
    const lotSize = Number(groupFormState.lotSize || 0);
    return groupPreview.map((entry) => {
      const broker = brokerLookup.get(entry.broker_id);
      return {
        account: entry.account_id,
        broker:
          broker?.broker_name ?? `${entry.broker_id}`.slice(0, 8).toUpperCase(),
        lots: entry.lots,
        quantity: lotSize > 0 ? entry.lots * lotSize : entry.lots,
        policy: entry.allocation_policy.replace(/_/g, " "),
        weight: entry.weight ?? entry.fixed_lots ?? "-",
      };
    });
  }, [groupPreview, groupFormState.lotSize, brokerLookup]);

  const groupAllocationRows = useMemo(
    () =>
      groupAllocations.map((entry) => {
        const broker = brokerLookup.get(entry.broker_id);
        return {
          account: entry.account_id,
          broker:
            broker?.broker_name ?? `${entry.broker_id}`.slice(0, 8).toUpperCase(),
          lots: entry.lots,
          quantity: entry.quantity,
          policy: entry.allocation_policy.replace(/_/g, " "),
          weight: entry.weight ?? entry.fixed_lots ?? "-",
        };
      }),
    [groupAllocations, brokerLookup]
  );

  async function refreshOrders() {
    try {
      const ordersRes = await api.getOrders();
      setOrders(ordersRes?.orders ?? []);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSubmit(ticket) {
    setError("");
    setStatusMessage("");
    setSubmitting(true);
    try {
      if (!selectedBrokerId) {
        throw new Error("Link a broker before placing orders.");
      }
      if (!ticket.quantity || ticket.quantity <= 0) {
        throw new Error("Quantity must be greater than zero.");
      }
      const payload = {
        broker_id: selectedBrokerId,
        symbol: ticket.symbol.trim(),
        qty: Number(ticket.quantity),
        order_type: ticket.orderType,
        side: ticket.side,
        exchange: ticket.exchange ? ticket.exchange.trim() : undefined,
        symbol_token: ticket.symbolToken ? String(ticket.symbolToken).trim() : undefined,
      };
      if (ticket.orderType === "LIMIT") {
        if (!ticket.price) throw new Error("Enter a limit price for limit orders.");
        payload.price = Number(ticket.price);
      }
      if (ticket.takeProfit) payload.take_profit = Number(ticket.takeProfit);
      if (ticket.stopLoss) payload.stop_loss = Number(ticket.stopLoss);

      const order = await api.placeOrder(payload);
      setStatusMessage(
        `Order ${order.id.slice(0, 8)} placed: ${order.side} ${order.qty} ${order.symbol}`
      );
      setFormState((prev) => ({ ...prev, takeProfit: "", stopLoss: "" }));
      await refreshOrders();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleGroupPreview() {
    setGroupError("");
    setGroupStatusMessage("");
    if (!selectedGroupId) {
      setGroupError("Select an execution group to preview lot allocation.");
      return;
    }
    const lots = Number(groupFormState.quantity);
    if (!lots || lots <= 0) {
      setGroupError("Enter the total lots you want to distribute across the group.");
      return;
    }
    setPreviewLoading(true);
    try {
      const preview = await api.previewExecutionGroup(selectedGroupId, lots);
      setGroupPreview(preview ?? []);
    } catch (err) {
      setGroupError(err.message);
    } finally {
      setPreviewLoading(false);
    }
  }

  async function handleGroupSubmit(ticket) {
    setGroupError("");
    setGroupStatusMessage("");
    setGroupSubmitting(true);
    try {
      if (!selectedGroupId) {
        throw new Error("Select an execution group before placing the order.");
      }
      const lots = Number(ticket.quantity);
      if (!lots || lots <= 0) {
        throw new Error("Lots must be greater than zero.");
      }
      const lotSize = Number(ticket.lotSize);
      if (!lotSize || lotSize <= 0) {
        throw new Error("Lot size must be greater than zero.");
      }
      const payload = {
        symbol: ticket.symbol.trim(),
        side: ticket.side,
        lots,
        lot_size: lotSize,
        order_type: ticket.orderType,
      };
      if (ticket.orderType === "LIMIT") {
        if (!ticket.price) throw new Error("Enter a limit price for limit orders.");
        payload.price = Number(ticket.price);
      }
      if (ticket.takeProfit) payload.take_profit = Number(ticket.takeProfit);
      if (ticket.stopLoss) payload.stop_loss = Number(ticket.stopLoss);
      if (ticket.strategyId) payload.strategy_id = ticket.strategyId;

      const response = await api.placeExecutionGroupOrder(selectedGroupId, payload);
      setGroupAllocations(response?.allocation ?? []);
      if (response?.orders?.length) {
        setGroupStatusMessage(
          `Execution run ${String(response.execution_run_id).slice(0, 8)} placed ${response.orders.length} orders across ${response.allocation?.length ?? 0} accounts.`
        );
      } else {
        setGroupStatusMessage("Execution group order processed successfully.");
      }
      setGroupPreview([]);
      setGroupFormState((prev) => ({ ...prev, takeProfit: "", stopLoss: "" }));
      await refreshOrders();
    } catch (err) {
      setGroupError(err.message);
    } finally {
      setGroupSubmitting(false);
    }
  }

  async function handleSquareOff() {
    setError("");
    setSquareOffMessage("");
    try {
      const response = await api.rmsSquareOff();
      setSquareOffMessage(response.message);
      await refreshOrders();
    } catch (err) {
      setError(err.message);
    }
  }

  const orderColumns = [
    { key: "symbol", label: "Symbol" },
    { key: "side", label: "Side" },
    { key: "qty", label: "Qty" },
    { key: "order_type", label: "Order Type" },
    { key: "status", label: "Status" },
    {
      key: "created",
      label: "Created",
      render: (row) => formatDateTime(row.created_at),
    },
  ];

  const groupColumns = [
    { key: "account", label: "Account" },
    { key: "broker", label: "Broker" },
    { key: "lots", label: "Lots" },
    { key: "quantity", label: "Quantity" },
    { key: "policy", label: "Policy" },
    { key: "weight", label: "Weight / Fixed" },
  ];

  return (
    <section className="page">
      <h1>Quick Trade Panel</h1>
      <p>Manual trading cockpit wired to the paper broker for Phase 1 testing.</p>

      {error && <NotificationBanner type="danger" message={error} />}
      {statusMessage && <NotificationBanner type="info" message={statusMessage} />}
      {squareOffMessage && (
        <NotificationBanner type="warning" message={squareOffMessage} />
      )}

      {loading ? (
        <Loader label="Loading trade data" />
      ) : (
        <div className="quick-trade-layout">
          <div>
            <label className="form-control">
              <span>Broker</span>
              <select
                value={selectedBrokerId}
                onChange={(event) => setSelectedBrokerId(event.target.value)}
              >
                {brokerOptions.length === 0 ? (
                  <option value="">Connect a broker first</option>
                ) : (
                  brokerOptions.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))
                )}
              </select>
            </label>

            <OrderTicket
              value={formState}
              onChange={setFormState}
              onSubmit={handleSubmit}
              submitting={submitting}
              submitLabel="Place Order"
              subtitle="Send paper orders via the connected broker adapter."
            />

            <div className="card">
              <h2>Execution Group Fan-Out</h2>
              <p>Distribute lots across linked accounts using execution groups.</p>

              <label className="form-control">
                <span>Execution Group</span>
                <select
                  value={selectedGroupId}
                  onChange={(event) => setSelectedGroupId(event.target.value)}
                >
                  {groupOptions.length === 0 ? (
                    <option value="">Create an execution group to begin</option>
                  ) : (
                    groupOptions.map((option) => (
                      <option key={option.id} value={option.id}>
                        {option.label}
                      </option>
                    ))
                  )}
                </select>
              </label>

              {groupError && <NotificationBanner type="danger" message={groupError} />}
              {groupStatusMessage && (
                <NotificationBanner type="info" message={groupStatusMessage} />
              )}

              <OrderTicket
                title="Execution Group Order"
                quantityLabel="Total Lots"
                showLotSize
                value={groupFormState}
                onChange={setGroupFormState}
                onSubmit={handleGroupSubmit}
                submitting={groupSubmitting}
                submitLabel="Send Group Order"
                subtitle="Allocate lots across every account mapped to this execution group."
              />

              <div className="button-row">
                <button
                  className="btn secondary"
                  type="button"
                  onClick={handleGroupPreview}
                  disabled={previewLoading || !selectedGroupId}
                >
                  {previewLoading ? "Previewing..." : "Preview Allocation"}
                </button>
              </div>

              {groupPreviewRows.length > 0 && (
                <div className="card">
                  <h3>Allocation Preview</h3>
                  <DataTable
                    columns={groupColumns}
                    data={groupPreviewRows}
                    emptyMessage="No preview available."
                  />
                </div>
              )}

              {groupAllocationRows.length > 0 && (
                <div className="card">
                  <h3>Last Execution Distribution</h3>
                  <DataTable
                    columns={groupColumns}
                    data={groupAllocationRows}
                    emptyMessage="Run an execution group order to see distribution details."
                  />
                </div>
              )}
            </div>
          </div>

          <div className="quick-trade-actions">
            <h2>Controls</h2>
            <QuickTradeButtons
              onBuy={() => setFormState((prev) => ({ ...prev, side: "BUY" }))}
              onSell={() => setFormState((prev) => ({ ...prev, side: "SELL" }))}
              onReverse={() =>
                setFormState((prev) => ({
                  ...prev,
                  side: prev.side === "BUY" ? "SELL" : "BUY",
                }))
              }
              onSquareOff={handleSquareOff}
            />
            <div className="card">
              <h3>Latest Orders</h3>
              <DataTable
                columns={orderColumns}
                data={orders}
                emptyMessage="No orders placed yet."
              />
            </div>
          </div>
        </div>
      )}

      {brokerOptions.length === 0 && !loading && (
        <NotificationBanner
          type="warning"
          message="No brokers linked. Head to the Broker Management tab to connect the paper trading adapter."
        />
      )}
      {groupOptions.length === 0 && !loading && (
        <NotificationBanner
          type="warning"
          message="Execution groups are empty. Visit the Execution Groups section to configure fan-out policies."
        />
      )}
    </section>
  );
}

export default QuickTradePanel;
