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
from app.utils.angel_master import get_angel_instrument_master

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
    token_refresh_endpoint = "/rest/auth/angelbroking/jwt/v1/generateTokens"
    profile_endpoint = "/rest/secure/angelbroking/user/v1/getProfile"
    logout_endpoint = "/rest/secure/angelbroking/user/v1/logout"
    order_place_endpoint = "/rest/secure/angelbroking/order/v1/placeOrder"
    order_cancel_endpoint = "/rest/secure/angelbroking/order/v1/cancelOrder"
    margin_endpoint = "/rest/secure/angelbroking/user/v1/getRMS"
    ltp_endpoint = "/rest/secure/angelbroking/order/v1/getLtpData"
    positions_endpoint = "/rest/secure/angelbroking/order/v1/getPosition"
    holdings_endpoint = "/rest/secure/angelbroking/portfolio/v1/getHolding"
    all_holdings_endpoint = "/rest/secure/angelbroking/portfolio/v1/getAllHolding"
    convert_position_endpoint = "/rest/secure/angelbroking/order/v1/convertPosition"

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
        self._instrument_master = get_angel_instrument_master()
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


    def refresh_session(self, session_token: str) -> BrokerSession:
        session = self._decode_session(session_token)
        api_key = session.get("api_key")
        jwt_token = session.get("jwt")
        refresh_token = session.get("refresh")
        if not api_key or not jwt_token or not refresh_token:
            raise BrokerAuthenticationError("Angel One session token is missing refresh credentials")

        try:
            data = self._call_api(
                "POST",
                self.token_refresh_endpoint,
                api_key=api_key,
                client_code=session.get("client_code"),
                jwt_token=jwt_token,
                json={"refreshToken": refresh_token},
            )
        except BrokerError as exc:
            raise BrokerAuthenticationError("Angel One session refresh failed") from exc

        new_jwt = data.get("jwtToken") or jwt_token
        new_refresh = data.get("refreshToken") or refresh_token
        new_feed = data.get("feedToken") or session.get("feed")
        expires_in = data.get("expiresIn")
        jwt_expiry_iso = data.get("jwtTokenExpiry")

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

        if expires_at is None:
            prior_expiry = session.get("expires_at")
            if isinstance(prior_expiry, str):
                try:
                    expires_at = datetime.fromisoformat(prior_expiry)
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                except ValueError:
                    expires_at = None

        session_payload = {
            "jwt": new_jwt,
            "refresh": new_refresh,
            "feed": new_feed,
            "api_key": api_key,
            "client_code": session.get("client_code"),
            "expires_at": expires_at.isoformat() if expires_at else None,
        }
        token = self._encode_session(session_payload)
        metadata = {k: v for k, v in session_payload.items() if k in {"refresh", "feed", "client_code"}}
        return BrokerSession(token=token, expires_at=expires_at, metadata=metadata)



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
        instrument = self._resolve_instrument(
            payload.symbol,
            exchange=payload.exchange,
            symbol_token=payload.symbol_token,
        )

        if payload.exchange:
            instrument["exchange"] = payload.exchange.strip().upper()
        if payload.product_type:
            instrument["producttype"] = payload.product_type.strip().upper()
        if payload.duration:
            instrument["duration"] = payload.duration.strip().upper()

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

    def get_positions(self, session_token: str) -> Mapping[str, Any]:
        session = self._decode_session(session_token)
        try:
            data = self._call_api(
                "GET",
                self.positions_endpoint,
                api_key=session["api_key"],
                client_code=session.get("client_code"),
                jwt_token=session["jwt"],
            )
        except BrokerError:
            return {"net": [], "day": []}

        payload = data.get("data") if isinstance(data, dict) else data
        if payload is None and isinstance(data, dict):
            payload = data
        net_positions: list[dict[str, Any]] = []
        day_positions: list[dict[str, Any]] = []

        if isinstance(payload, dict):
            net_raw = payload.get("net")
            day_raw = payload.get("day")
            if isinstance(net_raw, list):
                net_positions = [
                    self._normalize_position(item)
                    for item in net_raw
                    if isinstance(item, dict)
                ]
            if isinstance(day_raw, list):
                day_positions = [
                    self._normalize_position(item)
                    for item in day_raw
                    if isinstance(item, dict)
                ]
        elif isinstance(payload, list):
            net_positions = [
                self._normalize_position(item)
                for item in payload
                if isinstance(item, dict)
            ]

        return {"net": net_positions, "day": day_positions}

    def get_holdings(self, session_token: str) -> Mapping[str, Any]:
        session = self._decode_session(session_token)
        try:
            data = self._call_api(
                "GET",
                self.all_holdings_endpoint,
                api_key=session["api_key"],
                client_code=session.get("client_code"),
                jwt_token=session["jwt"],
            )
        except BrokerError:
            return {"holdings": [], "summary": None}

        payload = data.get("data") if isinstance(data, dict) else data
        if payload is None and isinstance(data, dict):
            payload = data
        holdings_payload: list[dict[str, Any]] = []
        summary_payload: dict[str, Any] | None = None

        if isinstance(payload, dict):
            raw_holdings = payload.get("holdings")
            if isinstance(raw_holdings, list):
                holdings_payload = [item for item in raw_holdings if isinstance(item, dict)]
            summary_raw = payload.get("totalholding")
            if isinstance(summary_raw, dict):
                summary_payload = summary_raw
        elif isinstance(payload, list):
            holdings_payload = [item for item in payload if isinstance(item, dict)]

        holdings = [self._normalize_holding(item) for item in holdings_payload]
        summary = (
            self._normalize_holding_summary(summary_payload) if summary_payload else None
        )
        return {"holdings": holdings, "summary": summary}

    def convert_position(self, session_token: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        session = self._decode_session(session_token)
        data = self._call_api(
            "POST",
            self.convert_position_endpoint,
            api_key=session["api_key"],
            client_code=session.get("client_code"),
            jwt_token=session["jwt"],
            json=dict(payload),
        )
        if isinstance(data, dict):
            return data
        return {"status": True, "data": data}

    def _normalize_position(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        exchange = self._clean_string(raw.get("exchange"))
        normalized["exchange"] = exchange.upper() if exchange else ""
        normalized["tradingsymbol"] = self._clean_string(raw.get("tradingsymbol")) or ""
        symbol_token = self._clean_string(raw.get("symboltoken")) or self._clean_string(raw.get("symbol_token"))
        normalized["symbol_token"] = symbol_token or ""
        product = self._clean_string(raw.get("producttype")) or self._clean_string(raw.get("product_type"))
        normalized["product_type"] = product.upper() if product else None
        symbol_name = self._clean_string(raw.get("symbolname")) or self._clean_string(raw.get("symbol_name"))
        normalized["symbol_name"] = symbol_name
        instrument = self._clean_string(raw.get("instrumenttype")) or self._clean_string(raw.get("instrument_type"))
        normalized["instrument_type"] = instrument.upper() if instrument else None
        normalized["buy_qty"] = self._coerce_int(raw.get("buyqty"))
        normalized["sell_qty"] = self._coerce_int(raw.get("sellqty"))
        normalized["buy_amount"] = self._coerce_float(raw.get("buyamount"))
        normalized["sell_amount"] = self._coerce_float(raw.get("sellamount"))
        normalized["buy_avg_price"] = self._coerce_float(raw.get("buyavgprice"))
        normalized["sell_avg_price"] = self._coerce_float(raw.get("sellavgprice"))
        normalized["avg_net_price"] = self._coerce_float(raw.get("avgnetprice"))
        normalized["net_value"] = self._coerce_float(raw.get("netvalue"))
        normalized["net_qty"] = self._coerce_int(raw.get("netqty"))
        normalized["total_buy_value"] = self._coerce_float(raw.get("totalbuyvalue"))
        normalized["total_sell_value"] = self._coerce_float(raw.get("totalsellvalue"))
        normalized["net_price"] = self._coerce_float(raw.get("netprice"))
        normalized["lot_size"] = self._coerce_int(raw.get("lotsize"), default=None)
        expiry = self._clean_string(raw.get("expirydate"))
        normalized["expiry_date"] = expiry

        skip_keys = {
            "exchange",
            "tradingsymbol",
            "symboltoken",
            "symbol_token",
            "producttype",
            "product_type",
            "symbolname",
            "symbol_name",
            "instrumenttype",
            "instrument_type",
            "buyqty",
            "sellqty",
            "buyamount",
            "sellamount",
            "buyavgprice",
            "sellavgprice",
            "avgnetprice",
            "netvalue",
            "netqty",
            "totalbuyvalue",
            "totalsellvalue",
            "netprice",
            "lotsize",
            "expirydate",
        }
        for key, value in raw.items():
            if key not in skip_keys:
                normalized[key] = value
        return normalized

    def _normalize_holding(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        normalized["tradingsymbol"] = self._clean_string(raw.get("tradingsymbol")) or ""
        exchange = self._clean_string(raw.get("exchange"))
        normalized["exchange"] = exchange.upper() if exchange else ""
        normalized["isin"] = self._clean_string(raw.get("isin"))
        normalized["t1_quantity"] = self._coerce_int(raw.get("t1quantity"))
        normalized["realised_quantity"] = self._coerce_int(raw.get("realisedquantity"))
        normalized["quantity"] = self._coerce_int(raw.get("quantity"))
        normalized["authorised_quantity"] = self._coerce_int(raw.get("authorisedquantity"))
        product = self._clean_string(raw.get("product"))
        normalized["product"] = product.upper() if product else None
        normalized["collateral_quantity"] = self._coerce_int(raw.get("collateralquantity"), default=None)
        normalized["collateral_type"] = self._clean_string(raw.get("collateraltype"))
        normalized["haircut"] = self._coerce_float(raw.get("haircut"))
        normalized["average_price"] = self._coerce_float(raw.get("averageprice"))
        normalized["ltp"] = self._coerce_float(raw.get("ltp"))
        normalized["symbol_token"] = self._clean_string(raw.get("symboltoken")) or ""
        normalized["close"] = self._coerce_float(raw.get("close"))
        normalized["profit_and_loss"] = self._coerce_float(raw.get("profitandloss"))
        normalized["pnl_percentage"] = self._coerce_float(raw.get("pnlpercentage"))

        skip_keys = {
            "tradingsymbol",
            "exchange",
            "isin",
            "t1quantity",
            "realisedquantity",
            "quantity",
            "authorisedquantity",
            "product",
            "collateralquantity",
            "collateraltype",
            "haircut",
            "averageprice",
            "ltp",
            "symboltoken",
            "close",
            "profitandloss",
            "pnlpercentage",
        }
        for key, value in raw.items():
            if key not in skip_keys:
                normalized[key] = value
        return normalized

    def _normalize_holding_summary(self, raw: Mapping[str, Any] | None) -> dict[str, Any] | None:
        if raw is None:
            return None
        return {
            "total_holding_value": self._coerce_float(raw.get("totalholdingvalue")),
            "total_investment_value": self._coerce_float(raw.get("totalinvvalue")),
            "total_profit_and_loss": self._coerce_float(raw.get("totalprofitandloss")),
            "total_pnl_percentage": self._coerce_float(raw.get("totalpnlpercentage")),
        }

    @staticmethod
    def _coerce_int(value: Any, *, default: int | None = 0) -> int | None:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            cleaned = value.replace(",", "").replace(" ", "").strip()
            if cleaned in {"", "-", "--"}:
                return default
            try:
                return int(float(cleaned))
            except ValueError:
                return default
        return default

    @staticmethod
    def _coerce_float(value: Any, *, default: float | None = None) -> float | None:
        if value is None:
            return default
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.replace(",", "").replace(" ", "").strip()
            if cleaned in {"", "-", "--"}:
                return default
            try:
                return float(cleaned)
            except ValueError:
                return default
        return default

    @staticmethod
    def _clean_string(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def get_margin(self, session_token: str) -> Mapping[str, Any]:
        session = self._decode_session(session_token)
        try:
            data = self._call_api(
                "GET",
                self.margin_endpoint,
                api_key=session["api_key"],
                client_code=session.get("client_code"),
                jwt_token=session["jwt"],
            )
        except BrokerError:
            return {}
        margin_data = data.get("data") if isinstance(data, dict) else None
        if isinstance(margin_data, dict):
            return margin_data
        if isinstance(data, dict):
            return data
        return {}

    def get_profile(self, session_token: str) -> Mapping[str, Any]:
        session = self._decode_session(session_token)
        try:
            data = self._call_api(
                "GET",
                self.profile_endpoint,
                api_key=session["api_key"],
                client_code=session.get("client_code"),
                jwt_token=session["jwt"],
            )
        except BrokerError:
            return {}
        profile_data = data.get("data") if isinstance(data, dict) else None
        if isinstance(profile_data, dict):
            return profile_data
        if isinstance(data, dict):
            return data
        return {}

    def logout(self, session_token: str) -> bool:
        session = self._decode_session(session_token)
        client_code = session.get("client_code")
        if not client_code:
            raise BrokerAuthenticationError("Angel One session token is missing client code for logout")

        try:
            data = self._call_api(
                "POST",
                self.logout_endpoint,
                api_key=session["api_key"],
                client_code=client_code,
                jwt_token=session["jwt"],
                json={"clientcode": client_code},
            )
        except BrokerError as exc:
            raise BrokerAuthenticationError("Angel One logout failed") from exc

        if isinstance(data, dict):
            return bool(data.get("status", True))
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_order_request(self, payload: OrderPayload, instrument: Mapping[str, str]) -> dict[str, Any]:
        order_type = payload.order_type.upper()
        quantity = int(payload.quantity)
        request: dict[str, Any] = {
            "variety": (payload.variety or instrument.get("variety") or self._default_variety).upper(),
            "tradingsymbol": instrument["tradingsymbol"],
            "symboltoken": instrument["symbol_token"],
            "exchange": (payload.exchange or instrument.get("exchange") or self._default_exchange).upper(),
            "transactiontype": payload.side.upper(),
            "ordertype": order_type,
            "producttype": (payload.product_type or instrument.get("producttype") or self._default_product_type).upper(),
            "duration": (payload.duration or instrument.get("duration") or self._default_duration).upper(),
            "quantity": str(quantity),
            "disclosedquantity": str(payload.disclosed_quantity) if payload.disclosed_quantity is not None else "0",
            "triggerprice": "0",
            "price": "0",
            "squareoff": "0",
            "stoploss": "0",
            "trailingStopLoss": "0",
        }

        if payload.order_tag:
            request["ordertag"] = payload.order_tag[:20]

        if order_type == "LIMIT" and payload.price is not None:
            request["price"] = f"{float(payload.price):.2f}"
        elif order_type == "LIMIT" and payload.price is None:
            raise BrokerOrderError("Limit orders require a price for Angel One")
        elif order_type != "LIMIT" and payload.price is not None:
            request["price"] = f"{float(payload.price):.2f}"

        trigger_value = payload.trigger_price if payload.trigger_price is not None else payload.stop_loss
        if trigger_value is not None:
            formatted_trigger = f"{float(trigger_value):.2f}"
            request["triggerprice"] = formatted_trigger
        if payload.stop_loss is not None:
            request["stoploss"] = f"{float(payload.stop_loss):.2f}"

        tp_value = payload.squareoff if payload.squareoff is not None else payload.take_profit
        if tp_value is not None:
            formatted_tp = f"{float(tp_value):.2f}"
            request["squareoff"] = formatted_tp
            request["targetprice"] = formatted_tp

        if payload.trailing_stop_loss is not None:
            request["trailingStopLoss"] = f"{float(payload.trailing_stop_loss):.2f}"

        return request

    def _resolve_instrument(
        self, symbol: str, *, exchange: str | None = None, symbol_token: str | None = None
    ) -> dict[str, str]:
        if not symbol and not symbol_token:
            raise BrokerOrderError("Symbol is required for Angel One orders")

        raw_symbol = (symbol or "").strip()
        exchange_hint = (exchange or "").strip().upper() or None
        if raw_symbol and "::" not in raw_symbol and "|" not in raw_symbol and "," not in raw_symbol and ":" in raw_symbol:
            exchange_part, potential_symbol = [part.strip() for part in raw_symbol.split(":", 1)]
            if exchange_part and potential_symbol:
                if not exchange_hint:
                    exchange_hint = exchange_part.upper()
                raw_symbol = potential_symbol

        normalized = raw_symbol.upper() if raw_symbol else ""

        if symbol_token:
            tradingsymbol = normalized or symbol_token.strip()
            instrument_payload = {
                "tradingsymbol": tradingsymbol,
                "symbol_token": symbol_token.strip(),
                "exchange": exchange_hint or self._default_exchange,
            }
            return self._normalize_instrument_dict(instrument_payload)
        if normalized in self._symbol_map:
            return self._normalize_instrument_dict(self._symbol_map[normalized])

        # Allow inline format: TRADINGSYMBOL::TOKEN::EXCHANGE or TRADINGSYMBOL|TOKEN|EXCHANGE
        for separator in ("::", "|", ","):
            if separator in raw_symbol:
                parts = [part.strip() for part in raw_symbol.split(separator)]
                if len(parts) == 3:
                    tradingsymbol, symbol_token, exchange = parts
                    return self._normalize_instrument_dict(
                        {
                            "tradingsymbol": tradingsymbol,
                            "symbol_token": symbol_token,
                            "exchange": exchange or exchange_hint or self._default_exchange,
                        }
                    )

        lookup_exchange = exchange_hint or self._default_exchange
        master_record = self._instrument_master.lookup(normalized, exchange=lookup_exchange)
        if master_record is None and exchange_hint is not None:
            master_record = self._instrument_master.lookup(normalized)
        if master_record is not None:
            return self._normalize_instrument_dict(master_record)

        raise BrokerOrderError(
            "Angel One requires a symbol token. Provide a mapping via adapter config, ensure the instrument master is up to date, "
            "or use the format 'TRADINGSYMBOL::TOKEN::EXCHANGE'."
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
