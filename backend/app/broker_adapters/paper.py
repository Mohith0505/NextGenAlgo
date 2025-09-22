from __future__ import annotations

import threading
import uuid
from datetime import datetime
from typing import Mapping

from .base import BaseBrokerAdapter, BrokerSession, OrderPayload, OrderResult


class _PaperTradingEngine:
    """Simple in-memory simulator used by the paper trading adapter."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, dict[str, str]] = {}
        self._orders: dict[str, dict[str, str]] = {}
        self._order_counter = 0

    def create_session(self, client_code: str | None) -> BrokerSession:
        token = f"PAPER-{uuid.uuid4().hex}"
        with self._lock:
            self._sessions[token] = {
                "client_code": client_code or "paper",
                "created_at": datetime.utcnow().isoformat(),
            }
        metadata = {"client_code": client_code or "paper"}
        return BrokerSession(token=token, metadata=metadata)

    def validate_session(self, token: str) -> bool:
        with self._lock:
            return token in self._sessions

    def _next_order_id(self) -> str:
        with self._lock:
            self._order_counter += 1
            return f"PAPER-ORD-{self._order_counter:06d}"

    def record_order(self, token: str, payload: OrderPayload) -> OrderResult:
        if not self.validate_session(token):
            raise ValueError("Invalid paper trading session token")
        order_id = self._next_order_id()
        status = "FILLED" if payload.order_type == "MARKET" else "PENDING"
        record = {
            "order_id": order_id,
            "symbol": payload.symbol,
            "side": payload.side,
            "qty": payload.quantity,
            "order_type": payload.order_type,
            "price": payload.price,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        with self._lock:
            self._orders[order_id] = record
        metadata = {
            "symbol": payload.symbol,
            "side": payload.side,
            "qty": payload.quantity,
            "order_type": payload.order_type,
            "timestamp": record["timestamp"],
        }
        return OrderResult(order_id=order_id, status=status, metadata=metadata)

    def cancel_order(self, token: str, order_id: str) -> bool:
        if not self.validate_session(token):
            return False
        with self._lock:
            order = self._orders.get(order_id)
            if order is None:
                return False
            order["status"] = "CANCELLED"
            return True

    def margin_snapshot(self) -> dict[str, float]:
        # Static snapshot suitable for paper trading demos
        return {"available": 1_000_000.0, "utilized": 0.0, "currency": "INR"}


_ENGINE = _PaperTradingEngine()


class PaperTradingAdapter(BaseBrokerAdapter):
    """Adapter that simulates broker behaviour for paper trading environments."""

    broker_name = "paper_trading"
    aliases = {"paper", "paper-trading", "simulator"}

    def connect(self, credentials: Mapping[str, str]) -> BrokerSession:
        client_code = credentials.get("client_code") if credentials else None
        return _ENGINE.create_session(client_code)

    def validate_session(self, session_token: str) -> bool:
        return _ENGINE.validate_session(session_token)

    def place_order(self, session_token: str, payload: OrderPayload) -> OrderResult:
        return _ENGINE.record_order(session_token, payload)

    def cancel_order(self, session_token: str, order_id: str) -> bool:
        return _ENGINE.cancel_order(session_token, order_id)

    def get_margin(self, session_token: str) -> Mapping[str, float]:
        return _ENGINE.margin_snapshot()

    def get_ltp(self, session_token: str, symbol: str) -> float:
        # Deterministic pseudo price for predictable paper trading demos
        base = abs(hash(symbol)) % 10_000
        return round(100 + base / 250, 2)
