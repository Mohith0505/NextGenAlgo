from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExecutionMode(str, enum.Enum):
    sync = "sync"
    parallel = "parallel"
    staggered = "staggered"


class ExecutionGroup(Base):
    __tablename__ = "execution_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    mode: Mapped[ExecutionMode] = mapped_column(Enum(ExecutionMode, name="execution_mode"), default=ExecutionMode.parallel)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped["User"] = relationship(back_populates="execution_groups")
    accounts: Mapped[list["ExecutionGroupAccount"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    runs: Mapped[list["ExecutionRun"]] = relationship(back_populates="group", cascade="all, delete-orphan")
