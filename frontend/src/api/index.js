const TOKEN_STORAGE_KEY = "nga_access_token";

let authToken = null;

if (typeof window !== "undefined") {
  authToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

function setAuthToken(token) {
  authToken = token || null;
  if (typeof window !== "undefined") {
    if (authToken) {
      window.localStorage.setItem(TOKEN_STORAGE_KEY, authToken);
    } else {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  }
}

function getAuthToken() {
  return authToken;
}

async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
  const { headers, body, ...rest } = options;

  const config = {
    method: "GET",
    ...rest,
    headers: {
      Accept: "application/json",
      ...headers,
    },
  };

  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }

  if (body !== undefined) {
    config.method = config.method || "POST";
    config.body = JSON.stringify(body);
    config.headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url, config);
  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const detail = isJson ? payload?.detail ?? payload : response.statusText;
    const message = typeof detail === "string" ? detail : JSON.stringify(detail);
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return payload;
}

export const api = {
  login: (payload) => request("/api/auth/login", { method: "POST", body: payload }),
  register: (payload) => request("/api/auth/register", { method: "POST", body: payload }),
  getCurrentUser: () => request("/api/users/me"),
  getAnalyticsDashboard: () => request("/api/analytics/dashboard"),
  getRmsStatus: () => request("/api/rms/status"),
  getRmsConfig: () => request("/api/rms/config"),
  updateRmsConfig: (payload) => request("/api/rms/config", { method: "POST", body: payload }),
  rmsSquareOff: () => request("/api/rms/squareoff", { method: "POST" }),
  enforceRms: () => request("/api/rms/enforce", { method: "POST" }),
  getSupportedBrokers: () => request("/api/brokers/supported"),
  getBrokers: () => request("/api/brokers"),
  connectBroker: (payload) => request("/api/brokers/connect", { method: "POST", body: payload }),
  getOrders: () => request("/api/orders"),
  placeOrder: (payload) => request("/api/orders", { method: "POST", body: payload }),
  getExecutionGroups: () => request("/api/execution-groups"),
  createExecutionGroup: (payload) =>
    request("/api/execution-groups", { method: "POST", body: payload }),
  updateExecutionGroup: (id, payload) =>
    request(`/api/execution-groups/${id}`, { method: "PATCH", body: payload }),
  deleteExecutionGroup: (id) =>
    request(`/api/execution-groups/${id}`, { method: "DELETE" }),
  addExecutionGroupAccount: (id, payload) =>
    request(`/api/execution-groups/${id}/accounts`, { method: "POST", body: payload }),
  updateExecutionGroupAccount: (id, mappingId, payload) =>
    request(`/api/execution-groups/${id}/accounts/${mappingId}`, { method: "PATCH", body: payload }),
  removeExecutionGroupAccount: (id, mappingId) =>
    request(`/api/execution-groups/${id}/accounts/${mappingId}`, { method: "DELETE" }),
  previewExecutionGroup: (id, lots) =>
    request(`/api/execution-groups/${id}/preview?lots=${encodeURIComponent(lots)}`),
  getExecutionGroupRuns: (id) =>
    request(`/api/execution-groups/${id}/runs`),
  getExecutionGroupRunEvents: (groupId, runId) =>
    request(`/api/execution-groups/${groupId}/runs/${runId}/events`),
  placeExecutionGroupOrder: (id, payload) =>
    request(`/api/execution-groups/${id}/orders`, { method: "POST", body: payload }),
  getStrategies: () => request("/api/strategies"),
  createStrategy: (payload) => request("/api/strategies", { method: "POST", body: payload }),
  startStrategy: (id, payload) => request(`/api/strategies/${id}/start`, { method: "POST", body: payload }),
  stopStrategy: (id, payload) => request(`/api/strategies/${id}/stop`, { method: "POST", body: payload ?? {} }),
  getStrategyLogs: (id) => request(`/api/strategies/${id}/logs`),
  getStrategyPerformance: (id) => request(`/api/strategies/${id}/pnl`),
};

export { API_BASE_URL, request, setAuthToken, getAuthToken };

