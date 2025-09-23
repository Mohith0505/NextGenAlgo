from __future__ import annotations
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BrokerStatus(str, enum.Enum):
    connected = "connected"
    disconnected = "disconnected"
    expired = "expired"
    error = "error"


class Broker(Base):
    __tablename__ = "brokers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    broker_name: Mapped[str] = mapped_column(String(100), nullable=False)
    client_code: Mapped[str] = mapped_column(String(64), nullable=False)
    session_token: Mapped[str | None] = mapped_column(String(512))
    credentials_encrypted: Mapped[str | None] = mapped_column(Text())
    status: Mapped[BrokerStatus] = mapped_column(Enum(BrokerStatus, name="broker_status"), default=BrokerStatus.connected)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="brokers")
    accounts: Mapped[list["Account"]] = relationship(back_populates="broker", cascade="all, delete-orphan")

    @property
    def has_saved_credentials(self) -> bool:
        return bool(self.credentials_encrypted)
