from __future__ import annotations

import uuid
from app.utils.dt import utcnow

from loguru import logger
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.strategy import Strategy
from app.models.strategy_run import StrategyRun
from app.schemas.strategy import StrategyLogLevelEnum, StrategyModeEnum
from app.services.strategy_dispatcher import StrategyDispatcher
from app.services.strategy_runner import StrategyRunner
from app.services.strategies import StrategyService


@celery_app.task(name="strategy.run", bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def trigger_strategy_run(self, user_id: str, strategy_id: str | None, context: dict | None = None) -> str:
    logger.info("[celery] dispatching strategy run", user_id=user_id, strategy_id=strategy_id)
    if strategy_id is None:
        logger.warning("No strategy_id provided to strategy.run task", user_id=user_id)
        return "skipped"

    context_payload = context or {}
    user_uuid = uuid.UUID(user_id)
    strategy_uuid = uuid.UUID(strategy_id)

    with SessionLocal() as session:  # type: Session
        dispatcher = StrategyDispatcher(session)
        run_read = dispatcher.dispatch(
            user_id=user_uuid,
            strategy_id=strategy_uuid,
            context=context_payload,
        )

        if run_read is None or getattr(run_read, "id", None) is None:
            logger.warning(
                "Strategy dispatch produced no run; skipping execution",
                user_id=user_id,
                strategy_id=strategy_id,
            )
            return "skipped"

        svc = StrategyService(session)
        strategy = session.get(Strategy, strategy_uuid)
        run_entity = session.get(StrategyRun, run_read.id)

        if strategy is None or run_entity is None:
            logger.error(
                "Strategy or run entity missing post-dispatch",
                strategy_id=strategy_id,
                run_id=getattr(run_read, "id", None),
            )
            svc.record_run_metrics(
                strategy_id=strategy_uuid,
                run_id=run_read.id,
                metrics={
                    "status": "failed",
                    "finished_at": utcnow(),
                    "error": "Strategy/run entity missing after dispatch",
                },
            )
            return "failed"

        mode = StrategyModeEnum(run_entity.mode.value)
        configuration = dict(run_entity.parameters or {})

        runner = StrategyRunner(session)

        try:
            result = runner.run(
                strategy=strategy,
                run=run_entity,
                user_id=user_uuid,
                mode=mode,
                configuration=configuration,
                extras=context_payload,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "[celery] strategy execution failed",
                run_id=str(run_entity.id),
                strategy_id=strategy_uuid,
                error=str(exc),
            )
            svc.record_run_metrics(
                strategy_id=strategy_uuid,
                run_id=run_entity.id,
                metrics={
                    "status": "failed",
                    "finished_at": utcnow(),
                    "error": str(exc),
                },
            )
            raise

        for level, message, log_context in result.logs:
            level_value = level.value if isinstance(level, StrategyLogLevelEnum) else str(level)
            try:
                level_enum = StrategyLogLevelEnum(level_value)
            except ValueError:
                level_enum = StrategyLogLevelEnum.info
            svc.log_event(
                strategy_id=strategy_uuid,
                run_id=run_entity.id,
                message=message,
                level=level_enum,
                context=log_context,
            )

        try:
            svc.record_run_metrics(
                strategy_id=strategy_uuid,
                run_id=run_entity.id,
                metrics=result.metrics,
            )
            logger.info(
                "[celery] strategy run completed",
                run_id=str(run_entity.id),
                execution_run_id=result.metrics.get("execution_run_id"),
                orders=result.metrics.get("orders"),
                pnl=result.metrics.get("pnl"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "[celery] failed to finalize strategy run metrics",
                run_id=str(run_entity.id),
                error=str(exc),
            )
            raise

    return "completed"
