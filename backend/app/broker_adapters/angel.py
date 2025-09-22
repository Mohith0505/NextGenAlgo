from __future__ import annotations

import uuid
from typing import Mapping

from .base import (
    BaseBrokerAdapter,
    BrokerAuthenticationError,
    BrokerSession,
    OrderPayload,
    OrderResult,
)


class AngelAdapter(BaseBrokerAdapter):
    """Lightweight mock for the Angel One SmartAPI adapter."""

    broker_name = "angel_one"
    aliases = {"angel", "angel-one", "angelone", "smartapi"}
    required_keys = {"client_code", "api_key", "api_secret", "totp"}

    def connect(self, credentials: Mapping[str, str]) -> BrokerSession:
        missing = self.required_keys - credentials.keys()
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise BrokerAuthenticationError(f"Missing credentials for Angel One: {missing_list}")
        token = f"ANG-{credentials['client_code']}-{uuid.uuid4().hex}"
        metadata = {
            "client_code": credentials["client_code"],
            "refresh_token": uuid.uuid4().hex,
        }
        return BrokerSession(token=token, metadata=metadata)

    def get_ltp(self, session_token: str, symbol: str) -> float:
        base = abs(hash((session_token, symbol))) % 5000
        return round(50 + base / 100, 2)

    def place_order(self, session_token: str, payload: OrderPayload) -> OrderResult:
        if not session_token:
            raise BrokerAuthenticationError("Broker session missing; please connect first.")
        order_id = f"ANG-ORD-{uuid.uuid4().hex[:10]}"
        status = "PENDING" if payload.order_type == "LIMIT" else "FILLED"
        metadata = {
            "symbol": payload.symbol,
            "side": payload.side,
            "qty": payload.quantity,
            "order_type": payload.order_type,
        }
        return OrderResult(order_id=order_id, status=status, metadata=metadata)

    def cancel_order(self, session_token: str, order_id: str) -> bool:
        return True

    def get_margin(self, session_token: str):
        return {"available": 250000.0, "utilized": 0.0, "collateral": 50000.0}
