import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app


def main() -> None:
    """Run a small smoke test against the FastAPI app. Only executed when the
    script is run directly so pytest/import-time collection doesn't trigger
    network/database access.
    """
    client = TestClient(app)
    print("GET /api/auth/health ->", client.get("/api/auth/health").status_code)
    print("GET /api/rms/status ->", client.get("/api/rms/status").status_code)
    print(
        "GET /api/analytics/dashboard ->",
        client.get("/api/analytics/dashboard").status_code,
    )


if __name__ == "__main__":
    main()
