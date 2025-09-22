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


class DhanAdapter(BaseBrokerAdapter):
    """Mock Dhan adapter with simplified contract implementations."""

    broker_name = "dhan"
    aliases = {"dhanhq", "dhan-hq"}
    required_keys = {"client_id", "access_token"}

    def connect(self, credentials: Mapping[str, str]) -> BrokerSession:
        missing = self.required_keys - credentials.keys()
        if missing:
            raise BrokerAuthenticationError(f"Missing Dhan credentials: {', '.join(sorted(missing))}")
        token = f"DHAN-{uuid.uuid4().hex}"
        metadata = {"client_id": credentials["client_id"]}
        return BrokerSession(token=token, metadata=metadata)

    def place_order(self, session_token: str, payload: OrderPayload) -> OrderResult:
        if not session_token:
            raise BrokerAuthenticationError("Dhan session invalid; please connect.")
        order_id = f"DHAN-ORD-{uuid.uuid4().hex[:10]}"
        metadata = {"exchange": "NSE", "tradeType": payload.side}
        return OrderResult(order_id=order_id, status="PENDING", metadata=metadata)

    def cancel_order(self, session_token: str, order_id: str) -> bool:
        return True

    def get_margin(self, session_token: str):
        return {"available": 100000.0, "utilized": 10000.0, "limits": {"cash": 80000.0}}
