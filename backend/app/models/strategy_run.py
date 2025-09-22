from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StrategyMode(str, enum.Enum):
    backtest = "backtest"
    paper = "paper"
    live = "live"


class StrategyRunStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    stopped = "stopped"


class StrategyRun(Base):
    __tablename__ = "strategy_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("strategies.id", ondelete="CASCADE"))
    mode: Mapped[StrategyMode] = mapped_column(Enum(StrategyMode, name="strategy_mode"), nullable=False)
    status: Mapped[StrategyRunStatus] = mapped_column(
        Enum(StrategyRunStatus, name="strategy_run_status"), default=StrategyRunStatus.running
    )
    parameters: Mapped[dict | None] = mapped_column(JSON)
    result_metrics: Mapped[dict | None] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    strategy: Mapped["Strategy"] = relationship(back_populates="runs")
    logs: Mapped[list["StrategyLog"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    execution_runs: Mapped[list["ExecutionRun"]] = relationship(back_populates="strategy_run")
