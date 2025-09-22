from __future__ import annotations

import uuid
from typing import Iterable

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserRoleEnum, UserStatusEnum


class UserService:
    """Database-backed user service used across API routers."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _role_from_schema(self, role: UserRoleEnum | None) -> UserRole:
        role_value = role.value if isinstance(role, UserRoleEnum) else role
        return UserRole(role_value or UserRole.trader.value)

    def _status_from_schema(self, status: UserStatusEnum | None) -> UserStatus:
        status_value = status.value if isinstance(status, UserStatusEnum) else status
        return UserStatus(status_value or UserStatus.active.value)

    def _to_schema(self, user: User) -> UserRead:
        return UserRead.model_validate(user)

    def _execute(self, stmt: Select[tuple[User]]) -> Iterable[User]:
        return self.session.execute(stmt).scalars()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def create_user(self, payload: UserCreate) -> UserRead:
        user = User(
            name=payload.name,
            email=payload.email.lower(),
            phone=payload.phone,
            password_hash=get_password_hash(payload.password),
            role=self._role_from_schema(payload.role),
            status=self._status_from_schema(payload.status),
            is_superuser=payload.is_superuser,
        )
        self.session.add(user)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ValueError("Email already registered") from exc
        self.session.refresh(user)
        return self._to_schema(user)

    def authenticate(self, email: str, password: str) -> UserRead | None:
        user = self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return self._to_schema(user)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower()).limit(1)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_user_by_id(self, user_id: uuid.UUID | str) -> UserRead | None:
        user = self.session.get(User, uuid.UUID(str(user_id)))
        if user is None:
            return None
        return self._to_schema(user)

    def get_user_model(self, user_id: uuid.UUID | str) -> User | None:
        return self.session.get(User, uuid.UUID(str(user_id)))

    def list_users(self) -> list[UserRead]:
        stmt = select(User).order_by(User.created_at.asc())
        return [self._to_schema(user) for user in self._execute(stmt)]

    def update_user(self, user_id: uuid.UUID | str, payload: UserUpdate) -> UserRead | None:
        user = self.session.get(User, uuid.UUID(str(user_id)))
        if user is None:
            return None
        if payload.name is not None:
            user.name = payload.name
        if payload.email is not None:
            user.email = payload.email.lower()
        if payload.phone is not None:
            user.phone = payload.phone
        if payload.role is not None:
            user.role = self._role_from_schema(payload.role)
        if payload.status is not None:
            user.status = self._status_from_schema(payload.status)
        if payload.is_superuser is not None:
            user.is_superuser = payload.is_superuser
        if payload.password:
            user.password_hash = get_password_hash(payload.password)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return self._to_schema(user)

    def delete_user(self, user_id: uuid.UUID | str) -> bool:
        user = self.session.get(User, uuid.UUID(str(user_id)))
        if user is None:
            return False
        self.session.delete(user)
        self.session.commit()
        return True

    def get_first_user(self) -> User | None:
        stmt = select(User).order_by(User.created_at.asc()).limit(1)
        return self.session.execute(stmt).scalar_one_or_none()
