from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.models.strategy_run import StrategyRun
from app.schemas.order import ExecutionGroupOrderCreate, OrderSideEnum, OrderTypeEnum
from app.schemas.strategy import StrategyLogLevelEnum, StrategyModeEnum
from app.services.brokers import BrokerService


@dataclass
class StrategyRunResult:
    metrics: dict[str, Any]
    logs: list[tuple[StrategyLogLevelEnum, str, dict[str, Any] | None]]
    execution_summary: dict[str, Any] | None = None


class StrategyRunner:
    """Executes strategy runs in paper/live/backtest modes."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.broker_service = BrokerService(session)

    def run(
        self,
        *,
        strategy: Strategy,
        run: StrategyRun,
        user_id: uuid.UUID,
        mode: StrategyModeEnum,
        configuration: dict[str, Any],
        extras: dict[str, Any] | None = None,
    ) -> StrategyRunResult:
        logger.debug(
            "Executing strategy run",
            strategy_id=strategy.id,
            run_id=run.id,
            mode=mode.value,
            configuration=configuration,
        )

        extras = extras or {}
        base_metrics: dict[str, Any] = {
            "status": "completed",
            "finished_at": datetime.utcnow(),
            "pnl": float(extras.get("expected_pnl", 0.0)),
            "trades": int(extras.get("trades", 0) or 0),
        }
        logs: list[tuple[StrategyLogLevelEnum, str, dict[str, Any] | None]] = []
        execution_summary: dict[str, Any] | None = None

        if mode in {StrategyModeEnum.paper, StrategyModeEnum.live}:
            execution_summary = self._execute_live_or_paper(
                user_id=user_id,
                strategy=strategy,
                run=run,
                configuration=configuration,
                mode=mode,
            )
            if execution_summary is not None:
                order_count = execution_summary.get("order_count")
                if order_count is not None:
                    base_metrics["orders"] = order_count
                    base_metrics["trades"] = order_count
                for key in ("total_lots", "lot_size", "latency_ms", "leg_status_counts"):
                    value = execution_summary.get(key)
                    if value is not None:
                        base_metrics[key] = value
                if execution_summary.get("execution_run_id") is not None:
                    base_metrics["execution_run_id"] = str(execution_summary["execution_run_id"])

                logs.append(
                    (
                        StrategyLogLevelEnum.info,
                        f"{mode.value.title()} execution dispatched",
                        {
                            "execution_run_id": str(execution_summary.get("execution_run_id")),
                            "orders": execution_summary.get("order_count"),
                            "symbol": execution_summary.get("symbol"),
                            "side": execution_summary.get("side"),
                            "lots": execution_summary.get("total_lots"),
                        },
                    )
                )
        elif mode == StrategyModeEnum.backtest:
            execution_summary = self._simulate_backtest(configuration)
            base_metrics.update(
                {
                    "orders": execution_summary.get("order_count", 0),
                    "trades": execution_summary.get("order_count", 0),
                    "pnl": execution_summary.get("pnl", base_metrics.get("pnl", 0.0)),
                }
            )
            logs.extend(
                [
                    (
                        StrategyLogLevelEnum.info,
                        "Backtest simulation executed",
                        {
                            "entry_price": execution_summary.get("entry_price"),
                            "exit_price": execution_summary.get("exit_price"),
                            "pnl": execution_summary.get("pnl"),
                            "quantity": execution_summary.get("quantity"),
                        },
                    ),
                    (
                        StrategyLogLevelEnum.info,
                        "Backtest simulation completed",
                        {
                            "orders": execution_summary.get("order_count"),
                            "side": execution_summary.get("side"),
                        },
                    ),
                ]
            )
        else:
            raise ValueError(f"Unsupported strategy mode: {mode}")

        base_metrics["finished_at"] = datetime.utcnow()
        return StrategyRunResult(metrics=base_metrics, logs=logs, execution_summary=execution_summary)

    def _execute_live_or_paper(
        self,
        *,
        user_id: uuid.UUID,
        strategy: Strategy,
        run: StrategyRun,
        configuration: dict[str, Any],
        mode: StrategyModeEnum,
    ) -> dict[str, Any] | None:
        execution_group_raw = self._get_value(configuration, "execution_group_id", "executionGroupId", "group_id")
        if execution_group_raw is None:
            raise ValueError("execution_group_id is required for live/paper execution")

        try:
            execution_group_id = uuid.UUID(str(execution_group_raw))
        except ValueError as exc:
            raise ValueError("execution_group_id must be a valid UUID") from exc

        symbol = configuration.get("symbol")
        side_raw = configuration.get("side")
        lots_raw = self._get_value(configuration, "lots", "total_lots")
        lot_size_raw = self._get_value(configuration, "lot_size", "lotSize")
        order_type_raw = self._get_value(configuration, "order_type", "orderType") or OrderTypeEnum.MARKET.value
        price = configuration.get("price")
        take_profit = self._get_value(configuration, "take_profit", "takeProfit")
        stop_loss = self._get_value(configuration, "stop_loss", "stopLoss")

        if symbol is None:
            raise ValueError("symbol is required for live/paper execution")
        if side_raw is None:
            raise ValueError("side is required for live/paper execution")
        if lots_raw is None:
            raise ValueError("lots is required for live/paper execution")

        try:
            side = OrderSideEnum(str(side_raw).upper())
        except ValueError as exc:
            raise ValueError(f"Unsupported order side: {side_raw}") from exc

        try:
            order_type = OrderTypeEnum(str(order_type_raw).upper())
        except ValueError as exc:
            raise ValueError(f"Unsupported order type: {order_type_raw}") from exc

        try:
            lots = int(lots_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("lots must be an integer") from exc

        lot_size = 1
        if lot_size_raw is not None:
            try:
                lot_size = int(lot_size_raw)
            except (TypeError, ValueError) as exc:
                raise ValueError("lot_size must be an integer") from exc

        payload = ExecutionGroupOrderCreate(
            symbol=str(symbol),
            side=side,
            lots=lots,
            lot_size=lot_size,
            order_type=order_type,
            price=price,
            take_profit=take_profit,
            stop_loss=stop_loss,
            strategy_id=strategy.id,
        )

        logger.info(
            "Dispatching %s strategy order",
            mode.value,
            strategy_id=strategy.id,
            run_id=run.id,
            execution_group_id=execution_group_id,
            symbol=symbol,
            side=side.value,
            lots=payload.lots,
            lot_size=payload.lot_size,
        )

        response = self.broker_service.place_execution_group_order(
            user_id=user_id,
            group_id=execution_group_id,
            payload=payload,
            strategy_run_id=run.id,
        )

        leg_status_counts: dict[str, int] = {}
        for leg in response.leg_outcomes:
            status = (leg.status or "unknown").lower()
            leg_status_counts[status] = leg_status_counts.get(status, 0) + 1

        latency_ms = response.latency.average_ms if response.latency else None

        summary = {
            "execution_run_id": response.execution_run_id,
            "order_count": len(response.orders),
            "total_lots": response.total_lots,
            "lot_size": response.lot_size,
            "latency_ms": latency_ms,
            "leg_status_counts": leg_status_counts,
            "symbol": payload.symbol,
            "side": payload.side.value,
        }

        logger.info(
            "Strategy execution completed",
            strategy_id=strategy.id,
            run_id=run.id,
            execution_run_id=response.execution_run_id,
            orders=summary["order_count"],
            latency_ms=latency_ms,
        )

        return summary

    @staticmethod
    def _simulate_backtest(configuration: dict[str, Any]) -> dict[str, Any]:
        symbol = configuration.get("symbol")
        side_raw = configuration.get("side", "BUY")
        entry_price_raw = StrategyRunner._get_value(configuration, "entry_price", "entryPrice")
        exit_price_raw = StrategyRunner._get_value(configuration, "exit_price", "exitPrice")
        lots_raw = StrategyRunner._get_value(configuration, "lots", "total_lots")
        lot_size_raw = StrategyRunner._get_value(configuration, "lot_size", "lotSize")

        if entry_price_raw is None or exit_price_raw is None:
            raise ValueError("Backtest configuration requires entry_price and exit_price")
        if lots_raw is None:
            raise ValueError("Backtest configuration requires lots")

        try:
            side = OrderSideEnum(str(side_raw).upper())
        except ValueError as exc:
            raise ValueError(f"Unsupported order side for backtest: {side_raw}") from exc

        try:
            entry_price = float(entry_price_raw)
            exit_price = float(exit_price_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("entry_price and exit_price must be numeric") from exc

        try:
            lots = int(lots_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("lots must be an integer") from exc

        lot_size = 1
        if lot_size_raw is not None:
            try:
                lot_size = int(lot_size_raw)
            except (TypeError, ValueError) as exc:
                raise ValueError("lot_size must be an integer") from exc

        quantity = lots * lot_size
        pnl_per_unit = exit_price - entry_price if side == OrderSideEnum.BUY else entry_price - exit_price
        pnl = round(pnl_per_unit * quantity, 4)

        return {
            "order_count": 1,
            "symbol": symbol,
            "side": side.value,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "quantity": quantity,
            "pnl": pnl,
        }

    @staticmethod
    def _get_value(mapping: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in mapping:
                return mapping[key]
        return None


__all__ = ["StrategyRunner", "StrategyRunResult"]
