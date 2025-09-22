import { useEffect, useMemo, useState } from "react";
import DataTable from "../components/DataTable";
import Loader from "../components/Loader";
import NotificationBanner from "../components/NotificationBanner";
import { api } from "../api";
import { formatCurrency, formatDateTime } from "../utils/formatters";

const defaultCredentials = {
  paper_trading: () => ({ client_code: "demo" }),
};

function BrokerManagement() {
  const [supported, setSupported] = useState([]);
  const [brokers, setBrokers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formState, setFormState] = useState({
    broker_name: "paper_trading",
    client_code: "demo",
    credentials: JSON.stringify(defaultCredentials.paper_trading(), null, 2),
  });

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

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setStatusMessage("");
    setSubmitting(true);
    try {
      let credentialsObject;
      try {
        credentialsObject = JSON.parse(formState.credentials || "{}");
      } catch (err) {
        throw new Error("Credentials must be valid JSON.");
      }
      const payload = {
        broker_name: formState.broker_name,
        client_code: formState.client_code,
        credentials: credentialsObject,
      };
      await api.connectBroker(payload);
      setStatusMessage(`Broker ${formState.broker_name} linked successfully.`);
      const brokersRes = await api.getBrokers();
      setBrokers(brokersRes?.brokers ?? brokersRes ?? []);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  function handleBrokerChange(value) {
    setFormState((prev) => {
      const nextCredentials = defaultCredentials[value]?.() ?? {};
      return {
        ...prev,
        broker_name: value,
        credentials: JSON.stringify(nextCredentials, null, 2),
      };
    });
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
  ];

  return (
    <section className="page">
      <h1>Broker Management</h1>
      <p>Link adapters, review session status, and monitor account exposure.</p>

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
              />
            </label>
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
                Provide broker-specific keys. For paper trading, the default JSON is sufficient.
              </small>
            </label>
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
