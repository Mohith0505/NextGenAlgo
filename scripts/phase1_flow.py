import json
import sys
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from app.main import app

client = TestClient(app)

print("Health", client.get("/api/auth/health").status_code)
print("RMS", client.get("/api/rms/status").status_code)
print("Analytics", client.get("/api/analytics/dashboard").status_code)

supported = client.get("/api/brokers/supported").json()
print("Supported brokers:", supported)

payload = {
    "broker_name": "paper_trading",
    "client_code": "demo",
    "credentials": {"client_code": "demo"},
}
connect_resp = client.post("/api/brokers/connect", json=payload)
print("Connect status:", connect_resp.status_code)
connect_json = connect_resp.json()
print(json.dumps(connect_json, indent=2))

broker_id = connect_json["id"]
order_payload = {
    "broker_id": broker_id,
    "symbol": "NIFTY24SEP24000CE",
    "side": "BUY",
    "qty": 1,
    "order_type": "MARKET",
}
order_resp = client.post("/api/orders", json=order_payload)
print("Order status:", order_resp.status_code)
print(json.dumps(order_resp.json(), indent=2))

orders_list = client.get("/api/orders").json()
print("Orders:", json.dumps(orders_list, indent=2))

rms_status = client.get("/api/rms/status").json()
print("RMS status after order:", json.dumps(rms_status, indent=2))
