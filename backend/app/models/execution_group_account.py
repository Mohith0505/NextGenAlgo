from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.execution_group import ExecutionGroup


class LotAllocationPolicy(str, enum.Enum):
    proportional = "proportional"
    fixed = "fixed"
    weighted = "weighted"


class ExecutionGroupAccount(Base):
    __tablename__ = "execution_group_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("execution_groups.id", ondelete="CASCADE"))
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"))
    allocation_policy: Mapped[LotAllocationPolicy] = mapped_column(
        Enum(LotAllocationPolicy, name="lot_allocation_policy"), default=LotAllocationPolicy.proportional
    )
    weight: Mapped[float | None] = mapped_column(Numeric(10, 4))
    fixed_lots: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    group: Mapped[ExecutionGroup] = relationship(back_populates="accounts")
    account: Mapped["Account"] = relationship(back_populates="execution_groups")
