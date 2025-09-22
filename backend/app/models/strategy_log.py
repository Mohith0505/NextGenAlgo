from __future__ import annotations

import enum
import uuid
from datetime import datetime

from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.strategy import Strategy
    from app.models.strategy_run import StrategyRun


class StrategyLogLevel(str, enum.Enum):
    info = "info"
    warning = "warning"
    error = "error"


class StrategyLog(Base):
    __tablename__ = "strategy_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("strategies.id", ondelete="CASCADE"))
    run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("strategy_runs.id", ondelete="SET NULL"))
    level: Mapped[StrategyLogLevel] = mapped_column(Enum(StrategyLogLevel, name="strategy_log_level"), default=StrategyLogLevel.info)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    strategy: Mapped["Strategy"] = relationship(back_populates="logs")
    run: Mapped["StrategyRun | None"] = relationship(back_populates="logs")
