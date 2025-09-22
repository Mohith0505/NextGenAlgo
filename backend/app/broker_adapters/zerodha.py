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


class ZerodhaAdapter(BaseBrokerAdapter):
    """Mocked Zerodha (Kite Connect) adapter used for service wiring."""

    broker_name = "zerodha"
    aliases = {"kite", "kiteconnect", "kite_connect"}
    required_keys = {"api_key", "api_secret", "request_token"}

    def connect(self, credentials: Mapping[str, str]) -> BrokerSession:
        missing = self.required_keys - credentials.keys()
        if missing:
            raise BrokerAuthenticationError(
                f"Missing credentials for Zerodha: {', '.join(sorted(missing))}"
            )
        token = f"KITE-{uuid.uuid4().hex}"
        metadata = {"access_token": token, "public_token": uuid.uuid4().hex}
        return BrokerSession(token=token, metadata=metadata)

    def get_ltp(self, session_token: str, symbol: str) -> float:
        base = abs(hash(symbol)) % 10000
        return round(100 + base / 200, 2)

    def place_order(self, session_token: str, payload: OrderPayload) -> OrderResult:
        if not session_token:
            raise BrokerAuthenticationError("Zerodha session expired; please reconnect.")
        order_id = f"KITE-ORD-{uuid.uuid4().hex[:8]}"
        metadata = {
            "segment": "NFO" if payload.symbol.endswith("FUT") else "NSE",
            "product": "NRML" if payload.order_type == "LIMIT" else "MIS",
        }
        return OrderResult(order_id=order_id, status="PENDING", metadata=metadata)

    def modify_order(self, session_token: str, order_id: str, payload):
        metadata = {"modified_fields": list(payload.keys())}
        return OrderResult(order_id=order_id, status="MODIFIED", metadata=metadata)

    def cancel_order(self, session_token: str, order_id: str) -> bool:
        return True

    def get_margin(self, session_token: str):
        return {"available": 500000.0, "utilized": 125000.0, "span": 300000.0}
