from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RmsConfigBase(BaseModel):
    max_loss: Optional[float] = Field(default=None, description="Legacy cap on cumulative loss")
    max_lots: Optional[int] = Field(default=None, description="Maximum lots allowed per single order")
    profit_lock: Optional[float] = Field(default=None, description="Lock-in profit threshold")
    trailing_sl: Optional[float] = Field(default=None, description="Trailing stop value")
    max_daily_loss: Optional[float] = Field(default=None, description="Maximum allowable loss in a trading day")
    max_daily_lots: Optional[int] = Field(default=None, description="Maximum cumulative lots per trading day")
    exposure_limit: Optional[float] = Field(default=None, description="Notional exposure cap across positions")
    margin_buffer_pct: Optional[float] = Field(default=None, description="Percentage of margin that must remain after pre-trade checks")
    drawdown_limit: Optional[float] = Field(default=None, description="Maximum equity drawdown allowed before automation triggers")
    auto_square_off_enabled: Optional[bool] = Field(default=None, description="Automatically square off positions when limits are breached")
    auto_square_off_buffer_pct: Optional[float] = Field(default=None, description="Buffer percentage applied before auto square-off")
    auto_hedge_enabled: Optional[bool] = Field(default=None, description="Automatically place hedge orders when risk thresholds are breached")
    auto_hedge_ratio: Optional[float] = Field(default=None, description="Ratio used to size hedge positions")
    notify_email: Optional[bool] = Field(default=None, description="Send RMS email alerts")
    notify_telegram: Optional[bool] = Field(default=None, description="Send RMS Telegram alerts")


class RmsConfigRead(RmsConfigBase):
    updated_at: datetime


class RmsConfigUpdate(RmsConfigBase):
    pass


class RmsStatusRead(BaseModel):
    day_pnl: float = 0.0
    total_lots_today: int = 0
    max_daily_lots: Optional[int] = None
    lots_remaining: Optional[int] = None
    max_daily_loss: Optional[float] = None
    loss_remaining: Optional[float] = None
    notional_exposure: float = 0.0
    exposure_limit: Optional[float] = None
    available_margin: float = 0.0
    margin_buffer_pct: Optional[float] = None
    alerts: list[str] = Field(default_factory=list)
    automations: list[str] = Field(default_factory=list)


class PositionSnapshot(BaseModel):
    account_id: UUID
    symbol: str
    qty: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RmsSquareOffResponse(BaseModel):
    triggered: bool
    message: str
    positions: list[PositionSnapshot] = Field(default_factory=list)


class RmsPretradeResult(BaseModel):
    passed: bool
    detail: Optional[str] = None
