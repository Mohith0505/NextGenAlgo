from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping

import httpx

from app.core.config import PROJECT_ROOT

MASTER_URL = "https://margincalculator.angelone.in/OpenAPI_File/files/OpenAPIScripMaster.json"
CACHE_DIR = PROJECT_ROOT / "data"
CACHE_PATH = CACHE_DIR / "angel_openapi_master.json"
CACHE_MAX_AGE = timedelta(hours=24)


class AngelInstrumentMaster:
    """Loads and caches the Angel One OpenAPI scrip master."""

    def __init__(self, *, url: str = MASTER_URL, cache_path: Path = CACHE_PATH, auto_refresh: bool = True) -> None:
        self.url = url
        self.cache_path = cache_path
        self.auto_refresh = auto_refresh
        self._lock = threading.Lock()
        self._records: list[dict[str, Any]] | None = None
        self._index: dict[tuple[str, str], dict[str, Any]] = {}
        self._loaded_mtime: float | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def ensure_cache(self, *, force: bool = False) -> None:
        """Download the master file if missing or stale."""

        with self._lock:
            if not force and self.cache_path.exists() and not self._is_stale(self.cache_path):
                return
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                response = httpx.get(self.url, timeout=30.0)
                response.raise_for_status()
            except httpx.HTTPError as exc:  # pragma: no cover - network failure
                if self.cache_path.exists():
                    return
                raise RuntimeError(
                    "Unable to download Angel One scrip master. "
                    "Download it manually from the Angel margin calculator website."
                ) from exc
            self.cache_path.write_bytes(response.content)
            self._records = None
            self._index.clear()
            self._loaded_mtime = None

    def refresh(self) -> None:
        """Force download of the latest master file."""

        self.ensure_cache(force=True)

    def lookup(self, symbol: str, *, exchange: str | None = None) -> dict[str, Any] | None:
        """Return instrument mapping for the provided symbol."""

        if not symbol:
            return None
        symbol_key = symbol.strip().upper()
        exchange_key = (exchange or "").strip().upper()
        records = self._load_records()
        self._build_index(records)

        direct = self._index.get((symbol_key, exchange_key))
        if direct:
            return direct

        if exchange_key:
            alt = self._index.get((symbol_key, ""))
            if alt:
                return alt

        if "-" in symbol_key:
            base = symbol_key.split("-", 1)[0]
            alt = self._index.get((base, exchange_key)) or self._index.get((base, ""))
            if alt:
                return alt
        else:
            equity_key = f"{symbol_key}-EQ"
            alt = self._index.get((equity_key, exchange_key)) or self._index.get((equity_key, ""))
            if alt:
                return alt

        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_records(self) -> list[dict[str, Any]]:
        with self._lock:
            current_mtime = self._current_mtime()
            if self._records is not None and self._loaded_mtime == current_mtime:
                return self._records

            if self.auto_refresh:
                self.ensure_cache()
            elif not self.cache_path.exists():
                raise RuntimeError(
                    "Angel One scrip master cache not found. Run the update script or enable auto_refresh."
                )

            data = self.cache_path.read_text(encoding="utf-8")
            records = json.loads(data)
            if not isinstance(records, list):
                raise RuntimeError("Angel One scrip master JSON is malformed")
            self._records = [item for item in records if isinstance(item, Mapping)]
            self._index.clear()
            self._loaded_mtime = current_mtime
            return self._records

    def _build_index(self, records: Iterable[Mapping[str, Any]]) -> None:
        if self._index:
            return
        for record in records:
            tradingsymbol = self._extract_symbol(record)
            token = self._extract_token(record)
            exchange = self._extract_exchange(record)
            if not tradingsymbol or not token:
                continue
            payload: dict[str, Any] = {
                "tradingsymbol": tradingsymbol,
                "symbol_token": token,
                "exchange": exchange or "",
            }
            instrument_type = self._extract_field(record, ["instrumenttype", "instrument_type", "instrumentType"])
            if instrument_type:
                payload["instrument_type"] = instrument_type

            key = (tradingsymbol, exchange or "")
            self._index[key] = payload
            if "-" in tradingsymbol:
                base = tradingsymbol.split("-", 1)[0]
                self._index.setdefault((base, exchange or ""), payload)
            else:
                self._index.setdefault((f"{tradingsymbol}-EQ", exchange or ""), payload)
            self._index.setdefault((tradingsymbol, ""), payload)

    def _extract_symbol(self, record: Mapping[str, Any]) -> str:
        for key in ("tradingsymbol", "symbol", "symbolname", "name"):
            value = record.get(key)
            if value:
                symbol = str(value).strip().upper()
                if symbol:
                    return symbol
        return ""

    def _extract_token(self, record: Mapping[str, Any]) -> str:
        for key in ("symboltoken", "symbolToken", "token", "instrument_token"):
            value = record.get(key)
            if value is not None:
                token = str(value).strip()
                if token:
                    return token
        return ""

    def _extract_exchange(self, record: Mapping[str, Any]) -> str:
        for key in ("exch_seg", "exchange", "exchangeSegment", "segment"):
            value = record.get(key)
            if value:
                exchange = str(value).strip().upper()
                if exchange:
                    return exchange
        return ""

    @staticmethod
    def _extract_field(record: Mapping[str, Any], keys: Iterable[str]) -> str | None:
        for key in keys:
            value = record.get(key)
            if value:
                text = str(value).strip()
                if text:
                    return text
        return None

    def _is_stale(self, path: Path) -> bool:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return datetime.utcnow() - mtime > CACHE_MAX_AGE

    def _current_mtime(self) -> float | None:
        if not self.cache_path.exists():
            return None
        return self.cache_path.stat().st_mtime


_master_instance: AngelInstrumentMaster | None = None
_master_lock = threading.Lock()


def get_angel_instrument_master() -> AngelInstrumentMaster:
    global _master_instance
    if _master_instance is None:
        with _master_lock:
            if _master_instance is None:
                _master_instance = AngelInstrumentMaster()
    return _master_instance


__all__ = ["AngelInstrumentMaster", "get_angel_instrument_master", "CACHE_PATH", "MASTER_URL"]
