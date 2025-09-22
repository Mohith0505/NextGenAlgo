from __future__ import annotations

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.api.dependencies import get_analytics_service, get_current_user
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsDashboardResponse,
    DailyPnlPoint,
    PositionRecord,
    StrategyPerformanceRow,
    TradeRecord,
)
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _require_user(current_user: Optional[User]) -> User:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return current_user


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
def analytics_dashboard(
    days: int = Query(default=7, ge=1, le=60),
    trade_limit: int = Query(default=20, ge=1, le=200),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> AnalyticsDashboardResponse:
    user = _require_user(current_user)
    return analytics_service.build_dashboard(user.id, days=days, trade_limit=trade_limit)


@router.get("/daily", response_model=list[DailyPnlPoint])
def analytics_daily_pnl(
    days: int = Query(default=7, ge=1, le=60),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> list[DailyPnlPoint]:
    user = _require_user(current_user)
    return analytics_service.daily_pnl_series(user.id, days=days)


@router.get("/strategies", response_model=list[StrategyPerformanceRow])
def analytics_strategy_performance(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> list[StrategyPerformanceRow]:
    user = _require_user(current_user)
    return analytics_service.strategy_performance(user.id)


@router.get("/trades", response_model=list[TradeRecord])
def analytics_recent_trades(
    limit: int = Query(default=20, ge=1, le=200),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> list[TradeRecord]:
    user = _require_user(current_user)
    return analytics_service.recent_trade_records(user.id, limit=limit)


@router.get("/positions", response_model=list[PositionRecord])
def analytics_open_positions(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> list[PositionRecord]:
    user = _require_user(current_user)
    return analytics_service.position_snapshot(user.id)


@router.get("/exports/daily-pnl")
def export_daily_pnl(
    days: int = Query(default=7, ge=1, le=60),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> Response:
    user = _require_user(current_user)
    points = analytics_service.daily_pnl_series(user.id, days=days)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "realized_pnl", "trade_count"])
    for point in points:
        writer.writerow([point.date.isoformat(), point.realized_pnl, point.trade_count])

    content = buffer.getvalue()
    filename = f"daily_pnl_{days}d.csv"
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/exports/latency-summary")
def export_latency_summary(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> dict[str, float | int | None]:
    user = _require_user(current_user)
    summary = analytics_service.build_dashboard(user.id).summary
    return {
        "average_ms": summary.avg_execution_latency_ms,
        "p50_ms": summary.p50_execution_latency_ms,
        "p95_ms": summary.p95_execution_latency_ms,
        "leg_status_counts": summary.execution_leg_status_counts,
    }


@router.get("/exports/leg-status")
def export_leg_status(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> list[dict[str, str | int]]:
    user = _require_user(current_user)
    summary = analytics_service.build_dashboard(user.id).summary
    entries = summary.execution_leg_status_counts
    return [
        {"status": status, "count": count}
        for status, count in entries.items()
    ]
