from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.account import Account
from app.models.broker import Broker
from app.models.log import LogEntry, LogType
from app.models.order import Order
from app.models.position import Position
from app.models.rms import RmsRule
from app.models.trade import Trade
from app.utils.dt import utcnow
from app.schemas.order import OrderCreate
from app.schemas.rms import (
    PositionSnapshot,
    RmsConfigRead,
    RmsConfigUpdate,
    RmsSquareOffResponse,
    RmsStatusRead,
)


@dataclass(slots=True)
class _DailySnapshot:
    total_lots: int
    day_pnl: float
    notional_exposure: float
    available_margin: float


@dataclass(slots=True)
class _AutomationCue:
    code: str
    message: str


class RmsViolationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class RmsService:
    """Risk management helper handling configuration and runtime checks."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_config(self, user_id: uuid.UUID) -> RmsConfigRead:
        rule = self._get_or_create_rule(user_id)
        return self._to_config(rule)

    def update_config(self, user_id: uuid.UUID, payload: RmsConfigUpdate) -> RmsConfigRead:
        rule = self._get_or_create_rule(user_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(rule, field, value)
        rule.updated_at = utcnow()
        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)
        return self._to_config(rule)

    def get_status(self, user_id: uuid.UUID) -> RmsStatusRead:
        rule = self._get_or_create_rule(user_id)
        snapshot = self._daily_snapshot(user_id)
        automation_cues = self._automation_recommendations(rule, snapshot)
        automations = [cue.message for cue in automation_cues]
        alerts: list[str] = []
        lots_remaining = None
        if rule.max_daily_lots:
            lots_remaining = max(rule.max_daily_lots - snapshot.total_lots, 0)
            if lots_remaining <= max(int(rule.max_daily_lots * 0.1), 1):
                alerts.append("Daily lot limit is nearly exhausted")
        loss_remaining = None
        if rule.max_daily_loss is not None:
            max_loss_value = float(rule.max_daily_loss)
            loss_remaining = max(max_loss_value + snapshot.day_pnl, 0.0)
            if snapshot.day_pnl <= -0.8 * max_loss_value:
                alerts.append("Daily loss approaching limit")
        if rule.exposure_limit is not None and snapshot.notional_exposure >= float(rule.exposure_limit) * 0.9:
            alerts.append("Exposure near configured limit")
        return RmsStatusRead(
            day_pnl=snapshot.day_pnl,
            total_lots_today=snapshot.total_lots,
            max_daily_lots=rule.max_daily_lots,
            lots_remaining=lots_remaining,
            max_daily_loss=float(rule.max_daily_loss) if rule.max_daily_loss is not None else None,
            loss_remaining=loss_remaining,
            notional_exposure=snapshot.notional_exposure,
            exposure_limit=float(rule.exposure_limit) if rule.exposure_limit is not None else None,
            available_margin=snapshot.available_margin,
            margin_buffer_pct=float(rule.margin_buffer_pct) if rule.margin_buffer_pct is not None else None,
            alerts=alerts,
            automations=automations,
        )

    def evaluate_pre_trade(self, user_id: uuid.UUID, payload: OrderCreate) -> None:
        rule = self._get_or_create_rule(user_id)
        status = self.get_status(user_id)

        if rule.max_lots is not None and payload.qty > rule.max_lots:
            raise RmsViolationError(
                "RMS_MAX_ORDER_SIZE",
                f"Order quantity {payload.qty} exceeds max lots per order {rule.max_lots}",
            )

        if rule.max_daily_lots is not None:
            if status.total_lots_today + payload.qty > rule.max_daily_lots:
                raise RmsViolationError(
                    "RMS_MAX_DAILY_LOTS",
                    "Daily lot limit would be exceeded by this order",
                )

        if rule.max_daily_loss is not None and status.day_pnl <= -float(rule.max_daily_loss):
            raise RmsViolationError(
                "RMS_MAX_DAILY_LOSS",
                "Daily loss threshold breached; new orders are blocked",
            )

        if rule.exposure_limit is not None:
            projected_exposure = status.notional_exposure + self._estimate_notional(payload)
            if projected_exposure > float(rule.exposure_limit):
                raise RmsViolationError(
                    "RMS_EXPOSURE_LIMIT",
                    "Notional exposure limit reached",
                )

        if rule.margin_buffer_pct is not None:
            required_margin = self._estimate_notional(payload)
            allowed_utilisation = status.available_margin * (float(rule.margin_buffer_pct) / 100)
            if allowed_utilisation and required_margin > allowed_utilisation:
                raise RmsViolationError(
                    "RMS_MARGIN_BUFFER",
                    "Order violates configured margin buffer",
                )

    def auto_enforce(self, user_id: uuid.UUID) -> list[str]:
        rule = self._get_or_create_rule(user_id)
        snapshot = self._daily_snapshot(user_id)
        cues = self._automation_recommendations(rule, snapshot)
        executed: list[str] = []
        square_off_executed = False
        hedge_executed = False
        for cue in cues:
            if cue.code == "auto_square_off":
                if square_off_executed:
                    continue
                response = self.trigger_square_off(user_id, reason=cue.message, automated=True)
                executed.append(f"{cue.message} ({len(response.positions)} positions queued)")
                self._record_notifications(rule, user_id, cue.message)
                square_off_executed = True
            elif cue.code == "auto_hedge":
                if hedge_executed:
                    continue
                ratio = self._decimal_to_float(rule.auto_hedge_ratio) or 1.0
                self._log_rms_event(
                    user_id,
                    f"Auto hedge queued (ratio {ratio:.2f}): {cue.message}",
                )
                executed.append(cue.message)
                self._record_notifications(rule, user_id, cue.message)
                hedge_executed = True
        return executed

    def trigger_square_off(self, user_id: uuid.UUID, *, reason: str | None = None, automated: bool = False) -> RmsSquareOffResponse:
        positions = self._user_positions(user_id)
        position_snapshots = [
            PositionSnapshot(
                account_id=pos.account_id,
                symbol=pos.symbol,
                qty=pos.qty,
                updated_at=pos.updated_at,
            )
            for pos in positions
            if pos.qty != 0
        ]
        default_message = "Square-off request recorded; execution to be handled by downstream worker"
        if reason:
            response_message = reason
            log_message = "{} RMS square-off initiated: {}".format(
                "Automated" if automated else "Manual",
                reason,
            )
        elif automated:
            response_message = "Automated RMS square-off triggered"
            log_message = "Automated RMS square-off triggered"
        else:
            response_message = default_message
            log_message = "Manual RMS square-off requested"
        log_entry = LogEntry(
            user_id=user_id,
            type=LogType.rms,
            message=log_message,
            created_at=utcnow(),
        )
        self.session.add(log_entry)
        self.session.commit()
        return RmsSquareOffResponse(triggered=bool(position_snapshots), message=response_message, positions=position_snapshots)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _automation_recommendations(self, rule: RmsRule, snapshot: _DailySnapshot) -> list[_AutomationCue]:
        cues: list[_AutomationCue] = []
        if rule.auto_square_off_enabled:
            trigger_loss: float | None = None
            daily_loss_limit = self._decimal_to_float(rule.max_daily_loss)
            if daily_loss_limit is not None:
                buffer_pct = self._decimal_to_float(rule.auto_square_off_buffer_pct) or 0.0
                buffer_pct = max(buffer_pct, 0.0)
                buffer_multiplier = 1.0 - min(buffer_pct, 100.0) / 100.0
                trigger_loss = -daily_loss_limit * buffer_multiplier
            else:
                drawdown_limit = self._decimal_to_float(rule.drawdown_limit)
                if drawdown_limit is not None:
                    trigger_loss = -drawdown_limit
            if trigger_loss is not None and snapshot.day_pnl <= trigger_loss:
                limit_value = abs(trigger_loss)
                cues.append(
                    _AutomationCue(
                        code="auto_square_off",
                        message=(
                            f"Auto square-off triggered: day PnL {snapshot.day_pnl:.2f} "
                            f"breached loss limit {limit_value:.2f}"
                        ),
                    )
                )
            profit_lock = self._decimal_to_float(rule.profit_lock)
            if profit_lock is not None and snapshot.day_pnl >= profit_lock:
                cues.append(
                    _AutomationCue(
                        code="auto_square_off",
                        message=(
                            f"Auto square-off triggered: profit lock target {profit_lock:.2f} reached "
                            f"(PnL {snapshot.day_pnl:.2f})"
                        ),
                    )
                )
        if rule.auto_hedge_enabled:
            ratio = self._decimal_to_float(rule.auto_hedge_ratio) or 1.0
            exposure_limit = self._decimal_to_float(rule.exposure_limit)
            if exposure_limit is not None:
                hedge_trigger = exposure_limit * 0.9
                if snapshot.notional_exposure >= hedge_trigger:
                    cues.append(
                        _AutomationCue(
                            code="auto_hedge",
                            message=(
                                f"Auto hedge triggered: exposure {snapshot.notional_exposure:.2f} "
                                f"within 10% of limit {exposure_limit:.2f} (ratio {ratio:.2f})"
                            ),
                        )
                    )
            elif snapshot.notional_exposure > 0:
                cues.append(
                    _AutomationCue(
                        code="auto_hedge",
                        message=(
                            f"Auto hedge triggered: exposure {snapshot.notional_exposure:.2f} "
                            f"requires coverage (ratio {ratio:.2f})"
                        ),
                    )
                )
        return cues

    def _record_notifications(self, rule: RmsRule, user_id: uuid.UUID, detail: str) -> None:
        channels: list[str] = []
        if rule.notify_email:
            channels.append("email")
        if rule.notify_telegram:
            channels.append("telegram")
        for channel in channels:
            self._log_rms_event(user_id, f"Notification queued via {channel}: {detail}")

    def _log_rms_event(self, user_id: uuid.UUID, message: str) -> None:
        entry = LogEntry(
            user_id=user_id,
            type=LogType.rms,
            message=message,
            created_at=utcnow(),
        )
        self.session.add(entry)
        self.session.commit()

    def _get_or_create_rule(self, user_id: uuid.UUID) -> RmsRule:
        stmt: Select[RmsRule] = select(RmsRule).where(RmsRule.user_id == user_id).limit(1)
        rule = self.session.execute(stmt).scalar_one_or_none()
        if rule is None:
            rule = RmsRule(user_id=user_id)
            self.session.add(rule)
            self.session.commit()
            self.session.refresh(rule)
        return rule

    def _daily_snapshot(self, user_id: uuid.UUID) -> _DailySnapshot:
        start = self._day_start()
        lots_stmt = (
            select(func.coalesce(func.sum(Order.qty), 0))
            .select_from(Order)
            .join(Order.account)
            .join(Account.broker)
            .where(Broker.user_id == user_id, Order.created_at >= start)
        )
        total_lots = int(self.session.execute(lots_stmt).scalar_one() or 0)

        trades_stmt = (
            select(func.coalesce(func.sum(Trade.pnl), 0))
            .select_from(Trade)
            .join(Trade.order)
            .join(Order.account)
            .join(Account.broker)
            .where(Broker.user_id == user_id, Trade.timestamp >= start)
        )
        trade_pnl = self._decimal_to_float(self.session.execute(trades_stmt).scalar_one() or 0)

        positions_stmt = (
            select(Position)
            .join(Position.account)
            .join(Account.broker)
            .options(joinedload(Position.account))
            .where(Broker.user_id == user_id)
        )
        positions: list[Position] = list(self.session.execute(positions_stmt).scalars())

        unrealised_pnl = sum(self._decimal_to_float(pos.pnl or 0) for pos in positions)
        notional_exposure = sum(abs(pos.qty) * self._decimal_to_float(pos.avg_price) for pos in positions)

        margin_stmt = (
            select(func.coalesce(func.sum(Account.margin), 0))
            .select_from(Account)
            .join(Account.broker)
            .where(Broker.user_id == user_id)
        )
        available_margin = self._decimal_to_float(self.session.execute(margin_stmt).scalar_one() or 0)

        return _DailySnapshot(
            total_lots=total_lots,
            day_pnl=trade_pnl + unrealised_pnl,
            notional_exposure=notional_exposure,
            available_margin=available_margin,
        )

    def _user_positions(self, user_id: uuid.UUID) -> list[Position]:
        stmt = (
            select(Position)
            .join(Position.account)
            .join(Account.broker)
            .where(Broker.user_id == user_id)
        )
        return list(self.session.execute(stmt).scalars())

    def _estimate_notional(self, payload: OrderCreate) -> float:
        if payload.price is None:
            return 0.0
        return abs(payload.qty) * float(payload.price)

    def _to_config(self, rule: RmsRule) -> RmsConfigRead:
        return RmsConfigRead(
            max_loss=self._decimal_to_float(rule.max_loss),
            max_lots=rule.max_lots,
            profit_lock=self._decimal_to_float(rule.profit_lock),
            trailing_sl=self._decimal_to_float(rule.trailing_sl),
            max_daily_loss=self._decimal_to_float(rule.max_daily_loss),
            max_daily_lots=rule.max_daily_lots,
            exposure_limit=self._decimal_to_float(rule.exposure_limit),
            margin_buffer_pct=self._decimal_to_float(rule.margin_buffer_pct),
            drawdown_limit=self._decimal_to_float(rule.drawdown_limit),
            auto_square_off_enabled=rule.auto_square_off_enabled,
            auto_square_off_buffer_pct=self._decimal_to_float(rule.auto_square_off_buffer_pct),
            auto_hedge_enabled=rule.auto_hedge_enabled,
            auto_hedge_ratio=self._decimal_to_float(rule.auto_hedge_ratio),
            notify_email=rule.notify_email,
            notify_telegram=rule.notify_telegram,
            updated_at=rule.updated_at,
        )

    @staticmethod
    def _decimal_to_float(value: Decimal | float | None) -> float | None:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        return value

    @staticmethod
    def _day_start() -> datetime:
        now = utcnow()
        return now.replace(hour=0, minute=0, second=0, microsecond=0)


__all__ = ["RmsService", "RmsViolationError"]
