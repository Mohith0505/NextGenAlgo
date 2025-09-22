from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.strategy import StrategyRunStatusEnum


class DailyPnlPoint(BaseModel):
    date: date
    realized_pnl: float
    trade_count: int


class StrategyPerformanceRow(BaseModel):
    strategy_id: UUID
    strategy_name: str
    total_runs: int
    cumulative_pnl: float
    total_trades: int
    last_run_status: Optional[StrategyRunStatusEnum] = None
    last_run_started_at: Optional[datetime] = None
    last_run_finished_at: Optional[datetime] = None


class TradeRecord(BaseModel):
    trade_id: UUID
    order_id: UUID
    symbol: str
    qty: int
    pnl: float
    timestamp: datetime
    strategy_id: Optional[UUID] = None


class PositionRecord(BaseModel):
    account_id: UUID
    symbol: str
    qty: int
    avg_price: float
    pnl: float
    updated_at: datetime


class AnalyticsSummary(BaseModel):
    realized_pnl: float
    unrealized_pnl: float
    today_realized_pnl: float
    total_trades: int
    open_positions: int
    execution_run_count: int
    failed_execution_runs: int
    avg_execution_latency_ms: float | None = None
    p50_execution_latency_ms: float | None = None
    p95_execution_latency_ms: float | None = None
    execution_leg_status_counts: dict[str, int] = Field(default_factory=dict)
    updated_at: datetime


class AnalyticsDashboardResponse(BaseModel):
    summary: AnalyticsSummary
    daily_pnl: list[DailyPnlPoint] = Field(default_factory=list)
    strategies: list[StrategyPerformanceRow] = Field(default_factory=list)
    recent_trades: list[TradeRecord] = Field(default_factory=list)
    open_positions: list[PositionRecord] = Field(default_factory=list)
