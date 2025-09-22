from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ScheduledJobBase(BaseModel):
    name: str = Field(..., max_length=120)
    cron_expression: str = Field(..., description="Cron expression in crontab format")
    strategy_id: UUID | None = None
    is_active: bool = True
    context: dict[str, Any] | None = None


class ScheduledJobCreate(ScheduledJobBase):
    pass


class ScheduledJobRead(ScheduledJobBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    last_triggered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

