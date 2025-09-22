import { useEffect, useMemo, useState } from "react";
import DataTable from "../components/DataTable";
import Loader from "../components/Loader";
import NotificationBanner from "../components/NotificationBanner";
import { api } from "../api";
import { formatCurrency, formatDateTime } from "../utils/formatters";

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
      helper: "Paste the 32-character base32 seed from SmartAPI. It is used transiently and never stored.",
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

  const usingStructuredFields = Boolean(structuredBrokerFields[formState.broker_name]);
  const activeStructuredFields = structuredBrokerFields[formState.broker_name] ?? [];
  const activeStructuredValues = structuredCredentials[formState.broker_name] ?? {};

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
      render: (row) => (
        <div className="table-actions">
          <button className="btn small secondary" type="button" onClick={() => handleLogout(row)}>
            Logout
          </button>
          <button className="btn small danger" type="button" onClick={() => handleDelete(row)}>
            Delete
          </button>
        </div>
      ),
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
                  Credentials are used only to initiate the session; we do not persist API keys or TOTP seeds.
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
