from __future__ import annotations
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RmsRule(Base):
    __tablename__ = "rms_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    max_loss: Mapped[float | None] = mapped_column(Numeric(18, 2))
    max_lots: Mapped[int | None] = mapped_column(Integer)
    profit_lock: Mapped[float | None] = mapped_column(Numeric(18, 2))
    trailing_sl: Mapped[float | None] = mapped_column(Numeric(18, 2))
    max_daily_loss: Mapped[float | None] = mapped_column(Numeric(18, 2))
    max_daily_lots: Mapped[int | None] = mapped_column(Integer)
    exposure_limit: Mapped[float | None] = mapped_column(Numeric(18, 2))
    margin_buffer_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    drawdown_limit: Mapped[float | None] = mapped_column(Numeric(18, 2))
    auto_square_off_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_square_off_buffer_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    auto_hedge_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_hedge_ratio: Mapped[float | None] = mapped_column(Numeric(5, 2))
    notify_email: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_telegram: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    owner: Mapped["User"] = relationship(back_populates="rms_rules")
