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



def test_refresh_session_renews_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_request(method: str, url: str, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = kwargs.get("headers")
        captured["json"] = kwargs.get("json")
        payload = {
            "status": True,
            "data": {
                "jwtToken": "jwt-new",
                "refreshToken": "refresh-new",
                "feedToken": "feed-new",
                "expiresIn": 90,
            },
        }
        return DummyResponse(payload)

    monkeypatch.setattr("app.broker_adapters.angel.httpx.request", fake_request)

    adapter = AngelAdapter()
    session_token = adapter._encode_session(
        {
            "jwt": "jwt-old",
            "refresh": "refresh-old",
            "feed": "feed-old",
            "api_key": "key",
            "client_code": "CLIENT",
            "expires_at": None,
        }
    )

    session = adapter.refresh_session(session_token)

    assert captured["method"] == "POST"
    assert str(captured["url"]).endswith("/rest/auth/angelbroking/jwt/v1/generateTokens")
    assert captured["json"] == {"refreshToken": "refresh-old"}
    headers = captured.get("headers")
    assert isinstance(headers, dict)
    assert headers["Authorization"] == "Bearer jwt-old"

    payload = adapter._decode_session(session.token)
    assert payload["jwt"] == "jwt-new"
    assert payload["refresh"] == "refresh-new"
    assert payload["feed"] == "feed-new"
    assert session.metadata["refresh"] == "refresh-new"
    assert session.expires_at is not None


def test_refresh_session_requires_refresh_token() -> None:
    adapter = AngelAdapter()
    session_token = adapter._encode_session({"jwt": "jwt-old", "api_key": "key"})
    with pytest.raises(BrokerAuthenticationError):
        adapter.refresh_session(session_token)

def test_get_profile_returns_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_request(method: str, url: str, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = kwargs.get("headers")
        return DummyResponse({"status": True, "data": {"clientcode": "CLIENT", "name": "User"}})

    monkeypatch.setattr("app.broker_adapters.angel.httpx.request", fake_request)

    adapter = AngelAdapter()
    session_token = adapter._encode_session({"jwt": "jwt", "api_key": "key", "client_code": "CLIENT"})

    profile = adapter.get_profile(session_token)

    assert profile == {"clientcode": "CLIENT", "name": "User"}
    assert captured["method"] == "GET"
    assert str(captured["url"]).endswith("/rest/secure/angelbroking/user/v1/getProfile")
    headers = captured.get("headers")
    assert isinstance(headers, dict)
    assert headers["Authorization"] == "Bearer jwt"


def test_logout_clears_remote_session(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_request(method: str, url: str, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["json"] = kwargs.get("json")
        captured["headers"] = kwargs.get("headers")
        return DummyResponse({"status": True, "data": ""})

    monkeypatch.setattr("app.broker_adapters.angel.httpx.request", fake_request)

    adapter = AngelAdapter()
    session_token = adapter._encode_session({"jwt": "jwt", "api_key": "key", "client_code": "CLIENT"})

    result = adapter.logout(session_token)

    assert result is True
    assert captured["method"] == "POST"
    assert str(captured["url"]).endswith("/rest/secure/angelbroking/user/v1/logout")
    assert captured["json"] == {"clientcode": "CLIENT"}
    headers = captured.get("headers")
    assert isinstance(headers, dict)
    assert headers["Authorization"] == "Bearer jwt"


def test_logout_requires_client_code() -> None:
    adapter = AngelAdapter()
    session_token = adapter._encode_session({"jwt": "jwt", "api_key": "key"})
    with pytest.raises(BrokerAuthenticationError):
        adapter.logout(session_token)

def test_get_positions_normalizes_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    sample_position = {
        "exchange": "NSE",
        "tradingsymbol": "RELIANCE-EQ",
        "symboltoken": "2885",
        "producttype": "DELIVERY",
        "symbolname": "RELIANCE",
        "buyqty": "1",
        "sellqty": "0",
        "buyamount": "2235.80",
        "sellamount": "0",
        "buyavgprice": "2235.80",
        "sellavgprice": "0",
        "avgnetprice": "2235.80",
        "netvalue": "- 2235.80",
        "netqty": "1",
        "totalbuyvalue": "2235.80",
        "totalsellvalue": "0",
        "netprice": "2235.80",
        "lotsize": "1",
    }

    def fake_request(method: str, url: str, **kwargs):
        captured["method"] = method
        captured["url"] = url
        return DummyResponse({"status": True, "data": {"net": [sample_position], "day": []}})

    monkeypatch.setattr("app.broker_adapters.angel.httpx.request", fake_request)

    adapter = AngelAdapter()
    session_token = adapter._encode_session({"jwt": "jwt", "api_key": "key", "client_code": "CLIENT"})

    positions = adapter.get_positions(session_token)

    assert positions["net"]
    entry = positions["net"][0]
    assert entry["buy_qty"] == 1
    assert entry["net_value"] == -2235.8
    assert entry["product_type"] == "DELIVERY"
    assert captured["method"] == "GET"
    assert str(captured["url"]).endswith("/rest/secure/angelbroking/order/v1/getPosition")


def test_get_holdings_normalizes_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    sample_holding = {
        "tradingsymbol": "TATASTEEL-EQ",
        "exchange": "nse",
        "isin": "INE081A01020",
        "t1quantity": "0",
        "realisedquantity": "2",
        "quantity": "2",
        "authorisedquantity": "0",
        "product": "delivery",
        "averageprice": "111.87",
        "ltp": "130.15",
        "symboltoken": "3499",
        "close": "129.6",
        "profitandloss": "37",
        "pnlpercentage": "16.34",
    }
    sample_summary = {
        "totalholdingvalue": "5294",
        "totalinvvalue": "5116",
        "totalprofitandloss": "178.14",
        "totalpnlpercentage": "3.48",
    }

    def fake_request(method: str, url: str, **kwargs):
        captured["method"] = method
        captured["url"] = url
        return DummyResponse({"status": True, "data": {"holdings": [sample_holding], "totalholding": sample_summary}})

    monkeypatch.setattr("app.broker_adapters.angel.httpx.request", fake_request)

    adapter = AngelAdapter()
    session_token = adapter._encode_session({"jwt": "jwt", "api_key": "key", "client_code": "CLIENT"})

    holdings = adapter.get_holdings(session_token)

    assert holdings["holdings"]
    entry = holdings["holdings"][0]
    assert entry["exchange"] == "NSE"
    assert entry["quantity"] == 2
    assert entry["profit_and_loss"] == 37.0
    summary = holdings["summary"]
    assert summary is not None
    assert summary["total_profit_and_loss"] == 178.14
    assert str(captured["url"]).endswith("/rest/secure/angelbroking/portfolio/v1/getAllHolding")


def test_convert_position_posts_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_request(method: str, url: str, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["json"] = kwargs.get("json")
        return DummyResponse({"status": True, "message": "SUCCESS", "data": None})

    monkeypatch.setattr("app.broker_adapters.angel.httpx.request", fake_request)

    adapter = AngelAdapter()
    session_token = adapter._encode_session({"jwt": "jwt", "api_key": "key", "client_code": "CLIENT"})

    payload = {
        "exchange": "NSE",
        "symboltoken": "2885",
        "tradingsymbol": "RELIANCE-EQ",
        "oldproducttype": "DELIVERY",
        "newproducttype": "INTRADAY",
        "transactiontype": "BUY",
        "quantity": 1,
    }

    response = adapter.convert_position(session_token, payload)

    assert response["status"] is True
    assert captured["method"] == "POST"
    assert str(captured["url"]).endswith("/rest/secure/angelbroking/order/v1/convertPosition")
    assert captured["json"]["newproducttype"] == "INTRADAY"
