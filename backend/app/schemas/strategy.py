from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StrategyTypeEnum(str, Enum):
    built_in = "built-in"
    custom = "custom"
    connector = "connector"


class StrategyStatusEnum(str, Enum):
    active = "active"
    stopped = "stopped"


class StrategyModeEnum(str, Enum):
    backtest = "backtest"
    paper = "paper"
    live = "live"


class StrategyRunStatusEnum(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    stopped = "stopped"


class StrategyLogLevelEnum(str, Enum):
    info = "info"
    warning = "warning"
    error = "error"


class StrategyBase(BaseModel):
    name: str
    type: StrategyTypeEnum
    params: dict[str, Any] = Field(default_factory=dict)


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    params: Optional[dict[str, Any]] = None
    status: Optional[StrategyStatusEnum] = None


class StrategyRunRead(BaseModel):
    id: UUID
    mode: StrategyModeEnum
    status: StrategyRunStatusEnum
    started_at: datetime
    finished_at: Optional[datetime] = None
    result_metrics: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class StrategyRead(BaseModel):
    id: UUID
    name: str
    type: StrategyTypeEnum
    status: StrategyStatusEnum
    params: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    latest_run: Optional[StrategyRunRead] = None


class StrategyListResponse(BaseModel):
    strategies: list[StrategyRead]


class StrategyStartRequest(BaseModel):
    mode: StrategyModeEnum
    configuration: dict[str, Any] = Field(default_factory=dict)


class StrategyStopRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=255)


class StrategyLogRead(BaseModel):
    id: UUID
    run_id: Optional[UUID]
    level: StrategyLogLevelEnum
    message: str
    context: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StrategyLogListResponse(BaseModel):
    logs: list[StrategyLogRead]


class StrategyPerformanceResponse(BaseModel):
    strategy_id: UUID
    lifetime_pnl: float
    total_trades: int
    last_run: Optional[StrategyRunRead] = None
