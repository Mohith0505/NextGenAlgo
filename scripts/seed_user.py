import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from app.db.session import SessionLocal
from app.services.users import UserService
from app.schemas.user import UserCreate, UserRoleEnum, UserStatusEnum


def ensure_seed_user() -> None:
    session = SessionLocal()
    service = UserService(session)
    try:
        existing = service.list_users()
        if existing:
            print("Existing users:", ", ".join(user.email for user in existing))
            return
        user = service.create_user(
            UserCreate(
                name="Demo Owner",
                email="owner@example.com",
                phone="+911234567890",
                password="StrongPass123",
                role=UserRoleEnum.owner,
                status=UserStatusEnum.active,
                is_superuser=True,
            )
        )
        print("Created user:", user.email)
    finally:
        session.close()


if __name__ == "__main__":
    ensure_seed_user()
