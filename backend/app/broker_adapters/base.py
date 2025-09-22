from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping


@dataclass(slots=True)
class BrokerSession:
    """Represents an authenticated session with a broker API."""

    token: str
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OrderPayload:
    """Normalized order request passed to broker adapters."""

    symbol: str
    side: str
    quantity: int
    order_type: str = "MARKET"
    price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    strategy_id: str | None = None


@dataclass(slots=True)
class OrderResult:
    """Standardized broker response for an order attempt."""

    order_id: str
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BrokerError(RuntimeError):
    """Base error raised for adapter level issues."""


class BrokerAuthenticationError(BrokerError):
    """Raised when broker authentication fails."""


class BrokerOrderError(BrokerError):
    """Raised when broker order placement fails."""


class BaseBrokerAdapter(ABC):
    """Interface that every broker adapter implementation must follow."""

    broker_name: str = "generic"
    aliases: set[str] = set()

    def __init__(self, *, config: Mapping[str, Any] | None = None) -> None:
        self.config = dict(config or {})

    @abstractmethod
    def connect(self, credentials: Mapping[str, Any]) -> BrokerSession:
        """Authenticate with the broker and return a session token."""

    def validate_session(self, session_token: str) -> bool:
        """Adapters may override to verify whether a session token is still valid."""

        return bool(session_token)

    def get_ltp(self, session_token: str, symbol: str) -> float:
        raise NotImplementedError("LTP retrieval not implemented for this adapter")

    def place_order(self, session_token: str, payload: OrderPayload) -> OrderResult:
        raise NotImplementedError("Order placement not implemented for this adapter")

    def modify_order(
        self, session_token: str, order_id: str, payload: Mapping[str, Any]
    ) -> OrderResult:
        raise NotImplementedError("Order modification not implemented for this adapter")

    def cancel_order(self, session_token: str, order_id: str) -> bool:
        raise NotImplementedError("Order cancel not implemented for this adapter")

    def get_positions(self, session_token: str) -> list[dict[str, Any]]:
        return []

    def get_holdings(self, session_token: str) -> list[dict[str, Any]]:
        return []

    def get_margin(self, session_token: str) -> Mapping[str, Any]:
        return {}
