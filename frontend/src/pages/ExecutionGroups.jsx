import { useEffect, useMemo, useState } from "react";
import DataTable from "../components/DataTable";
import Loader from "../components/Loader";
import NotificationBanner from "../components/NotificationBanner";
import { api } from "../api";

const defaultGroupForm = {
  name: "",
  description: "",
  mode: "parallel",
};

const defaultAccountForm = {
  account_id: "",
  allocation_policy: "proportional",
  weight: "",
  fixed_lots: "",
};

function normaliseGroups(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }
  if (payload?.items) {
    return payload.items;
  }
  if (payload?.execution_groups) {
    return payload.execution_groups;
  }
  return [];
}

function normaliseRuns(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }
  if (payload?.items) {
    return payload.items;
  }
  if (payload?.runs) {
    return payload.runs;
  }
  return [];
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function humaniseStatus(value) {
  if (!value) {
    return "-";
  }
  return value
    .replace(/_/g, " ")
    .replace(/\w/g, (char) => char.toUpperCase());
}


function ExecutionGroups() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [groups, setGroups] = useState([]);
  const [brokers, setBrokers] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [groupFormState, setGroupFormState] = useState(defaultGroupForm);
  const [groupSubmitting, setGroupSubmitting] = useState(false);
  const [accountFormState, setAccountFormState] = useState(defaultAccountForm);
  const [accountSubmitting, setAccountSubmitting] = useState(false);
  const [accountStatusMessage, setAccountStatusMessage] = useState("");
  const [accountError, setAccountError] = useState("");
  const [editingMappingId, setEditingMappingId] = useState(null);
  const [runHistory, setRunHistory] = useState([]);
  const [runsLoading, setRunsLoading] = useState(false);
  const [runError, setRunError] = useState("");
  const [runRefreshKey, setRunRefreshKey] = useState(0);

  const [selectedRunId, setSelectedRunId] = useState("");
  const [runEvents, setRunEvents] = useState([]);
  const [runEventsLoading, setRunEventsLoading] = useState(false);
  const [runEventsError, setRunEventsError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        setLoading(true);
        const [groupsRes, brokersRes] = await Promise.all([
          api.getExecutionGroups(),
          api.getBrokers(),
        ]);
        if (!mounted) return;
        const groupList = normaliseGroups(groupsRes);
        setGroups(groupList);
        setBrokers(brokersRes?.brokers ?? brokersRes ?? []);
        if (groupList.length > 0) {
          setSelectedGroupId(groupList[0].id);
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
  }, []);

  useEffect(() => {
    let cancelled = false;

    if (!selectedGroupId) {
      setRunHistory([]);
      setRunError("");
      setRunsLoading(false);
      return () => {
        cancelled = true;
      };
    }

    async function loadRuns(groupId) {
      try {
        setRunsLoading(true);
        setRunError("");
        const response = await api.getExecutionGroupRuns(groupId);
        if (!cancelled) {
          setRunHistory(normaliseRuns(response));
        }
      } catch (err) {
        if (!cancelled) {
          setRunError(err.message);
          setRunHistory([]);
        }
      } finally {
        if (!cancelled) {
          setRunsLoading(false);
        }
      }
    }

    loadRuns(selectedGroupId);
    return () => {
      cancelled = true;
    };
  }, [selectedGroupId, runRefreshKey]);

  useEffect(() => {
    if (!selectedGroupId) {
      setSelectedRunId("");
      setRunEvents([]);
      return;
    }
    if (!runHistory.length) {
      setSelectedRunId("");
      setRunEvents([]);
      return;
    }
    if (!selectedRunId || !runHistory.some((run) => run.id === selectedRunId)) {
      setSelectedRunId(runHistory[0].id);
    }
  }, [runHistory, selectedGroupId, selectedRunId]);

  useEffect(() => {
    if (!selectedGroupId || !selectedRunId) {
      setRunEvents([]);
      setRunEventsError("");
      setRunEventsLoading(false);
      return;
    }

    let cancelled = false;
    async function loadEvents(currentGroupId, currentRunId) {
      try {
        setRunEventsLoading(true);
        setRunEventsError("");
        const response = await api.getExecutionGroupRunEvents(currentGroupId, currentRunId);
        if (!cancelled) {
          setRunEvents(response ?? []);
        }
      } catch (err) {
        if (!cancelled) {
          setRunEventsError(err.message);
          setRunEvents([]);
        }
      } finally {
        if (!cancelled) {
          setRunEventsLoading(false);
        }
      }
    }

    loadEvents(selectedGroupId, selectedRunId);
    return () => {
      cancelled = true;
    };
  }, [selectedGroupId, selectedRunId]);

  const selectedGroup = useMemo(
    () => groups.find((group) => group.id === selectedGroupId) ?? null,
    [groups, selectedGroupId]
  );

  const editingMapping = useMemo(() => {
    if (!selectedGroup || !editingMappingId) {
      return null;
    }
    return (selectedGroup.accounts ?? []).find(
      (mapping) => mapping.id === editingMappingId
    ) ?? null;
  }, [selectedGroup, editingMappingId]);

  const brokerLookup = useMemo(() => {
    const map = new Map();
    brokers.forEach((broker) => {
      map.set(broker.id, broker);
    });
    return map;
  }, [brokers]);

  const accountLookup = useMemo(() => {
    const map = new Map();
    brokers.forEach((broker) => {
      (broker.accounts ?? []).forEach((account) => {
        map.set(account.id, { account, broker });
      });
    });
    return map;
  }, [brokers]);

  const availableAccounts = useMemo(() => {
    const assigned = new Set(
      (selectedGroup?.accounts ?? []).map((mapping) => mapping.account_id)
    );
    return brokers.flatMap((broker) =>
      (broker.accounts ?? [])
        .filter((account) => !assigned.has(account.id))
        .map((account) => ({
          id: account.id,
          label: `${broker.broker_name} / ${broker.client_code} (${String(account.id).slice(0, 8)})`,
        }))
    );
  }, [brokers, selectedGroup]);

  const groupRows = useMemo(
    () =>
      groups.map((group) => ({
        id: group.id,
        name: group.name,
        mode: group.mode?.replace(/_/g, " ") ?? "-",
        accounts: group.accounts?.length ?? 0,
        updated: group.updated_at ? new Date(group.updated_at).toLocaleString() : "-",
      })),
    [groups]
  );

  const mappingRows = useMemo(() => {
    if (!selectedGroup) {
      return [];
    }
    return (selectedGroup.accounts ?? []).map((mapping) => {
      const info = accountLookup.get(mapping.account_id);
      const brokerName = info?.broker?.broker_name ?? "Unknown Broker";
      const clientCode = info?.broker?.client_code ?? "";
      const accountSuffix = String(mapping.account_id).slice(0, 8);
      return {
        mapping,
        account: info
          ? `${brokerName} / ${clientCode} (${accountSuffix})`
          : mapping.account_id,
        policy: mapping.allocation_policy.replace(/_/g, " "),
        weight: mapping.weight ?? "-",
        fixed_lots: mapping.fixed_lots ?? "-",
      };
    });
  }, [selectedGroup, accountLookup]);

  const runRows = useMemo(() => {
    return runHistory.map((run) => {
      const payload = run?.payload ?? {};
      const lotsValue = payload.lots ?? payload.total_lots;
      const lotSize = payload.lot_size ?? null;
      const lotSummary =
        lotsValue === undefined || lotsValue === null
          ? "-"
          : lotSize && lotSize !== 1
            ? `${lotsValue} (lot size ${lotSize})`
            : String(lotsValue);
      const orderIds = Array.isArray(payload.order_ids) ? payload.order_ids : [];
      const orderCount = orderIds.length || payload.order_count || 0;
      const distribution = Array.isArray(payload.distribution) ? payload.distribution : [];
      const accountCount = distribution.length || payload.account_count || 0;
      const symbolParts = [];
      if (payload.symbol) {
        symbolParts.push(payload.symbol);
      }
      if (payload.side) {
        symbolParts.push(payload.side);
      }

      let notes = "-";
      if (payload.error) {
        notes = payload.error;
      } else if ((run.status ?? "").toLowerCase() === "pending") {
        notes = "Awaiting completion";
      }

      const latency = payload.latency ?? {};
      const avgLatency =
        typeof latency.average_ms === "number"
          ? `${latency.average_ms.toFixed(1)} ms`
          : "-";
      const medianLatency =
        typeof latency.p50_ms === "number"
          ? `${latency.p50_ms.toFixed(1)} ms`
          : "-";
      const p95Latency =
        typeof latency.p95_ms === "number"
          ? `${latency.p95_ms.toFixed(1)} ms`
          : "-";

      const legOutcomes = Array.isArray(payload.leg_outcomes) ? payload.leg_outcomes : [];
      const statusCounts = legOutcomes.reduce((acc, outcome) => {
        const status = String(outcome.status || "unknown").toUpperCase();
        acc[status] = (acc[status] || 0) + 1;
        return acc;
      }, {});
      const legSummary = Object.keys(statusCounts).length
        ? Object.entries(statusCounts)
            .map(([status, count]) => `${status}: ${count}`)
            .join(" / ")
        : "-";

      return {
        id: run.id,
        runId: run.id,
        requestedAt: formatDateTime(run.requested_at),
        completedAt: formatDateTime(run.completed_at),
        status: humaniseStatus(run.status),
        instrument: symbolParts.length ? symbolParts.join(" / ") : "-",
        lots: lotSummary,
        accounts: accountCount === 0 ? "0" : accountCount ? String(accountCount) : "-",
        orders: orderCount === 0 ? "0" : orderCount ? String(orderCount) : "-",
        avgLatency,
        medianLatency,
        p95Latency,
        legSummary,
        notes,
      };
    });
  }, [runHistory]);
  const selectedRun = useMemo(
    () => runHistory.find((run) => run.id === selectedRunId) ?? null,
    [runHistory, selectedRunId]
  );

  const runEventRows = useMemo(() => {
    return runEvents.map((event) => {
      const accountInfo = event.account_id ? accountLookup.get(event.account_id) : null;
      const accountLabel = accountInfo
        ? `${accountInfo.broker.broker_name} / ${accountInfo.broker.client_code} (${String(accountInfo.account.id).slice(0, 8)})`
        : event.account_id ?? "-";
      const metadata = event.metadata ?? {};
      const metadataEntries = Object.entries(metadata)
        .filter(([, value]) => value !== null && typeof value !== "object")
        .map(([key, value]) => `${key}: ${value}`);
      const details = metadataEntries.length ? metadataEntries.join(" | ") : "-";

      return {
        status: humaniseStatus(event.status),
        account: accountLabel,
        latency: typeof event.latency_ms === "number" ? `${event.latency_ms.toFixed(1)} ms` : "-",
        requested: formatDateTime(event.requested_at),
        completed: formatDateTime(event.completed_at),
        details,
        message: event.message ?? "-",
      };
    });
  }, [runEvents, accountLookup]);

  const selectedRunSummary = useMemo(() => {
    if (!selectedRun) {
      return "";
    }
    const payload = selectedRun.payload ?? {};
    const symbol = payload.symbol ? `${payload.symbol}` : "Execution run";
    const statusLabel = humaniseStatus(selectedRun.status);
    const latency = payload.latency ?? {};
    const latencyParts = [];
    if (typeof latency.average_ms === "number") {
      latencyParts.push(`avg ${latency.average_ms.toFixed(1)} ms`);
    }
    if (typeof latency.p50_ms === "number") {
      latencyParts.push(`p50 ${latency.p50_ms.toFixed(1)} ms`);
    }
    if (typeof latency.p95_ms === "number") {
      latencyParts.push(`p95 ${latency.p95_ms.toFixed(1)} ms`);
    }
    const legOutcomes = Array.isArray(payload.leg_outcomes) ? payload.leg_outcomes : [];
    const statusCounts = legOutcomes.reduce((acc, outcome) => {
      const status = String(outcome.status || "unknown").toUpperCase();
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {});
    const legSummary = Object.keys(statusCounts).length
      ? Object.entries(statusCounts)
          .map(([status, count]) => `${status}: ${count}`)
          .join(" / ")
      : "";

    const summaryParts = [`${symbol} (${statusLabel})`];
    if (latencyParts.length) {
      summaryParts.push(latencyParts.join(", "));
    }
    if (legSummary) {
      summaryParts.push(`Legs ${legSummary}`);
    }
    return summaryParts.join(" • ");
  }, [selectedRun]);

  const editingAccountLabel = useMemo(() => {
    if (!editingMapping) {
      return "";
    }
    const info = accountLookup.get(editingMapping.account_id);
    if (!info) {
      return editingMapping.account_id;
    }
    const suffix = String(info.account.id).slice(0, 8);
    return `${info.broker.broker_name} / ${info.broker.client_code} (${suffix})`;
  }, [editingMapping, accountLookup]);

  useEffect(() => {
    if (selectedGroup) {
      setGroupFormState({
        name: selectedGroup.name ?? "",
        description: selectedGroup.description ?? "",
        mode: selectedGroup.mode ?? "parallel",
      });
    } else {
      setGroupFormState(defaultGroupForm);
    }
    setAccountFormState(defaultAccountForm);
    setEditingMappingId(null);
    setAccountStatusMessage("");
    setAccountError("");
  }, [selectedGroup]);

  async function reloadGroups(nextSelectionId) {
    try {
      const response = await api.getExecutionGroups();
      const groupList = normaliseGroups(response);
      setGroups(groupList);
      if (groupList.length === 0) {
        setSelectedGroupId("");
        return;
      }
      if (nextSelectionId && groupList.some((group) => group.id === nextSelectionId)) {
        setSelectedGroupId(nextSelectionId);
        return;
      }
      if (selectedGroupId && groupList.some((group) => group.id === selectedGroupId)) {
        setSelectedGroupId(selectedGroupId);
        return;
      }
      setSelectedGroupId(groupList[0].id);
    } catch (err) {
      setError(err.message);
    }
  }

  function handleSelectGroup(groupId) {
    setSelectedGroupId(groupId);
    setStatusMessage("");
  }

  function handleSelectRun(runId) {
    setSelectedRunId(runId);
    setRunEventsError("");
  }

  async function handleRefreshEvents() {
    if (!selectedGroupId || !selectedRunId) {
      return;
    }
    try {
      setRunEventsLoading(true);
      setRunEventsError("");
      const response = await api.getExecutionGroupRunEvents(selectedGroupId, selectedRunId);
      setRunEvents(response ?? []);
    } catch (err) {
      setRunEventsError(err.message);
      setRunEvents([]);
    } finally {
      setRunEventsLoading(false);
    }
  }

  function handleNewGroup() {
    setSelectedGroupId("");
    setGroupFormState(defaultGroupForm);
    setStatusMessage("");
  }

  async function handleGroupSubmit(event) {
    event.preventDefault();
    setError("");
    setStatusMessage("");
    setGroupSubmitting(true);
    try {
      const payload = {
        name: groupFormState.name.trim(),
        description: groupFormState.description?.trim() || null,
        mode: groupFormState.mode,
      };
      if (!payload.name) {
        throw new Error("Group name is required.");
      }
      if (selectedGroup) {
        await api.updateExecutionGroup(selectedGroup.id, payload);
        setStatusMessage(`Group ${payload.name} updated successfully.`);
        await reloadGroups(selectedGroup.id);
      } else {
        const created = await api.createExecutionGroup(payload);
        setStatusMessage(`Group ${created.name} created successfully.`);
        await reloadGroups(created.id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setGroupSubmitting(false);
    }
  }

  async function handleDeleteGroup() {
    if (!selectedGroup) {
      return;
    }
    if (
      !window.confirm(
        `Delete execution group ${selectedGroup.name}? This cannot be undone.`
      )
    ) {
      return;
    }
    setError("");
    setStatusMessage("");
    setGroupSubmitting(true);
    try {
      await api.deleteExecutionGroup(selectedGroup.id);
      setStatusMessage(`Group ${selectedGroup.name} deleted.`);
      await reloadGroups(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setGroupSubmitting(false);
    }
  }

  function computeAccountPayload(formState) {
    const payload = {
      allocation_policy: formState.allocation_policy,
      weight: null,
      fixed_lots: null,
    };
    if (formState.allocation_policy === "weighted") {
      const weightValue = Number(formState.weight);
      if (!weightValue || Number.isNaN(weightValue)) {
        throw new Error("Provide a valid weight for weighted allocation.");
      }
      payload.weight = weightValue;
    } else if (formState.allocation_policy === "fixed") {
      const lotsValue = Number(formState.fixed_lots);
      if (!Number.isInteger(lotsValue) || lotsValue <= 0) {
        throw new Error("Fixed lots must be a positive integer.");
      }
      payload.fixed_lots = lotsValue;
    }
    return payload;
  }

  async function handleAccountSubmit(event) {
    event.preventDefault();
    if (!selectedGroup) {
      setAccountError("Select a group before modifying account allocations.");
      return;
    }
    setAccountError("");
    setAccountStatusMessage("");
    setAccountSubmitting(true);
    try {
      const payload = computeAccountPayload(accountFormState);
      if (editingMapping) {
        await api.updateExecutionGroupAccount(selectedGroup.id, editingMapping.id, payload);
        setAccountStatusMessage("Account allocation updated.");
      } else {
        if (!accountFormState.account_id) {
          throw new Error("Choose an account to add to the group.");
        }
        await api.addExecutionGroupAccount(selectedGroup.id, {
          account_id: accountFormState.account_id,
          ...payload,
        });
        setAccountStatusMessage("Account added to execution group.");
      }
      setAccountFormState(defaultAccountForm);
      setEditingMappingId(null);
      await reloadGroups(selectedGroup.id);
    } catch (err) {
      setAccountError(err.message);
    } finally {
      setAccountSubmitting(false);
    }
  }

  function handleEditMapping(mapping) {
    setAccountFormState({
      account_id: mapping.account_id,
      allocation_policy: mapping.allocation_policy,
      weight: mapping.weight ?? "",
      fixed_lots: mapping.fixed_lots ?? "",
    });
    setEditingMappingId(mapping.id);
    setAccountStatusMessage("");
    setAccountError("");
  }

  async function handleRemoveMapping(mapping) {
    if (!selectedGroup) {
      return;
    }
    if (!window.confirm("Remove this account from the execution group?")) {
      return;
    }
    setAccountError("");
    setAccountStatusMessage("");
    try {
      await api.removeExecutionGroupAccount(selectedGroup.id, mapping.id);
      setAccountStatusMessage("Account mapping removed.");
      await reloadGroups(selectedGroup.id);
    } catch (err) {
      setAccountError(err.message);
    }
  }

  function resetAccountForm() {
    setAccountFormState(defaultAccountForm);
    setEditingMappingId(null);
    setAccountStatusMessage("");
    setAccountError("");
  }

  function handleRefreshRuns() {
    setRunError("");
    setRunRefreshKey((value) => value + 1);
  }

  const groupColumns = [
    { key: "name", label: "Name" },
    { key: "mode", label: "Mode" },
    { key: "accounts", label: "Accounts" },
    { key: "updated", label: "Updated" },
    {
      key: "actions",
      label: "Actions",
      render: (row) => (
        <div className="table-actions">
          {row.id === selectedGroupId ? (
            <span className="muted small">Selected</span>
          ) : (
            <button
              type="button"
              className="btn small"
              onClick={() => handleSelectGroup(row.id)}
            >
              Select
            </button>
          )}
        </div>
      ),
    },
  ];

  const mappingColumns = [
    { key: "account", label: "Account" },
    { key: "policy", label: "Policy" },
    { key: "weight", label: "Weight" },
    { key: "fixed_lots", label: "Fixed Lots" },
    {
      key: "actions",
      label: "Actions",
      render: (row) => (
        <div className="table-actions">
          <button
            type="button"
            className="btn small"
            onClick={() => handleEditMapping(row.mapping)}
          >
            Edit
          </button>
          <button
            type="button"
            className="btn small outline"
            onClick={() => handleRemoveMapping(row.mapping)}
          >
            Remove
          </button>
        </div>
      ),
    },
  ];

  const runColumns = [
    { key: "requestedAt", label: "Requested" },
    { key: "completedAt", label: "Completed" },
    { key: "status", label: "Status" },
    { key: "instrument", label: "Instrument" },
    { key: "lots", label: "Lots" },
    { key: "accounts", label: "Accounts" },
    { key: "orders", label: "Orders" },
    { key: "avgLatency", label: "Avg Latency" },
      { key: "medianLatency", label: "P50 Latency" },
      { key: "p95Latency", label: "P95 Latency" },
      { key: "legSummary", label: "Leg Outcomes" },
    { key: "notes", label: "Notes" },
    {
      key: "actions",
      label: "Actions",
      render: (row) => (
        <button
          type="button"
          className="btn small"
          onClick={() => handleSelectRun(row.runId)}
        >
          View Events
        </button>
      ),
    },
  ];

  const eventColumns = [
    { key: "status", label: "Status" },
    { key: "account", label: "Account" },
    { key: "latency", label: "Latency" },
    { key: "requested", label: "Requested" },
    { key: "completed", label: "Completed" },
    { key: "message", label: "Message" },
  ];

  const hasGroup = Boolean(selectedGroup);

  return (
    <section className="page">
      <h1>Execution Groups</h1>
      <p>Configure account fan-out policies and manage group-based order execution.</p>

      {error && <NotificationBanner type="danger" message={error} />}
      {statusMessage && <NotificationBanner type="info" message={statusMessage} />}

      {loading ? (
        <Loader label="Loading execution groups" />
      ) : (
        <>
          <div className="card-grid">
            <div className="card">
              <div className="button-row">
                <h2>Groups</h2>
                <span className="spacer" />
                <button className="btn small secondary" type="button" onClick={handleNewGroup}>
                  New Group
                </button>
              </div>
              <p className="muted small">
                Select an execution group to review accounts and update allocations.
              </p>
              <DataTable
                columns={groupColumns}
                data={groupRows}
                emptyMessage="Create your first execution group to begin."
              />
            </div>
            <div className="card">
              <h2>{selectedGroup ? "Edit Group" : "Create Group"}</h2>
              <form className="form-grid" onSubmit={handleGroupSubmit}>
                <label className="form-control">
                  <span>Name</span>
                  <input
                    type="text"
                    value={groupFormState.name}
                    onChange={(event) =>
                      setGroupFormState((prev) => ({ ...prev, name: event.target.value }))
                    }
                    required
                  />
                </label>
                <label className="form-control">
                  <span>Description</span>
                  <textarea
                    rows={3}
                    value={groupFormState.description}
                    onChange={(event) =>
                      setGroupFormState((prev) => ({ ...prev, description: event.target.value }))
                    }
                  />
                </label>
                <label className="form-control">
                  <span>Execution Mode</span>
                  <select
                    value={groupFormState.mode}
                    onChange={(event) =>
                      setGroupFormState((prev) => ({ ...prev, mode: event.target.value }))
                    }
                  >
                    <option value="parallel">Parallel</option>
                    <option value="sync">Synchronous</option>
                    <option value="staggered">Staggered</option>
                  </select>
                </label>
                <div className="button-row">
                  <button className="btn primary" type="submit" disabled={groupSubmitting}>
                    {groupSubmitting
                      ? selectedGroup
                        ? "Saving..."
                        : "Creating..."
                      : selectedGroup
                      ? "Save Changes"
                      : "Create Group"}
                  </button>
                  {selectedGroup && (
                    <button
                      className="btn outline"
                      type="button"
                      onClick={handleDeleteGroup}
                      disabled={groupSubmitting}
                    >
                      Delete Group
                    </button>
                  )}
                </div>
              </form>
            </div>
          </div>

          <div className="card">
            <h2>Account Allocation</h2>
            <p className="muted small">
              Map broker accounts to the selected group and define how lots should be distributed.
            </p>

            {accountError && <NotificationBanner type="danger" message={accountError} />}
            {accountStatusMessage && (
              <NotificationBanner type="info" message={accountStatusMessage} />
            )}

            <form className="form-grid" onSubmit={handleAccountSubmit}>
              <label className="form-control">
                <span>Account</span>
                <select
                  value={accountFormState.account_id}
                  onChange={(event) =>
                    setAccountFormState((prev) => ({ ...prev, account_id: event.target.value }))
                  }
                  disabled={!hasGroup || Boolean(editingMapping)}
                  required
                >
                  <option value="">Select account</option>
                  {
                    editingMapping ? (
                      <option value={editingMapping.account_id}>{editingAccountLabel}</option>
                    ) : (
                      availableAccounts.map((account) => (
                        <option key={account.id} value={account.id}>
                          {account.label}
                        </option>
                      ))
                    )
                  }
                </select>
              </label>
              <label className="form-control">
                <span>Allocation Policy</span>
                <select
                  value={accountFormState.allocation_policy}
                  onChange={(event) =>
                    setAccountFormState((prev) => ({
                      ...prev,
                      allocation_policy: event.target.value,
                      weight: event.target.value === "weighted" ? prev.weight : "",
                      fixed_lots: event.target.value === "fixed" ? prev.fixed_lots : "",
                    }))
                  }
                  disabled={!hasGroup}
                >
                  <option value="proportional">Proportional</option>
                  <option value="fixed">Fixed lots</option>
                  <option value="weighted">Weighted</option>
                </select>
              </label>
              {accountFormState.allocation_policy === "weighted" && (
                <label className="form-control">
                  <span>Weight</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={accountFormState.weight}
                    onChange={(event) =>
                      setAccountFormState((prev) => ({ ...prev, weight: event.target.value }))
                    }
                    required
                    disabled={!hasGroup}
                  />
                </label>
              )}
              {accountFormState.allocation_policy === "fixed" && (
                <label className="form-control">
                  <span>Fixed Lots</span>
                  <input
                    type="number"
                    min="1"
                    value={accountFormState.fixed_lots}
                    onChange={(event) =>
                      setAccountFormState((prev) => ({
                        ...prev,
                        fixed_lots: event.target.value,
                      }))
                    }
                    required
                    disabled={!hasGroup}
                  />
                </label>
              )}
              <div className="button-row">
                <button className="btn primary" type="submit" disabled={accountSubmitting || !hasGroup}>
                  {accountSubmitting
                    ? editingMapping
                      ? "Saving..."
                      : "Adding..."
                    : editingMapping
                    ? "Save Allocation"
                    : "Add Account"}
                </button>
                <button className="btn outline" type="button" onClick={resetAccountForm}>
                  Reset
                </button>
              </div>
            </form>

            <DataTable
              columns={mappingColumns}
              data={mappingRows}
              emptyMessage={
                hasGroup ? "No accounts linked yet." : "Select a group to view mappings."
              }
            />
          </div>

          <div className="card">
            <div className="button-row">
              <h2>Recent Execution Runs</h2>
              <span className="spacer" />
              <button
                className="btn small secondary"
                type="button"
                onClick={handleRefreshRuns}
                disabled={!hasGroup || runsLoading}
              >
                Refresh
              </button>
            </div>
            <p className="muted small">Review fan-out activity captured for the selected execution group.</p>
            {runError && <NotificationBanner type="danger" message={runError} />}
            {runsLoading ? (
              <Loader label="Loading execution runs" />
            ) : (
              <DataTable
                columns={runColumns}
                data={runRows}
                emptyMessage={
                  hasGroup
                    ? "No execution runs recorded yet."
                    : "Select a group to view run history."
                }
              />
            )}
          </div>
          <div className="card">
            <div className="button-row">
              <h3>Execution Event Timeline</h3>
              <span className="spacer" />
              <button
                className="btn small secondary"
                type="button"
                onClick={handleRefreshEvents}
                disabled={!selectedRunId || runEventsLoading}
              >
                Refresh Events
              </button>
            </div>
            <p className="muted small">
              {selectedRun
                ? `Inspecting run ${String(selectedRun.id).slice(0, 8)} — ${selectedRunSummary}`
                : "Select a run above to view per-order events."}
            </p>
            {runEventsError && <NotificationBanner type="danger" message={runEventsError} />}
            {runEventsLoading ? (
              <Loader label="Loading execution events" />
            ) : (
              <DataTable
                columns={eventColumns}
                data={runEventRows}
                emptyMessage={
                  selectedRun
                    ? "No execution events recorded for this run yet."
                    : "Select a run to view events."
                }
              />
            )}
          </div>
        </>
      )}
    </section>
  );
}

export default ExecutionGroups;






















