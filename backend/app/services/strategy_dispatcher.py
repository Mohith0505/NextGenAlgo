from __future__ import annotations

import uuid
from typing import Any

from loguru import logger
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.schemas.strategy import StrategyModeEnum, StrategyStartRequest
from app.services.strategies import StrategyService


class StrategyDispatcher:
    """Coordinates strategy runs triggered by external events."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.strategy_service = StrategyService(session)

    def dispatch(
        self,
        *,
        user_id: uuid.UUID,
        strategy_id: uuid.UUID | None,
        context: dict[str, Any] | None = None,
    ) -> Any | None:
        if strategy_id is None:
            logger.warning("No strategy_id provided for dispatch", context=context)
            return None
        try:
            strategy = self.session.get(Strategy, strategy_id)
            if strategy is None or strategy.user_id != user_id:
                logger.error(
                    "Strategy not found for user",
                    strategy_id=strategy_id,
                    user_id=user_id,
                )
                return None

            configuration = self._merge_configuration(strategy.params or {}, context or {})
            mode = self._resolve_mode(context or {}, configuration)
            start_request = self._build_start_request(mode=mode, configuration=configuration)
            run = self.strategy_service.start_strategy(user_id, strategy_id, start_request)
            logger.info(
                "Strategy run queued",
                strategy_id=strategy_id,
                run_id=run.id if run else None,
                mode=mode.value,
            )
            return run
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to dispatch strategy", strategy_id=strategy_id, error=str(exc))
            return None

    @staticmethod
    def _build_start_request(*, mode: StrategyModeEnum, configuration: dict[str, Any]) -> StrategyStartRequest:
        return StrategyStartRequest(mode=mode, configuration=configuration)

    @staticmethod
    def _merge_configuration(strategy_params: dict[str, Any] | None, context: dict[str, Any]) -> dict[str, Any]:
        configuration = dict(strategy_params or {})
        context_config = context.get("configuration")
        if isinstance(context_config, dict):
            configuration.update(context_config)

        flattened = {
            key: value
            for key, value in context.items()
            if key not in {"configuration", "mode"}
        }
        if flattened:
            configuration.update(flattened)
        return configuration

    @staticmethod
    def _resolve_mode(context: dict[str, Any], configuration: dict[str, Any]) -> StrategyModeEnum:
        mode_value = context.get("mode")
        if mode_value is None and "mode" in configuration:
            mode_value = configuration.pop("mode")

        if isinstance(mode_value, StrategyModeEnum):
            return mode_value
        if mode_value is not None:
            try:
                return StrategyModeEnum(str(mode_value))
            except ValueError:
                logger.warning("Unsupported mode provided, defaulting to paper", mode=mode_value)
        return StrategyModeEnum.paper


__all__ = ["StrategyDispatcher"]
