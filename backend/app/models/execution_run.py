from __future__ import annotations

from typing import TYPE_CHECKING
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.execution_run_event import ExecutionRunEvent
    from app.models.strategy_run import StrategyRun


class ExecutionRun(Base):
    __tablename__ = "execution_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("execution_groups.id", ondelete="CASCADE"))
    strategy_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("strategy_runs.id", ondelete="SET NULL"))
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    payload: Mapped[dict | None] = mapped_column(JSON)

    group: Mapped["ExecutionGroup"] = relationship(back_populates="runs")
    strategy_run: Mapped["StrategyRun | None"] = relationship(back_populates="execution_runs")
    events: Mapped[list["ExecutionRunEvent"]] = relationship(back_populates="run", cascade="all, delete-orphan")
