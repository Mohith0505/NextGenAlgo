from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import math

from sqlalchemy import Date, Select, cast, func, select, case
from sqlalchemy.orm import Session, joinedload

from app.models.account import Account
from app.models.broker import Broker
from app.models.order import Order
from app.models.position import Position
from app.models.strategy import Strategy
from app.models.trade import Trade
from app.models.execution_group import ExecutionGroup
from app.models.execution_run import ExecutionRun
from app.models.execution_run_event import ExecutionRunEvent
from app.schemas.analytics import (
    AnalyticsDashboardResponse,
    AnalyticsSummary,
    DailyPnlPoint,
    PositionRecord,
    StrategyPerformanceRow,
    TradeRecord,
)
from app.schemas.strategy import StrategyRunStatusEnum


class AnalyticsService:
    """Aggregates trading and strategy telemetry for analytics dashboards."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build_dashboard(
        self,
        user_id: uuid.UUID,
        *,
        days: int = 7,
        trade_limit: int = 20,
    ) -> AnalyticsDashboardResponse:
        summary = self._summary(user_id)
        daily_pnl = self._daily_pnl(user_id, days)
        strategies = self._strategy_rows(user_id)
        trades = self._recent_trades(user_id, limit=trade_limit)
        positions = self._open_positions(user_id)
        return AnalyticsDashboardResponse(
            summary=summary,
            daily_pnl=daily_pnl,
            strategies=strategies,
            recent_trades=trades,
            open_positions=positions,
        )

    def daily_pnl_series(self, user_id: uuid.UUID, *, days: int = 7) -> list[DailyPnlPoint]:
        return self._daily_pnl(user_id, days)

    def strategy_performance(self, user_id: uuid.UUID) -> list[StrategyPerformanceRow]:
        return self._strategy_rows(user_id)

    def recent_trade_records(self, user_id: uuid.UUID, *, limit: int = 20) -> list[TradeRecord]:
        return self._recent_trades(user_id, limit=limit)

    def position_snapshot(self, user_id: uuid.UUID) -> list[PositionRecord]:
        return self._open_positions(user_id)

    # ------------------------------------------------------------------
    # Summary helpers
    # ------------------------------------------------------------------
    def _summary(self, user_id: uuid.UUID) -> AnalyticsSummary:
        trade_subquery = self._trade_base_query(user_id).subquery()
        realized_total = self._decimal_to_float(
            self.session.execute(
                select(func.coalesce(func.sum(trade_subquery.c.pnl), 0))
            ).scalar_one()
            or 0
        )

        today_start = self._day_start()
        today_total = self._decimal_to_float(
            self.session.execute(
                select(func.coalesce(func.sum(trade_subquery.c.pnl), 0)).where(trade_subquery.c.timestamp >= today_start)
            ).scalar_one()
            or 0
        )

        total_trades = int(
            self.session.execute(
                select(func.count()).select_from(trade_subquery)
            ).scalar_one()
            or 0
        )

        position_subquery = self._position_query(user_id).subquery()
        unrealised_total = self._decimal_to_float(
            self.session.execute(
                select(func.coalesce(func.sum(position_subquery.c.pnl), 0))
            ).scalar_one()
            or 0
        )

        open_positions = int(
            self.session.execute(
                select(func.count()).select_from(position_subquery).where(position_subquery.c.qty != 0)
            ).scalar_one()
            or 0
        )

        run_counts_row = self.session.execute(
            select(
                func.count(ExecutionRun.id),
                func.coalesce(
                    func.sum(case((ExecutionRun.status != "completed", 1), else_=0)),
                    0,
                ),
            )
            .join(ExecutionGroup, ExecutionGroup.id == ExecutionRun.group_id)
            .where(ExecutionGroup.user_id == user_id)
        ).one_or_none()
        execution_run_count = int(run_counts_row[0]) if run_counts_row else 0
        failed_execution_runs = int(run_counts_row[1]) if run_counts_row else 0

        latency_rows = self.session.execute(
            select(ExecutionRunEvent.latency_ms)
            .join(ExecutionRun, ExecutionRun.id == ExecutionRunEvent.run_id)
            .join(ExecutionGroup, ExecutionGroup.id == ExecutionRun.group_id)
            .where(ExecutionGroup.user_id == user_id)
        ).all()
        latencies = [float(row[0]) for row in latency_rows if row[0] is not None]
        avg_execution_latency = (
            sum(latencies) / len(latencies) if latencies else None
        )
        p50_latency = self._percentile(latencies, 50.0) if latencies else None
        p95_latency = self._percentile(latencies, 95.0) if latencies else None

        status_rows = self.session.execute(
            select(ExecutionRunEvent.status, func.count())
            .join(ExecutionRun, ExecutionRun.id == ExecutionRunEvent.run_id)
            .join(ExecutionGroup, ExecutionGroup.id == ExecutionRun.group_id)
            .where(ExecutionGroup.user_id == user_id)
            .group_by(ExecutionRunEvent.status)
        ).all()
        leg_status_counts = {str(row[0]): int(row[1]) for row in status_rows}

        return AnalyticsSummary(
            realized_pnl=realized_total,
            unrealized_pnl=unrealised_total,
            today_realized_pnl=today_total,
            total_trades=total_trades,
            open_positions=open_positions,
            execution_run_count=execution_run_count,
            failed_execution_runs=failed_execution_runs,
            avg_execution_latency_ms=avg_execution_latency,
            p50_execution_latency_ms=p50_latency,
            p95_execution_latency_ms=p95_latency,
            execution_leg_status_counts=leg_status_counts,
            updated_at=datetime.utcnow(),
        )

    def _daily_pnl(self, user_id: uuid.UUID, days: int) -> list[DailyPnlPoint]:
        start = self._day_start() - timedelta(days=days - 1)
        trade_subquery = self._trade_base_query(user_id).where(Trade.timestamp >= start).subquery()
        stmt = (
            select(
                cast(trade_subquery.c.timestamp, Date).label("day"),
                func.coalesce(func.sum(trade_subquery.c.pnl), 0).label("pnl"),
                func.count(trade_subquery.c.id).label("trade_count"),
            )
            .group_by("day")
            .order_by("day")
        )
        points: list[DailyPnlPoint] = []
        for day, pnl, trade_count in self.session.execute(stmt):
            points.append(
                DailyPnlPoint(
                    date=day,
                    realized_pnl=self._decimal_to_float(pnl),
                    trade_count=int(trade_count or 0),
                )
            )
        return points

    def _strategy_rows(self, user_id: uuid.UUID) -> list[StrategyPerformanceRow]:
        stmt: Select[Strategy] = (
            select(Strategy)
            .where(Strategy.user_id == user_id)
            .options(joinedload(Strategy.runs))
        )
        strategies = self.session.execute(stmt).unique().scalars().all()
        rows: list[StrategyPerformanceRow] = []
        for strategy in strategies:
            runs = list(strategy.runs)
            cumulative_pnl = 0.0
            total_trades = 0
            last_run = None
            for run in runs:
                metrics = run.result_metrics or {}
                cumulative_pnl += float(metrics.get("pnl", 0.0))
                total_trades += int(metrics.get("trades", 0))
                if last_run is None or run.started_at > last_run.started_at:
                    last_run = run
            rows.append(
                StrategyPerformanceRow(
                    strategy_id=strategy.id,
                    strategy_name=strategy.name,
                    total_runs=len(runs),
                    cumulative_pnl=cumulative_pnl,
                    total_trades=total_trades,
                    last_run_status=StrategyRunStatusEnum(last_run.status.value)
                    if last_run is not None
                    else None,
                    last_run_started_at=last_run.started_at if last_run is not None else None,
                    last_run_finished_at=last_run.finished_at if last_run is not None else None,
                )
            )
        return rows

    def _recent_trades(self, user_id: uuid.UUID, *, limit: int) -> list[TradeRecord]:
        stmt = (
            self._trade_base_query(user_id)
            .options(joinedload(Trade.order))
            .order_by(Trade.timestamp.desc())
            .limit(limit)
        )
        trades = self.session.execute(stmt).unique().scalars().all()
        records: list[TradeRecord] = []
        for trade in trades:
            order = trade.order
            records.append(
                TradeRecord(
                    trade_id=trade.id,
                    order_id=trade.order_id,
                    symbol=order.symbol if order else "N/A",
                    qty=trade.qty,
                    pnl=self._decimal_to_float(trade.pnl) or 0.0,
                    timestamp=trade.timestamp,
                    strategy_id=order.strategy_id if order else None,
                )
            )
        return records

    def _open_positions(self, user_id: uuid.UUID) -> list[PositionRecord]:
        stmt = self._position_query(user_id).where(Position.qty != 0)
        positions = self.session.execute(stmt).unique().scalars().all()
        records: list[PositionRecord] = []
        for pos in positions:
            records.append(
                PositionRecord(
                    account_id=pos.account_id,
                    symbol=pos.symbol,
                    qty=pos.qty,
                    avg_price=self._decimal_to_float(pos.avg_price) or 0.0,
                    pnl=self._decimal_to_float(pos.pnl) or 0.0,
                    updated_at=pos.updated_at,
                )
            )
        return records

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def _trade_base_query(self, user_id: uuid.UUID) -> Select[Trade]:
        return (
            select(Trade)
            .join(Trade.order)
            .join(Order.account)
            .join(Account.broker)
            .where(Broker.user_id == user_id)
        )

    def _position_query(self, user_id: uuid.UUID) -> Select[Position]:
        return (
            select(Position)
            .join(Position.account)
            .join(Account.broker)
            .where(Broker.user_id == user_id)
        )

    @staticmethod
    def _percentile(values: list[float], pct: float) -> float | None:
        if not values:
            return None
        if len(values) == 1:
            return values[0]
        sorted_values = sorted(values)
        rank = (pct / 100) * (len(sorted_values) - 1)
        lower = math.floor(rank)
        upper = math.ceil(rank)
        if lower == upper:
            return sorted_values[int(rank)]
        lower_value = sorted_values[lower]
        upper_value = sorted_values[upper]
        fraction = rank - lower
        return lower_value + (upper_value - lower_value) * fraction

    @staticmethod
    def _decimal_to_float(value: Decimal | float | None) -> float | None:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        return value

    @staticmethod
    def _day_start() -> datetime:
        now = datetime.utcnow()
        return datetime(now.year, now.month, now.day)


__all__ = ["AnalyticsService"]


