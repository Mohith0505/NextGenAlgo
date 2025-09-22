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


class FyersAdapter(BaseBrokerAdapter):
    """Mock Fyers adapter covering the unified adapter contract."""

    broker_name = "fyers"
    aliases = {"fyers_one", "fyers-api"}
    required_keys = {"client_id", "secret_key", "pin"}

    def connect(self, credentials: Mapping[str, str]) -> BrokerSession:
        missing = self.required_keys - credentials.keys()
        if missing:
            raise BrokerAuthenticationError(f"Missing Fyers credentials: {', '.join(sorted(missing))}")
        token = f"FYERS-{uuid.uuid4().hex}"
        metadata = {"auth_token": token, "access_type": "read_write"}
        return BrokerSession(token=token, metadata=metadata)

    def place_order(self, session_token: str, payload: OrderPayload) -> OrderResult:
        if not session_token:
            raise BrokerAuthenticationError("Fyers session invalid; connect again.")
        order_id = f"FYERS-ORD-{uuid.uuid4().hex[:12]}"
        metadata = {
            "productType": "INTRADAY",
            "orderValidity": "DAY",
        }
        status = "PENDING"
        if payload.order_type == "MARKET":
            status = "FILLED"
        return OrderResult(order_id=order_id, status=status, metadata=metadata)

    def cancel_order(self, session_token: str, order_id: str) -> bool:
        return True

    def get_margin(self, session_token: str):
        return {"available": 150000.0, "utilized": 25000.0}
