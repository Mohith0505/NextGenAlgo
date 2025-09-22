import json
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

strategy_payload = {
    "name": "Opening Range Breakout",
    "type": "built-in",
    "params": {"window": 15, "symbol": "NIFTY"}
}
create_resp = client.post("/api/strategies", json=strategy_payload)
print("Create strategy:", create_resp.status_code)
strategy = create_resp.json()
print(json.dumps(strategy, indent=2))

strategy_id = strategy["id"]

start_resp = client.post(
    f"/api/strategies/{strategy_id}/start",
    json={"mode": "paper", "configuration": {"note": "phase1 smoke"}},
)
print("Start strategy:", start_resp.status_code)
print(json.dumps(start_resp.json(), indent=2))

logs_resp = client.get(f"/api/strategies/{strategy_id}/logs")
print("Logs:", logs_resp.status_code)
print(json.dumps(logs_resp.json(), indent=2))

stop_resp = client.post(
    f"/api/strategies/{strategy_id}/stop",
    json={"reason": "demo complete"},
)
print("Stop strategy:", stop_resp.status_code)
print(json.dumps(stop_resp.json(), indent=2))

perf_resp = client.get(f"/api/strategies/{strategy_id}/pnl")
print("Performance:", perf_resp.status_code)
print(json.dumps(perf_resp.json(), indent=2))
