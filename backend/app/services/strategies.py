from __future__ import annotations

import uuid
from datetime import datetime
from typing import Iterable

from loguru import logger
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.models.strategy import Strategy, StrategyStatus, StrategyType
from app.models.strategy_log import StrategyLog, StrategyLogLevel
from app.models.strategy_run import StrategyMode, StrategyRun, StrategyRunStatus
from app.schemas.strategy import (
    StrategyCreate,
    StrategyListResponse,
    StrategyLogListResponse,
    StrategyLogRead,
    StrategyLogLevelEnum,
    StrategyModeEnum,
    StrategyPerformanceResponse,
    StrategyRead,
    StrategyRunRead,
    StrategyRunStatusEnum,
    StrategyStartRequest,
    StrategyStatusEnum,
    StrategyStopRequest,
    StrategyTypeEnum,
    StrategyUpdate,
)


class StrategyService:
    """Encapsulates strategy lifecycle management and run bookkeeping."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _strategy_stmt(self, user_id: uuid.UUID) -> Select[tuple[Strategy]]:
        return (
            select(Strategy)
            .options(joinedload(Strategy.runs))
            .where(Strategy.user_id == user_id)
            .order_by(Strategy.created_at.asc())
        )

    def _get_strategy(self, user_id: uuid.UUID, strategy_id: uuid.UUID | str) -> Strategy | None:
        stmt = (
            select(Strategy)
            .options(joinedload(Strategy.runs))
            .where(Strategy.user_id == user_id, Strategy.id == uuid.UUID(str(strategy_id)))
            .limit(1)
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def _active_run(self, strategy: Strategy) -> StrategyRun | None:
        for run in sorted(strategy.runs, key=lambda r: r.started_at, reverse=True):
            if run.status in {StrategyRunStatus.running, StrategyRunStatus.queued}:
                return run
        return None

    def _latest_run(self, strategy: Strategy) -> StrategyRun | None:
        if not strategy.runs:
            return None
        return max(strategy.runs, key=lambda run: run.started_at)

    def _to_strategy_read(self, strategy: Strategy) -> StrategyRead:
        latest_run = self._latest_run(strategy)
        return StrategyRead(
            id=strategy.id,
            name=strategy.name,
            type=StrategyTypeEnum(strategy.type.value),
            status=StrategyStatusEnum(strategy.status.value),
            params=strategy.params or {},
            created_at=strategy.created_at,
            latest_run=self._to_run_read(latest_run) if latest_run else None,
        )

    def _to_run_read(self, run: StrategyRun | None) -> StrategyRunRead | None:
        if run is None:
            return None
        return StrategyRunRead(
            id=run.id,
            mode=StrategyModeEnum(run.mode.value),
            status=StrategyRunStatusEnum(run.status.value),
            started_at=run.started_at,
            finished_at=run.finished_at,
            result_metrics=run.result_metrics or {},
        )

    def _to_log_read(self, log: StrategyLog) -> StrategyLogRead:
        return StrategyLogRead(
            id=log.id,
            run_id=log.run_id,
            level=StrategyLogLevelEnum(log.level.value),
            message=log.message,
            context=log.context or {},
            created_at=log.created_at,
        )

    def _ensure_strategy(self, user_id: uuid.UUID, strategy_id: uuid.UUID | str) -> Strategy:
        strategy = self._get_strategy(user_id, strategy_id)
        if strategy is None:
            raise ValueError("Strategy not found")
        return strategy

    # ------------------------------------------------------------------
    # Strategy CRUD
    # ------------------------------------------------------------------
    def create_strategy(self, user_id: uuid.UUID, payload: StrategyCreate) -> StrategyRead:
        strategy = Strategy(
            user_id=user_id,
            name=payload.name,
            type=StrategyType(payload.type.value),
            params=payload.params or {},
        )
        self.session.add(strategy)
        self.session.commit()
        self.session.refresh(strategy)
        return self._to_strategy_read(strategy)

    def list_strategies(self, user_id: uuid.UUID) -> StrategyListResponse:
        stmt = self._strategy_stmt(user_id)
        strategies: Iterable[Strategy] = self.session.execute(stmt).unique().scalars()
        return StrategyListResponse(strategies=[self._to_strategy_read(s) for s in strategies])

    def get_strategy(self, user_id: uuid.UUID, strategy_id: uuid.UUID | str) -> StrategyRead:
        strategy = self._ensure_strategy(user_id, strategy_id)
        return self._to_strategy_read(strategy)

    def update_strategy(
        self, user_id: uuid.UUID, strategy_id: uuid.UUID | str, payload: StrategyUpdate
    ) -> StrategyRead:
        strategy = self._ensure_strategy(user_id, strategy_id)
        if payload.name is not None:
            strategy.name = payload.name
        if payload.params is not None:
            strategy.params = payload.params
        if payload.status is not None:
            strategy.status = StrategyStatus(payload.status.value)
        self.session.add(strategy)
        self.session.commit()
        self.session.refresh(strategy)
        return self._to_strategy_read(strategy)

    def delete_strategy(self, user_id: uuid.UUID, strategy_id: uuid.UUID | str) -> bool:
        strategy = self._ensure_strategy(user_id, strategy_id)
        self.session.delete(strategy)
        self.session.commit()
        return True

    # ------------------------------------------------------------------
    # Strategy execution lifecycle
    # ------------------------------------------------------------------
    def start_strategy(
        self, user_id: uuid.UUID, strategy_id: uuid.UUID | str, payload: StrategyStartRequest
    ) -> StrategyRunRead:
        strategy = self._ensure_strategy(user_id, strategy_id)
        existing = self._active_run(strategy)
        if existing is not None:
            raise ValueError("Strategy already running")
        base_configuration = dict(strategy.params or {})
        override_configuration = dict(payload.configuration or {})
        merged_configuration = {**base_configuration, **override_configuration}

        run = StrategyRun(
            strategy_id=strategy.id,
            mode=StrategyMode(payload.mode.value),
            status=StrategyRunStatus.running,
            parameters=merged_configuration,
            result_metrics={"pnl": 0.0, "trades": 0},
            started_at=datetime.utcnow(),
        )
        strategy.status = StrategyStatus.active
        self.session.add(run)
        self.session.add(strategy)
        self.session.flush()

        log_context = {
            "configuration": merged_configuration,
            "source": override_configuration.get("source"),
            "mode": payload.mode.value,
        }
        self._append_log(
            strategy_id=strategy.id,
            run_id=run.id,
            level=StrategyLogLevel.info,
            message=f"Strategy started in {payload.mode.value} mode",
            context={k: v for k, v in log_context.items() if v is not None},
        )
        self.session.commit()
        self.session.refresh(run)
        self.session.refresh(strategy)

        context_payload = {
            "mode": payload.mode.value,
            "configuration": merged_configuration,
            "source": override_configuration.get("source", "manual"),
        }
        try:
            from app.tasks.strategy import trigger_strategy_run  # local import to avoid circular dependency

            trigger_strategy_run.delay(
                user_id=str(user_id),
                strategy_id=str(strategy.id),
                context=context_payload,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Falling back to synchronous strategy execution",
                strategy_id=str(strategy.id),
                run_id=str(run.id),
                error=str(exc),
            )
            try:
                trigger_strategy_run.apply(
                    args=(str(user_id), str(strategy.id)),
                    kwargs={"context": context_payload},
                )
            except Exception as inner_exc:  # noqa: BLE001
                logger.error(
                    "Failed to execute strategy run",
                    strategy_id=str(strategy.id),
                    run_id=str(run.id),
                    error=str(inner_exc),
                )

        return self._to_run_read(run)

    def stop_strategy(
        self, user_id: uuid.UUID, strategy_id: uuid.UUID | str, payload: StrategyStopRequest | None = None
    ) -> StrategyRunRead:
        strategy = self._ensure_strategy(user_id, strategy_id)
        run = self._active_run(strategy)
        if run is None:
            raise ValueError("Strategy is not running")
        run.status = StrategyRunStatus.stopped
        run.finished_at = datetime.utcnow()
        run.result_metrics = run.result_metrics or {"pnl": 0.0, "trades": 0}
        strategy.status = StrategyStatus.stopped
        self.session.add(run)
        self.session.add(strategy)
        self.session.flush()
        reason = payload.reason if payload else None
        context = {"reason": reason} if reason else None
        self._append_log(
            strategy_id=strategy.id,
            run_id=run.id,
            level=StrategyLogLevel.info,
            message="Strategy stopped",
            context=context,
        )
        self.session.commit()
        self.session.refresh(run)
        self.session.refresh(strategy)
        return self._to_run_read(run)

    def record_run_metrics(
        self,
        strategy_id: uuid.UUID,
        run_id: uuid.UUID,
        metrics: dict,
    ) -> StrategyRunRead:
        run = self.session.get(StrategyRun, run_id)
        if run is None or run.strategy_id != strategy_id:
            raise ValueError("Strategy run not found")
        run.result_metrics = {**(run.result_metrics or {}), **metrics}
        if metrics.get("status"):
            run.status = StrategyRunStatus(metrics["status"])
        if metrics.get("finished_at"):
            run.finished_at = metrics["finished_at"]
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return self._to_run_read(run)

    # ------------------------------------------------------------------
    # Logs and analytics
    # ------------------------------------------------------------------
    def get_logs(
        self, user_id: uuid.UUID, strategy_id: uuid.UUID | str, *, limit: int = 100
    ) -> StrategyLogListResponse:
        strategy = self._ensure_strategy(user_id, strategy_id)
        stmt = (
            select(StrategyLog)
            .where(StrategyLog.strategy_id == strategy.id)
            .order_by(StrategyLog.created_at.desc())
            .limit(limit)
        )
        logs: Iterable[StrategyLog] = self.session.execute(stmt).unique().scalars()
        return StrategyLogListResponse(logs=[self._to_log_read(log) for log in logs])

    def get_performance(
        self, user_id: uuid.UUID, strategy_id: uuid.UUID | str
    ) -> StrategyPerformanceResponse:
        strategy = self._ensure_strategy(user_id, strategy_id)
        stmt = (
            select(StrategyRun)
            .where(StrategyRun.strategy_id == strategy.id)
            .order_by(StrategyRun.started_at.desc())
        )
        runs: list[StrategyRun] = list(self.session.execute(stmt).unique().scalars())
        lifetime_pnl = 0.0
        total_trades = 0
        for run in runs:
            metrics = run.result_metrics or {}
            lifetime_pnl += float(metrics.get("pnl", 0.0))
            total_trades += int(metrics.get("trades", 0))
        last_run = runs[0] if runs else None
        return StrategyPerformanceResponse(
            strategy_id=strategy.id,
            lifetime_pnl=lifetime_pnl,
            total_trades=total_trades,
            last_run=self._to_run_read(last_run) if last_run else None,
        )

    # ------------------------------------------------------------------
    # Internal logging helper
    # ------------------------------------------------------------------
    def _append_log(
        self,
        *,
        strategy_id: uuid.UUID,
        run_id: uuid.UUID | None,
        level: StrategyLogLevel,
        message: str,
        context: dict | None = None,
    ) -> StrategyLog:
        log = StrategyLog(
            strategy_id=strategy_id,
            run_id=run_id,
            level=level,
            message=message,
            context=context,
            created_at=datetime.utcnow(),
        )
        self.session.add(log)
        return log

    # ------------------------------------------------------------------
    # External helpers
    # ------------------------------------------------------------------
    def log_event(
        self,
        *,
        strategy_id: uuid.UUID,
        run_id: uuid.UUID | None,
        message: str,
        level: StrategyLogLevelEnum = StrategyLogLevelEnum.info,
        context: dict | None = None,
    ) -> StrategyLogRead:
        log = self._append_log(
            strategy_id=strategy_id,
            run_id=run_id,
            level=StrategyLogLevel(level.value),
            message=message,
            context=context,
        )
        self.session.commit()
        self.session.refresh(log)
        return self._to_log_read(log)


__all__ = ["StrategyService"]
