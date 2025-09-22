from __future__ import annotations
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    broker_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brokers.id", ondelete="CASCADE"))
    margin: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    broker: Mapped["Broker"] = relationship(back_populates="accounts")
    positions: Mapped[list["Position"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    execution_groups: Mapped[list["ExecutionGroupAccount"]] = relationship(back_populates="account", cascade="all, delete-orphan")
