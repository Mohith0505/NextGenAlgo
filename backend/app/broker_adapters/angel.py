import base64
import os
import binascii
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Any, Mapping

import httpx
import pyotp
from loguru import logger

from .base import (
    BaseBrokerAdapter,
    BrokerAuthenticationError,
    BrokerError,
    BrokerOrderError,
    BrokerSession,
    OrderPayload,
    OrderResult,
)


class AngelAdapter(BaseBrokerAdapter):
    """Angel One SmartAPI adapter supporting session login and basic order flow."""

    broker_name = "angel_one"
    aliases = {"angel", "angel-one", "angelone", "smartapi", "angel_one"}
    required_keys = {"client_code", "password", "api_key", "totp_secret"}

    base_url = "https://apiconnect.angelone.in"
    login_endpoint = "/rest/auth/angelbroking/user/v1/loginByPassword"
    order_place_endpoint = "/rest/secure/angelbroking/order/v1/placeOrder"
    order_cancel_endpoint = "/rest/secure/angelbroking/order/v1/cancelOrder"
    margin_endpoint = "/rest/secure/angelbroking/user/v1/getRMS"
    ltp_endpoint = "/rest/secure/angelbroking/order/v1/getLtpData"

    _session_prefix = "angel:"
    _default_timeout = 15.0

    def __init__(self, *, config: Mapping[str, Any] | None = None) -> None:
        super().__init__(config=config)
        timeout_value = self.config.get("timeout")
        if timeout_value is None:
            timeout_value = os.getenv("ANGELONE_HTTP_TIMEOUT")
        try:
            self._timeout = float(timeout_value) if timeout_value is not None else self._default_timeout
        except (TypeError, ValueError):
            self._timeout = self._default_timeout

        self._default_exchange = self._string_config("default_exchange", "ANGELONE_DEFAULT_EXCHANGE", "NSE").upper()
        self._default_variety = self._string_config("default_variety", "ANGELONE_DEFAULT_VARIETY", "NORMAL").upper()
        self._default_product_type = self._string_config("default_product_type", "ANGELONE_DEFAULT_PRODUCT_TYPE", "INTRADAY").upper()
        self._default_duration = self._string_config("default_duration", "ANGELONE_DEFAULT_DURATION", "DAY").upper()
        timezone_name = self._string_config("timezone", "ANGELONE_TIMEZONE", "Asia/Kolkata")
        try:
            self._timezone = ZoneInfo(timezone_name)
        except Exception:
            self._timezone = ZoneInfo("Asia/Kolkata")

        self._symbol_map: dict[str, dict[str, str]] = {}
        config_symbols = self.config.get("symbols") or {}
        if isinstance(config_symbols, dict):
            for key, value in config_symbols.items():
                self._symbol_map[key.upper()] = value

        env_symbol_map = os.getenv("ANGELONE_SYMBOL_MAP")
        if env_symbol_map:
            try:
                env_symbols = json.loads(env_symbol_map)
            except json.JSONDecodeError:
                logger.warning("ANGELONE_SYMBOL_MAP is not valid JSON; skipping")
            else:
                if isinstance(env_symbols, dict):
                    for key, value in env_symbols.items():
                        self._symbol_map[key.upper()] = value


    # ------------------------------------------------------------------
    # Public adapter API
    # ------------------------------------------------------------------
    def connect(self, credentials: Mapping[str, Any]) -> BrokerSession:
        missing = self.required_keys - credentials.keys()
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise BrokerAuthenticationError(f"Missing credentials for Angel One: {missing_list}")

        client_code = str(credentials["client_code"]).strip()
        password = str(credentials["password"]).strip()
        api_key = str(credentials["api_key"]).strip()
        totp_secret = str(credentials["totp_secret"]).replace(" ", "").upper()

        try:
            totp_code = pyotp.TOTP(totp_secret).now()
        except (binascii.Error, ValueError) as exc:
            raise BrokerAuthenticationError("Invalid Angel One TOTP secret") from exc

        payload = {
            "clientcode": client_code,
            "password": password,
            "totp": totp_code,
        }

        logger.debug("Angel One login request", client_code=client_code)
        data = self._call_api(
            "POST",
            self.login_endpoint,
            api_key=api_key,
            client_code=client_code,
            json=payload,
        )

        jwt_token = data.get("jwtToken")
        refresh_token = data.get("refreshToken")
        feed_token = data.get("feedToken")
        expires_in = data.get("expiresIn")
        jwt_expiry_iso = data.get("jwtTokenExpiry")

        if not jwt_token:
            raise BrokerAuthenticationError("Angel One login did not return a JWT token")

        expires_at = None
        if isinstance(expires_in, (int, float)):
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=float(expires_in))
        elif isinstance(jwt_expiry_iso, str):
            try:
                expires_at = datetime.fromisoformat(jwt_expiry_iso)
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
            except ValueError:
                expires_at = None

        session_payload = {
            "jwt": jwt_token,
            "refresh": refresh_token,
            "feed": feed_token,
            "api_key": api_key,
            "client_code": client_code,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }
        token = self._encode_session(session_payload)

        metadata = {k: v for k, v in session_payload.items() if k in {"refresh", "feed", "client_code"}}
        return BrokerSession(token=token, expires_at=expires_at, metadata=metadata)

    def validate_session(self, session_token: str) -> bool:
        try:
            payload = self._decode_session(session_token)
        except BrokerAuthenticationError:
            return False

        expires_at_str = payload.get("expires_at")
        if not expires_at_str:
            return True
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
        except ValueError:
            return True
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at > datetime.now(timezone.utc)

    def get_ltp(self, session_token: str, symbol: str) -> float:
        session = self._decode_session(session_token)
        instrument = self._resolve_instrument(symbol)
        request_payload = {
            "exchange": instrument["exchange"],
            "tradingsymbol": instrument["tradingsymbol"],
            "symboltoken": instrument["symbol_token"],
        }
        data = self._call_api(
            "POST",
            self.ltp_endpoint,
            api_key=session["api_key"],
            client_code=session.get("client_code"),
            jwt_token=session["jwt"],
            json=request_payload,
        )
        try:
            payload = data.get("data") if isinstance(data, dict) else None
            if isinstance(payload, list) and payload:
                return float(payload[0].get("ltp"))
            if isinstance(data, dict) and "ltp" in data:
                return float(data["ltp"])
            raise KeyError
        except (KeyError, TypeError, ValueError) as exc:
            raise BrokerError("Angel One LTP response missing 'ltp'") from exc

    def place_order(self, session_token: str, payload: OrderPayload) -> OrderResult:
        session = self._decode_session(session_token)
        instrument = self._resolve_instrument(payload.symbol)

        order_request = self._build_order_request(payload, instrument)
        data = self._call_api(
            "POST",
            self.order_place_endpoint,
            api_key=session["api_key"],
            client_code=session.get("client_code"),
            jwt_token=session["jwt"],
            json=order_request,
        )

        order_id = data.get("orderid") or data.get("orderId")
        if not order_id:
            raise BrokerOrderError("Angel One did not return an order id")

        metadata = {
            "exchange": instrument["exchange"],
            "tradingsymbol": instrument["tradingsymbol"],
            "symbol_token": instrument["symbol_token"],
            "producttype": order_request.get("producttype"),
            "variety": order_request.get("variety"),
        }
        return OrderResult(order_id=str(order_id), status=data.get("status", "PENDING"), metadata=metadata)

    def cancel_order(self, session_token: str, order_id: str) -> bool:
        session = self._decode_session(session_token)
        payload = {
            "variety": self._default_variety,
            "orderid": order_id,
        }
        data = self._call_api(
            "POST",
            self.order_cancel_endpoint,
            api_key=session["api_key"],
            client_code=session.get("client_code"),
            jwt_token=session["jwt"],
            json=payload,
        )
        return bool(data.get("status", True))

    def get_margin(self, session_token: str) -> Mapping[str, Any]:
        session = self._decode_session(session_token)
        try:
            data = self._call_api(
                "POST",
                self.margin_endpoint,
                api_key=session["api_key"],
                client_code=session.get("client_code"),
                jwt_token=session["jwt"],
                json={},
            )
        except BrokerError:
            return {}
        margin_data = data.get("data") or data
        if isinstance(margin_data, dict):
            return margin_data
        return {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_order_request(self, payload: OrderPayload, instrument: Mapping[str, str]) -> dict[str, Any]:
        order_type = payload.order_type.upper()
        quantity = int(payload.quantity)
        request: dict[str, Any] = {
            "variety": self._default_variety,
            "tradingsymbol": instrument["tradingsymbol"],
            "symboltoken": instrument["symbol_token"],
            "exchange": instrument["exchange"],
            "transactiontype": payload.side.upper(),
            "ordertype": order_type,
            "producttype": instrument.get("producttype", self._default_product_type),
            "duration": instrument.get("duration", self._default_duration),
            "quantity": str(quantity),
            "disclosedquantity": "0",
            "triggerprice": "0",
            "price": "0",
            "squareoff": "0",
            "stoploss": "0",
            "trailingStopLoss": "0",
        }

        if order_type == "LIMIT" and payload.price is not None:
            request["price"] = f"{float(payload.price):.2f}"
        elif order_type == "LIMIT" and payload.price is None:
            raise BrokerOrderError("Limit orders require a price for Angel One")

        if payload.stop_loss is not None:
            formatted_sl = f"{float(payload.stop_loss):.2f}"
            request["triggerprice"] = formatted_sl
            request["stoploss"] = formatted_sl
        if payload.take_profit is not None:
            formatted_tp = f"{float(payload.take_profit):.2f}"
            request["squareoff"] = formatted_tp
            request["targetprice"] = formatted_tp

        return request

    def _resolve_instrument(self, symbol: str) -> dict[str, str]:
        if not symbol:
            raise BrokerOrderError("Symbol is required for Angel One orders")

        normalized = symbol.upper()
        if normalized in self._symbol_map:
            return self._normalize_instrument_dict(self._symbol_map[normalized])

        # Allow inline format: TRADINGSYMBOL::TOKEN::EXCHANGE or TRADINGSYMBOL|TOKEN|EXCHANGE
        for separator in ("::", "|", ","):
            if separator in symbol:
                parts = [part.strip() for part in symbol.split(separator)]
                if len(parts) == 3:
                    tradingsymbol, symbol_token, exchange = parts
                    return self._normalize_instrument_dict(
                        {
                            "tradingsymbol": tradingsymbol,
                            "symbol_token": symbol_token,
                            "exchange": exchange or self._default_exchange,
                        }
                    )

        raise BrokerOrderError(
            "Angel One requires a symbol token. Provide a mapping via adapter config or use the format "
            "'TRADINGSYMBOL::TOKEN::EXCHANGE'."
        )

    @staticmethod
    def _normalize_instrument_dict(raw: Mapping[str, str]) -> dict[str, str]:
        try:
            tradingsymbol = str(raw["tradingsymbol"]).strip()
            symbol_token = str(raw["symbol_token"]).strip()
        except KeyError as exc:
            raise BrokerOrderError("Instrument mapping must include 'tradingsymbol' and 'symbol_token'") from exc
        exchange = str(raw.get("exchange") or "NSE").strip().upper()
        if not tradingsymbol or not symbol_token:
            raise BrokerOrderError("Invalid instrument mapping for Angel One")
        payload: dict[str, str] = {
            "tradingsymbol": tradingsymbol,
            "symbol_token": symbol_token,
            "exchange": exchange,
        }
        if "producttype" in raw:
            payload["producttype"] = str(raw["producttype"]).strip().upper()
        if "duration" in raw:
            payload["duration"] = str(raw["duration"]).strip().upper()
        return payload

    def _string_config(self, key: str, env_var: str, default: str) -> str:
        value = self.config.get(key)
        if value is None:
            value = os.getenv(env_var)
        if value is None:
            return default
        value_str = str(value).strip()
        return value_str or default

    def _call_api(
        self,
        method: str,
        path: str,
        *,
        api_key: str | None,
        client_code: str | None,
        jwt_token: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if not api_key:
            raise BrokerAuthenticationError("Angel One API key is required")

        headers = self._base_headers(api_key=api_key, client_code=client_code, jwt_token=jwt_token)

        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                timeout=self._timeout,
                **kwargs,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Angel One API error",
                status_code=exc.response.status_code,
                body=exc.response.text,
            )
            raise BrokerError(f"Angel One API error: {exc}") from exc
        except httpx.HTTPError as exc:
            raise BrokerError(f"Angel One API request failed: {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            snippet = response.text.strip()[:200]
            if not snippet:
                snippet = f'status={response.status_code}'
            raise BrokerError(f"Angel One returned a non-JSON response: {snippet}") from exc

        if not isinstance(payload, dict):
            snippet = str(payload)[:200]
            raise BrokerError(f"Angel One response is malformed: {snippet}")

        if payload.get("status") is False:
            message = payload.get("message") or "Angel One request failed"
            raise BrokerError(message)

        data = payload.get("data")
        return data if isinstance(data, dict) else payload

    def _base_headers(
        self,
        *,
        api_key: str,
        client_code: str | None,
        jwt_token: str | None,
    ) -> dict[str, str]:
        client_time = datetime.now(self._timezone).strftime("%Y-%m-%d %H:%M:%S")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": self._string_config("user_type", "ANGELONE_USER_TYPE", "USER"),
            "X-SourceID": self._string_config("source_id", "ANGELONE_SOURCE_ID", "WEB"),
            "X-ClientLocalIP": self._string_config("client_local_ip", "ANGELONE_CLIENT_LOCAL_IP", "127.0.0.1"),
            "X-ClientPublicIP": self._string_config("client_public_ip", "ANGELONE_CLIENT_PUBLIC_IP", "127.0.0.1"),
            "X-MACAddress": self._string_config("client_mac_address", "ANGELONE_CLIENT_MAC", "AA-BB-CC-DD-EE-FF"),
            "X-ClientTime": client_time,
            "X-ClientTimezone": self._string_config("client_timezone", "ANGELONE_CLIENT_TIMEZONE", "Asia/Kolkata"),
            "X-PrivateKey": api_key,
        }
        if client_code:
            headers["X-ClientID"] = client_code
        if jwt_token:
            headers["Authorization"] = f"Bearer {jwt_token}"
        return headers

    def _encode_session(self, payload: Mapping[str, Any]) -> str:
        raw = json.dumps(payload, separators=(",", ":"))
        encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")
        return f"{self._session_prefix}{encoded}"

    def _decode_session(self, token: str) -> dict[str, Any]:
        if not token:
            raise BrokerAuthenticationError("Angel One session token missing")
        if token.startswith(self._session_prefix):
            token = token[len(self._session_prefix) :]
        padding = "=" * (-len(token) % 4)
        try:
            raw = base64.urlsafe_b64decode(f"{token}{padding}").decode("utf-8")
            payload = json.loads(raw)
        except (binascii.Error, ValueError, json.JSONDecodeError) as exc:
            raise BrokerAuthenticationError("Angel One session token is invalid") from exc
        if not isinstance(payload, dict):
            raise BrokerAuthenticationError("Angel One session token payload malformed")
        required = {"jwt", "api_key"}
        if not required.issubset(payload.keys()):
            raise BrokerAuthenticationError("Angel One session token missing required fields")
        return payload


__all__ = ["AngelAdapter"]





