"""Quick import smoke test for the backend package."""
from importlib import import_module
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Ensure backend is on sys.path so `app` package can be imported
sys.path.insert(0, str(PROJECT_ROOT))

MODULES = [
    "app.main",
    "app.celery_app",
    "app.api.router",
    "app.core.config",
]


def main():
    for mod in MODULES:
        print("Importing", mod)
        import_module(mod)
    print("All imports succeeded")


if __name__ == "__main__":
    main()
