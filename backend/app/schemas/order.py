from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.account_registry import LotAllocationPolicyEnum


class OrderSideEnum(str, Enum):
    BUY = "BUY"
    SELL = "SELL"




class OrderVarietyEnum(str, Enum):
    NORMAL = "NORMAL"
    STOPLOSS = "STOPLOSS"
    ROBO = "ROBO"


class ProductTypeEnum(str, Enum):
    DELIVERY = "DELIVERY"
    CARRYFORWARD = "CARRYFORWARD"
    MARGIN = "MARGIN"
    INTRADAY = "INTRADAY"
    BO = "BO"


class OrderDurationEnum(str, Enum):
    DAY = "DAY"
    IOC = "IOC"
class OrderTypeEnum(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatusEnum(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderCreate(BaseModel):
    broker_id: UUID = Field(..., description="Broker identifier returned from connect endpoint")
    symbol: str
    side: OrderSideEnum
    qty: int = Field(..., gt=0)
    order_type: OrderTypeEnum = OrderTypeEnum.MARKET
    price: Optional[float] = Field(default=None, gt=0)
    take_profit: Optional[float] = Field(default=None, gt=0)
    stop_loss: Optional[float] = Field(default=None, gt=0)
    strategy_id: Optional[UUID] = None
    exchange: Optional[str] = Field(default=None, description="Exchange hint such as NSE/BSE")
    symbol_token: Optional[str] = Field(default=None, description="Angel One symbol token")
    variety: Optional[OrderVarietyEnum] = Field(default=OrderVarietyEnum.NORMAL)
    product_type: Optional[ProductTypeEnum] = Field(default=None)
    duration: Optional[OrderDurationEnum] = Field(default=OrderDurationEnum.DAY)
    disclosed_quantity: Optional[int] = Field(default=None, ge=0)
    trigger_price: Optional[float] = Field(default=None, gt=0)
    squareoff: Optional[float] = Field(default=None, gt=0)
    trailing_stop_loss: Optional[float] = Field(default=None, gt=0)
    order_tag: Optional[str] = Field(default=None, max_length=20)


class OrderRead(BaseModel):
    id: UUID
    account_id: UUID
    symbol: str
    side: OrderSideEnum
    qty: int
    order_type: OrderTypeEnum
    price: Optional[float]
    status: OrderStatusEnum
    broker_order_id: Optional[str]
    tp_price: Optional[float]
    sl_price: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    orders: list[OrderRead]


class ExecutionAllocationResult(BaseModel):
    account_id: UUID
    broker_id: UUID
    lots: int
    quantity: int
    allocation_policy: LotAllocationPolicyEnum
    weight: float | None = None
    fixed_lots: int | None = None


class ExecutionLatencySummary(BaseModel):
    average_ms: float
    max_ms: float
    count: int
    p50_ms: float | None = None
    p95_ms: float | None = None


class ExecutionLegOutcome(BaseModel):
    account_id: UUID
    broker_id: UUID
    order_id: UUID
    status: str
    latency_ms: float | None = None
    message: str | None = None
    metadata: dict[str, Any] | None = None


class ExecutionGroupOrderCreate(BaseModel):
    symbol: str
    side: OrderSideEnum
    lots: int = Field(..., gt=0, description="Total lots to distribute across the execution group")
    lot_size: int = Field(default=1, gt=0, description="Number of units represented by a single lot")
    order_type: OrderTypeEnum = OrderTypeEnum.MARKET
    price: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)
    stop_loss: float | None = Field(default=None, gt=0)
    strategy_id: UUID | None = None


class ExecutionGroupOrderResponse(BaseModel):
    execution_run_id: UUID
    orders: list[OrderRead]
    allocation: list[ExecutionAllocationResult]
    total_lots: int
    lot_size: int
    latency: ExecutionLatencySummary | None = None
    leg_outcomes: list[ExecutionLegOutcome] = Field(default_factory=list)

