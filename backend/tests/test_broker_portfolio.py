import pytest

from app.models.broker import Broker, BrokerStatus
from app.models.user import User
from app.schemas.portfolio import (
    PositionConvertRequest,
    PositionsResponse,
    HoldingsResponse,
    PositionConvertResponse,
)
from app.services.brokers import BrokerService


class DummyPortfolioAdapter:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.last_payload: dict | None = None

    def get_positions(self, token: str) -> dict:
        self.calls.append(f"positions:{token}")
        return {
            "net": [
                {
                    "tradingsymbol": "ABC",
                    "exchange": "NSE",
                    "symboltoken": "1",
                }
            ],
            "day": [],
        }

    def get_holdings(self, token: str) -> dict:
        self.calls.append(f"holdings:{token}")
        return {
            "holdings": [
                {
                    "tradingsymbol": "ABC",
                    "exchange": "NSE",
                    "quantity": "1",
                    "symboltoken": "1",
                }
            ],
            "summary": {"totalholdingvalue": "100"},
        }

    def convert_position(self, token: str, payload: dict) -> dict:
        self.calls.append(f"convert:{token}")
        self.last_payload = payload
        return {"status": True, "message": "OK", "data": payload}


@pytest.fixture()
def user(session):
    record = User(name="Portfolio User", email="portfolio@example.com", password_hash="hash")
    session.add(record)
    session.commit()
    return record


@pytest.fixture()
def broker(session, user):
    broker = Broker(
        user_id=user.id,
        broker_name="dummy",
        client_code="demo",
        session_token="token",
        status=BrokerStatus.connected,
    )
    session.add(broker)
    session.commit()
    return broker


def test_broker_service_get_positions(session, user, broker, monkeypatch: pytest.MonkeyPatch) -> None:
    service = BrokerService(session)
    adapter = DummyPortfolioAdapter()
    monkeypatch.setattr("app.services.brokers.get_adapter", lambda name: adapter)

    result = service.get_positions(user.id, broker.id)

    assert isinstance(result, PositionsResponse)
    assert result.net and result.net[0].tradingsymbol == "ABC"
    assert adapter.calls == ["positions:token"]


def test_broker_service_get_holdings(session, user, broker, monkeypatch: pytest.MonkeyPatch) -> None:
    service = BrokerService(session)
    adapter = DummyPortfolioAdapter()
    monkeypatch.setattr("app.services.brokers.get_adapter", lambda name: adapter)

    result = service.get_holdings(user.id, broker.id)

    assert isinstance(result, HoldingsResponse)
    assert result.holdings and result.holdings[0].tradingsymbol == "ABC"
    assert result.summary is not None
    assert result.summary.total_holding_value == 100.0
    assert adapter.calls == ["holdings:token"]


def test_broker_service_convert_position(session, user, broker, monkeypatch: pytest.MonkeyPatch) -> None:
    service = BrokerService(session)
    adapter = DummyPortfolioAdapter()
    monkeypatch.setattr("app.services.brokers.get_adapter", lambda name: adapter)

    payload = PositionConvertRequest(
        exchange="NSE",
        symbol_token="2885",
        tradingsymbol="RELIANCE-EQ",
        old_product_type="DELIVERY",
        new_product_type="INTRADAY",
        transaction_type="BUY",
        quantity=1,
    )

    result = service.convert_position(user.id, broker.id, payload)

    assert isinstance(result, PositionConvertResponse)
    assert result.status is True
    assert adapter.last_payload is not None
    assert adapter.last_payload["symboltoken"] == "2885"
    assert adapter.calls == ["convert:token"]
