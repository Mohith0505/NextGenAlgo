from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from app.broker_adapters.angel import AngelAdapter
from app.broker_adapters.base import BrokerAuthenticationError, BrokerOrderError, BrokerError, OrderPayload


class DummyResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def raise_for_status(self) -> None:  # noqa: D401 - simple stub
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return self._payload


class DummyTOTP:
    def __init__(self, secret: str) -> None:
        self.secret = secret

    def now(self) -> str:
        return "123456"


def test_connect_encodes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []

    def fake_request(method: str, url: str, **kwargs):
        calls.append((method, url))
        assert kwargs["headers"]["X-PrivateKey"] == "key"
        assert kwargs["json"]["clientcode"] == "CLIENT"
        payload = {
            "status": True,
            "data": {
                "jwtToken": "jwt-token",
                "refreshToken": "refresh-token",
                "feedToken": "feed-token",
                "expiresIn": 3600,
            },
        }
        return DummyResponse(payload)

    monkeypatch.setattr("app.broker_adapters.angel.httpx.request", fake_request)
    monkeypatch.setattr("app.broker_adapters.angel.pyotp.TOTP", lambda secret: DummyTOTP(secret))

    adapter = AngelAdapter()
    session = adapter.connect(
        {
            "client_code": "CLIENT",
            "password": "pass",
            "api_key": "key",
            "totp_secret": "BASE32SECRET",
        }
    )

    assert calls == [("POST", "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword")]
    assert session.expires_at is not None
    assert session.expires_at > datetime.now(timezone.utc)

    payload = adapter._decode_session(session.token)
    assert payload["jwt"] == "jwt-token"
    assert payload["api_key"] == "key"
    assert payload["client_code"] == "CLIENT"


def test_place_order_uses_symbol_map(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded_json: dict | None = None

    def fake_request(method: str, url: str, **kwargs):
        nonlocal recorded_json
        if url.endswith("/rest/auth/angelbroking/user/v1/loginByPassword"):
            payload = {
                "status": True,
                "data": {
                    "jwtToken": "jwt-token",
                    "refreshToken": "refresh-token",
                    "feedToken": "feed-token",
                },
            }
        else:
            recorded_json = kwargs.get("json")
            payload = {"status": True, "data": {"orderid": "12345", "status": "SUCCESS"}}
        return DummyResponse(payload)

    monkeypatch.setattr("app.broker_adapters.angel.httpx.request", fake_request)
    monkeypatch.setattr("app.broker_adapters.angel.pyotp.TOTP", lambda secret: DummyTOTP(secret))

    adapter = AngelAdapter(
        config={
            "symbols": {
                "SBIN": {
                    "tradingsymbol": "SBIN-EQ",
                    "symbol_token": "3045",
                    "exchange": "NSE",
                }
            }
        }
    )

    session = adapter.connect(
        {
            "client_code": "CLIENT",
            "password": "pass",
            "api_key": "key",
            "totp_secret": "BASE32SECRET",
        }
    )

    order_payload = OrderPayload(
        symbol="SBIN",
        side="BUY",
        quantity=10,
        order_type="LIMIT",
        price=780.5,
    )
    result = adapter.place_order(session.token, order_payload)

    assert result.order_id == "12345"
    assert recorded_json is not None
    assert recorded_json["tradingsymbol"] == "SBIN-EQ"
    assert recorded_json["symboltoken"] == "3045"
    assert recorded_json["quantity"] == "10"
    assert recorded_json["squareoff"] == "0"
    assert recorded_json["price"] == "780.50"


def test_resolve_instrument_requires_mapping() -> None:
    adapter = AngelAdapter()
    session_token = adapter._encode_session(
        {
            "jwt": "jwt",
            "api_key": "key",
        }
    )

    with pytest.raises(BrokerOrderError):
        adapter.place_order(
            session_token,
            OrderPayload(symbol="UNKNOWN", side="BUY", quantity=1, order_type="MARKET"),
        )


def test_invalid_session_token() -> None:
    adapter = AngelAdapter()
    with pytest.raises(BrokerAuthenticationError):
        adapter.place_order(
            "invalid-token",
            OrderPayload(symbol="SBIN::3045::NSE", side="BUY", quantity=1, order_type="MARKET"),
        )

def test_call_api_non_json(monkeypatch):
    def fake_request(method, url, **kwargs):
        class Resp:
            status_code = 500
            text = "Server maintenance"

            def raise_for_status(self):
                return None

            def json(self):
                raise ValueError("not json")

        return Resp()

    monkeypatch.setattr("app.broker_adapters.angel.httpx.request", fake_request)

    adapter = AngelAdapter()
    with pytest.raises(BrokerError) as exc_info:
        adapter._call_api("GET", "/test", api_key="k", client_code=None, jwt_token=None)
    assert "Server maintenance" in str(exc_info.value)


