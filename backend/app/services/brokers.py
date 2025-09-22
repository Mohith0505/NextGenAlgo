from __future__ import annotations

import math
import uuid
from time import perf_counter
from typing import Iterable

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.broker_adapters import (
    BrokerAuthenticationError,
    BrokerError,
    OrderPayload,
    get_adapter,
)
from app.models.account import Account
from app.models.broker import Broker, BrokerStatus
from app.models.execution_run import ExecutionRun
from app.models.execution_run_event import ExecutionRunEvent
from app.models.order import Order, OrderSide, OrderStatus, OrderType
from app.schemas.broker import BrokerConnectRequest, BrokerRead, BrokerRefreshRequest
from app.schemas.order import (
    ExecutionAllocationResult,
    ExecutionGroupOrderCreate,
    ExecutionGroupOrderResponse,
    ExecutionLatencySummary,
    ExecutionLegOutcome,
    OrderCreate,
    OrderRead,
)
from app.services.account_registry import AccountRegistryService
from app.services.rms import RmsService, RmsViolationError
from app.utils.dt import utcnow


class BrokerService:
    """Coordinates broker adapters with the database-backed domain models."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.rms_service = RmsService(session)
        self.account_registry = AccountRegistryService(session)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _select_brokers(self, user_id: uuid.UUID) -> Select[tuple[Broker]]:
        return (
            select(Broker)
            .options(joinedload(Broker.accounts))
            .where(Broker.user_id == user_id)
            .order_by(Broker.created_at.asc())
        )

    def _get_broker(self, broker_id: uuid.UUID, user_id: uuid.UUID) -> Broker | None:
        stmt = (
            select(Broker)
            .options(joinedload(Broker.accounts))
            .where(Broker.id == broker_id, Broker.user_id == user_id)
            .limit(1)
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def _find_existing(self, user_id: uuid.UUID, broker_name: str, client_code: str) -> Broker | None:
        stmt = (
            select(Broker)
            .options(joinedload(Broker.accounts))
            .where(
                Broker.user_id == user_id,
                Broker.broker_name == broker_name,
                Broker.client_code == client_code,
            )
            .limit(1)
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()

    def _ensure_account(self, broker: Broker) -> Account:
        if broker.accounts:
            return broker.accounts[0]

        account = Account(broker_id=broker.id, margin=0, currency="INR")
        self.session.add(account)
        self.session.flush()
        broker.accounts.append(account)
        return account

    def _to_broker_schema(self, broker: Broker) -> BrokerRead:
        return BrokerRead.model_validate(broker)

    def _order_query(self, user_id: uuid.UUID) -> Select[tuple[Order]]:
        return (
            select(Order)
            .join(Order.account)
            .join(Account.broker)
            .options(joinedload(Order.account).joinedload(Account.broker))
            .where(Broker.user_id == user_id)
            .order_by(Order.created_at.desc())
        )

    def _order_to_schema(self, order: Order) -> OrderRead:
        return OrderRead.model_validate(order)

    def _status_from_adapter(self, status: str | None) -> OrderStatus:
        if not status:
            return OrderStatus.pending

        try:
            return OrderStatus(status.upper())
        except ValueError:
            return OrderStatus.pending

    # ------------------------------------------------------------------
    # Broker lifecycle
    # ------------------------------------------------------------------
    def connect(self, user_id: uuid.UUID, payload: BrokerConnectRequest) -> BrokerRead:
        adapter = get_adapter(payload.broker_name)
        session = adapter.connect(payload.credentials)

        broker = self._find_existing(user_id, adapter.broker_name, payload.client_code)
        if broker is None:
            broker = Broker(
                user_id=user_id,
                broker_name=adapter.broker_name,
                client_code=payload.client_code,
            )

        broker.session_token = session.token
        broker.status = BrokerStatus.connected
        self.session.add(broker)
        self.session.flush()
        self._ensure_account(broker)
        self.session.commit()
        self.session.refresh(broker)
        return self._to_broker_schema(broker)

    def list_brokers(self, user_id: uuid.UUID) -> list[BrokerRead]:
        stmt = self._select_brokers(user_id)
        brokers: Iterable[Broker] = self.session.execute(stmt).unique().scalars()
        return [self._to_broker_schema(broker) for broker in brokers]

    def refresh(self, user_id: uuid.UUID, broker_id: uuid.UUID, payload: BrokerRefreshRequest) -> BrokerRead:
        broker = self._get_broker(broker_id, user_id)
        if broker is None:
            raise ValueError("Broker not found")

        adapter = get_adapter(broker.broker_name)
        session = adapter.connect(payload.credentials)
        broker.session_token = session.token
        broker.status = BrokerStatus.connected
        self.session.add(broker)
        self.session.commit()
        self.session.refresh(broker)
        return self._to_broker_schema(broker)

    def delete_broker(self, user_id: uuid.UUID, broker_id: uuid.UUID) -> bool:
        broker = self._get_broker(broker_id, user_id)
        if broker is None:
            return False

        self.session.delete(broker)
        self.session.commit()
        return True

    # ------------------------------------------------------------------
    # Order flow
    # ------------------------------------------------------------------
    def place_order(self, user_id: uuid.UUID, payload: OrderCreate) -> OrderRead:
        return self._place_single_order(user_id, payload)

    def _place_single_order(self, user_id: uuid.UUID, payload: OrderCreate) -> OrderRead:
        broker = self._get_broker(payload.broker_id, user_id)
        if broker is None:
            raise ValueError("Broker not found for user")

        self.rms_service.evaluate_pre_trade(user_id, payload)

        if not broker.session_token:
            raise BrokerAuthenticationError("Broker session expired; please refresh the connection")

        adapter = get_adapter(broker.broker_name)
        order_payload = OrderPayload(
            symbol=payload.symbol,
            side=payload.side.value,
            quantity=payload.qty,
            order_type=payload.order_type.value,
            price=payload.price,
            take_profit=payload.take_profit,
            stop_loss=payload.stop_loss,
            strategy_id=str(payload.strategy_id) if payload.strategy_id else None,
        )
        adapter_result = adapter.place_order(broker.session_token, order_payload)

        account = self._ensure_account(broker)
        order = Order(
            account_id=account.id,
            strategy_id=payload.strategy_id,
            symbol=payload.symbol,
            side=OrderSide(payload.side.value),
            qty=payload.qty,
            order_type=OrderType(payload.order_type.value),
            price=payload.price,
            tp_price=payload.take_profit,
            sl_price=payload.stop_loss,
            broker_order_id=adapter_result.order_id,
            status=self._status_from_adapter(adapter_result.status),
        )
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return self._order_to_schema(order)

    def place_execution_group_order(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID | str,
        payload: ExecutionGroupOrderCreate,
        *,
        strategy_run_id: uuid.UUID | None = None,
    ) -> ExecutionGroupOrderResponse:
        group_uuid = uuid.UUID(str(group_id))
        metadata = {
            "symbol": payload.symbol,
            "side": payload.side.value,
            "order_type": payload.order_type.value,
            "lots": payload.lots,
            "lot_size": payload.lot_size,
        }

        execution_run = ExecutionRun(
            group_id=group_uuid,
            strategy_run_id=strategy_run_id,
            status="pending",
            requested_at=utcnow(),
            payload=dict(metadata),
        )

        orders: list[Order] = []
        allocation_results: list[ExecutionAllocationResult] = []
        adapter_cache: dict[str, object] = {}
        event_records: list[dict[str, object | None]] = []

        use_transaction = not self.session.in_transaction()

        try:
            allocations = self.account_registry.preview_allocation(user_id, group_uuid, payload.lots)
            if not allocations:
                raise ValueError("Execution group has no accounts to allocate orders")

            self.session.add(execution_run)
            self.session.flush()

            for allocation in allocations:
                quantity = int(allocation.lots * payload.lot_size)
                if quantity <= 0:
                    continue

                account_stmt = (
                    select(Account)
                    .options(joinedload(Account.broker))
                    .where(Account.id == allocation.account_id)
                    .limit(1)
                )
                account = (
                    self.session.execute(account_stmt)
                    .unique()
                    .scalar_one_or_none()
                )
                if account is None or account.broker.user_id != user_id:
                    raise ValueError("Account not found for execution group")

                broker = account.broker
                if not broker.session_token:
                    raise BrokerAuthenticationError(
                        f"Broker session expired for {broker.broker_name}; please refresh the connection"
                    )

                per_order_payload = OrderCreate(
                    broker_id=broker.id,
                    symbol=payload.symbol,
                    side=payload.side,
                    qty=quantity,
                    order_type=payload.order_type,
                    price=payload.price,
                    take_profit=payload.take_profit,
                    stop_loss=payload.stop_loss,
                    strategy_id=payload.strategy_id,
                )
                self.rms_service.evaluate_pre_trade(user_id, per_order_payload)

                adapter = adapter_cache.get(broker.broker_name)
                if adapter is None:
                    adapter = get_adapter(broker.broker_name)
                    adapter_cache[broker.broker_name] = adapter

                order_payload = OrderPayload(
                    symbol=payload.symbol,
                    side=payload.side.value,
                    quantity=quantity,
                    order_type=payload.order_type.value,
                    price=payload.price,
                    take_profit=payload.take_profit,
                    stop_loss=payload.stop_loss,
                    strategy_id=str(payload.strategy_id) if payload.strategy_id else None,
                )

                started_at = utcnow()
                perf_start = perf_counter()
                adapter_result = adapter.place_order(broker.session_token, order_payload)
                completed_at = utcnow()
                latency_ms = (perf_counter() - perf_start) * 1000

                order = Order(
                    account_id=account.id,
                    strategy_id=payload.strategy_id,
                    symbol=payload.symbol,
                    side=OrderSide(payload.side.value),
                    qty=quantity,
                    order_type=OrderType(payload.order_type.value),
                    price=payload.price,
                    tp_price=payload.take_profit,
                    sl_price=payload.stop_loss,
                    broker_order_id=adapter_result.order_id,
                    status=self._status_from_adapter(adapter_result.status),
                )
                self.session.add(order)
                self.session.flush()
                orders.append(order)

                event_records.append(
                    {
                        "account_id": account.id,
                        "broker_id": broker.id,
                        "order_id": order.id,
                        "status": adapter_result.status,
                        "latency_ms": latency_ms,
                        "requested_at": started_at,
                        "completed_at": completed_at,
                        "message": adapter_result.metadata.get("message") if adapter_result.metadata else None,
                        "metadata": dict(adapter_result.metadata) if adapter_result.metadata else {},
                    }
                )

                allocation_results.append(
                    ExecutionAllocationResult(
                        account_id=account.id,
                        broker_id=broker.id,
                        lots=allocation.lots,
                        quantity=quantity,
                        allocation_policy=allocation.allocation_policy,
                        weight=allocation.weight,
                        fixed_lots=allocation.fixed_lots,
                    )
                )

            if not orders:
                raise ValueError("No valid orders were generated for the execution group")

            latencies = [record["latency_ms"] for record in event_records if record["latency_ms"] is not None]
            latency_summary: dict[str, float] | None = None
            latency_percentiles: dict[str, float] | None = None
            if latencies:
                latencies.sort()
                count = len(latencies)
                avg_latency = sum(latencies) / count
                max_latency = latencies[-1]

                def _percentile(data: list[float], pct: float) -> float:
                    if len(data) == 1:
                        return data[0]
                    rank = (pct / 100) * (len(data) - 1)
                    lower = math.floor(rank)
                    upper = math.ceil(rank)
                    if lower == upper:
                        return data[int(rank)]
                    lower_value = data[lower]
                    upper_value = data[upper]
                    fraction = rank - lower
                    return lower_value + (upper_value - lower_value) * fraction

                latency_percentiles = {
                    "p50_ms": _percentile(latencies, 50.0),
                    "p95_ms": _percentile(latencies, 95.0),
                }
                latency_summary = {
                    "average_ms": avg_latency,
                    "max_ms": max_latency,
                    "count": count,
                }

            execution_run.status = "completed"
            execution_run.completed_at = utcnow()

            leg_outcomes: list[ExecutionLegOutcome] = []
            for record in event_records:
                event = ExecutionRunEvent(
                    run=execution_run,
                    account_id=record["account_id"],
                    broker_id=record["broker_id"],
                    order_id=record["order_id"],
                    status=(record["status"] or "pending"),
                    latency_ms=record["latency_ms"],
                    requested_at=record["requested_at"],
                    completed_at=record["completed_at"],
                    message=record["message"],
                    event_metadata=record["metadata"],
                )
                self.session.add(event)
                leg_outcomes.append(
                    ExecutionLegOutcome(
                        account_id=record["account_id"],
                        broker_id=record["broker_id"],
                        order_id=record["order_id"],
                        status=(record["status"] or "unknown"),
                        latency_ms=record["latency_ms"],
                        message=record["message"],
                        metadata=record["metadata"],
                    )
                )

            execution_run.payload = {
                **metadata,
                "order_ids": [str(order.id) for order in orders],
                "distribution": [
                    {
                        "account_id": str(result.account_id),
                        "broker_id": str(result.broker_id),
                        "lots": result.lots,
                        "quantity": result.quantity,
                    }
                    for result in allocation_results
                ],
            }
            if latency_summary is not None:
                rounded_summary = {
                    "average_ms": round(latency_summary["average_ms"], 4),
                    "max_ms": round(latency_summary["max_ms"], 4),
                    "count": latency_summary["count"],
                }
                if latency_percentiles is not None:
                    rounded_summary["p50_ms"] = round(latency_percentiles["p50_ms"], 4)
                    rounded_summary["p95_ms"] = round(latency_percentiles["p95_ms"], 4)
                execution_run.payload["latency"] = rounded_summary
                latency_model = ExecutionLatencySummary(**rounded_summary)
            else:
                latency_model = None

            self.session.flush()
            if use_transaction:
                self.session.commit()
        except Exception as exc:  # noqa: BLE001
            self.session.rollback()
            failure_payload = {
                **metadata,
                "distribution": [
                    {
                        "account_id": str(result.account_id),
                        "broker_id": str(result.broker_id),
                        "lots": result.lots,
                        "quantity": result.quantity,
                    }
                    for result in allocation_results
                ],
                "error": str(exc),
                "events_recorded": len(event_records),
            }
            failure_run = ExecutionRun(
                group_id=group_uuid,
                strategy_run_id=strategy_run_id,
                status="failed",
                requested_at=utcnow(),
                completed_at=utcnow(),
                payload=failure_payload,
            )
            self.session.add(failure_run)
            failure_event = ExecutionRunEvent(
                run=failure_run,
                status="failed",
                latency_ms=None,
                requested_at=utcnow(),
                completed_at=utcnow(),
                message=str(exc),
                event_metadata=failure_payload,
            )
            self.session.add(failure_event)
            self.session.commit()
            raise

        self.session.refresh(execution_run)
        return ExecutionGroupOrderResponse(
            execution_run_id=execution_run.id,
            orders=[self._order_to_schema(order) for order in orders],
            allocation=allocation_results,
            total_lots=payload.lots,
            lot_size=payload.lot_size,
            latency=latency_model,
            leg_outcomes=leg_outcomes,
        )

    def list_orders(self, user_id: uuid.UUID) -> list[OrderRead]:
        stmt = self._order_query(user_id)
        orders: Iterable[Order] = self.session.execute(stmt).unique().scalars()
        return [self._order_to_schema(order) for order in orders]

    def get_order(self, user_id: uuid.UUID, order_id: uuid.UUID) -> OrderRead | None:
        stmt = self._order_query(user_id).where(Order.id == order_id).limit(1)
        order = self.session.execute(stmt).unique().scalar_one_or_none()
        if order is None:
            return None
        return self._order_to_schema(order)

    def cancel_order(self, user_id: uuid.UUID, order_id: uuid.UUID) -> OrderRead | None:
        stmt = (
            select(Order)
            .join(Order.account)
            .join(Account.broker)
            .options(joinedload(Order.account).joinedload(Account.broker))
            .where(Order.id == order_id, Broker.user_id == user_id)
            .limit(1)
        )
        order = self.session.execute(stmt).unique().scalar_one_or_none()
        if order is None:
            return None

        broker = order.account.broker
        adapter = get_adapter(broker.broker_name)
        broker_order_id = order.broker_order_id or str(order.id)
        try:
            adapter.cancel_order(broker.session_token or "", broker_order_id)
        except BrokerError:
            # The stub adapters are tolerant of cancellation failures; we still mark it cancelled locally.
            pass

        order.status = OrderStatus.cancelled
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return self._order_to_schema(order)


__all__ = ["BrokerService", "RmsViolationError"]
