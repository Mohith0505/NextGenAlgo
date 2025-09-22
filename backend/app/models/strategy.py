from __future__ import annotations
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StrategyType(str, enum.Enum):
    built_in = "built-in"
    custom = "custom"
    connector = "connector"


class StrategyStatus(str, enum.Enum):
    active = "active"
    stopped = "stopped"


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[StrategyType] = mapped_column(Enum(StrategyType, name="strategy_type"), nullable=False)
    params: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[StrategyStatus] = mapped_column(
        Enum(StrategyStatus, name="strategy_status"), default=StrategyStatus.stopped
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    owner: Mapped["User"] = relationship(back_populates="strategies")
    orders: Mapped[list["Order"]] = relationship(back_populates="strategy")
    runs: Mapped[list["StrategyRun"]] = relationship(
        back_populates="strategy", cascade="all, delete-orphan"
    )
    logs: Mapped[list["StrategyLog"]] = relationship(
        back_populates="strategy", cascade="all, delete-orphan"
    )
