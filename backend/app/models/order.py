from __future__ import annotations
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrderSide(str, enum.Enum):
    buy = "BUY"
    sell = "SELL"


class OrderType(str, enum.Enum):
    market = "MARKET"
    limit = "LIMIT"


class OrderStatus(str, enum.Enum):
    pending = "PENDING"
    filled = "FILLED"
    cancelled = "CANCELLED"
    rejected = "REJECTED"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"))
    strategy_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("strategies.id"))
    symbol: Mapped[str] = mapped_column(String(100), nullable=False)
    side: Mapped[OrderSide] = mapped_column(Enum(OrderSide, name="order_side"), nullable=False)
    qty: Mapped[int] = mapped_column(nullable=False)
    order_type: Mapped[OrderType] = mapped_column(Enum(OrderType, name="order_type"), default=OrderType.market)
    price: Mapped[float | None] = mapped_column(Numeric(18, 2))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"), default=OrderStatus.pending
    )
    broker_order_id: Mapped[str | None] = mapped_column(String(100))
    tp_price: Mapped[float | None] = mapped_column(Numeric(18, 2))
    sl_price: Mapped[float | None] = mapped_column(Numeric(18, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    account: Mapped["Account"] = relationship(back_populates="orders")
    strategy: Mapped["Strategy"] = relationship(back_populates="orders")
    trades: Mapped[list["Trade"]] = relationship(back_populates="order", cascade="all, delete-orphan")
