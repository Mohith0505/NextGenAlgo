from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ExecutionModeEnum(str, Enum):
    sync = "sync"
    parallel = "parallel"
    staggered = "staggered"


class LotAllocationPolicyEnum(str, Enum):
    proportional = "proportional"
    fixed = "fixed"
    weighted = "weighted"


class ExecutionGroupBase(BaseModel):
    name: str
    description: str | None = None
    mode: ExecutionModeEnum = ExecutionModeEnum.parallel


class ExecutionGroupCreate(ExecutionGroupBase):
    pass


class ExecutionGroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    mode: ExecutionModeEnum | None = None


class ExecutionGroupAccountCreate(BaseModel):
    account_id: UUID
    allocation_policy: LotAllocationPolicyEnum = LotAllocationPolicyEnum.proportional
    weight: float | None = Field(default=None, ge=0)
    fixed_lots: int | None = Field(default=None, ge=0)


class ExecutionGroupAccountUpdate(BaseModel):
    allocation_policy: LotAllocationPolicyEnum | None = None
    weight: float | None = Field(default=None, ge=0)
    fixed_lots: int | None = Field(default=None, ge=0)


class ExecutionGroupAccountRead(BaseModel):
    id: UUID
    account_id: UUID
    allocation_policy: LotAllocationPolicyEnum
    weight: float | None = None
    fixed_lots: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutionGroupRead(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    mode: ExecutionModeEnum
    created_at: datetime
    updated_at: datetime
    accounts: list[ExecutionGroupAccountRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ExecutionRunEventRead(BaseModel):
    id: UUID
    run_id: UUID
    account_id: UUID | None = None
    broker_id: UUID | None = None
    order_id: UUID | None = None
    status: str
    latency_ms: float | None = None
    requested_at: datetime
    completed_at: datetime | None = None
    message: str | None = None
    metadata: dict[str, Any] | None = Field(default=None, alias="event_metadata")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ExecutionRunRead(BaseModel):
    id: UUID
    group_id: UUID
    strategy_run_id: UUID | None = None
    requested_at: datetime
    completed_at: datetime | None = None
    status: str
    payload: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class ExecutionAllocationPreview(BaseModel):
    account_id: UUID
    broker_id: UUID
    lots: int
    allocation_policy: LotAllocationPolicyEnum
    weight: float | None = None
    fixed_lots: int | None = None

