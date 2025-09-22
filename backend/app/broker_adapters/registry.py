from __future__ import annotations

from typing import Type

from .angel import AngelAdapter
from .base import BaseBrokerAdapter
from .dhan import DhanAdapter
from .fyers import FyersAdapter
from .paper import PaperTradingAdapter
from .zerodha import ZerodhaAdapter

_REGISTERED_ADAPTERS: tuple[Type[BaseBrokerAdapter], ...] = (
    AngelAdapter,
    ZerodhaAdapter,
    FyersAdapter,
    DhanAdapter,
    PaperTradingAdapter,
)

_ADAPTER_BY_KEY: dict[str, Type[BaseBrokerAdapter]] = {}
for adapter_cls in _REGISTERED_ADAPTERS:
    keys = {adapter_cls.broker_name}
    keys.update(getattr(adapter_cls, "aliases", set()))
    for raw_key in keys:
        normalized = raw_key.strip().lower().replace(" ", "_")
        _ADAPTER_BY_KEY[normalized] = adapter_cls


def normalize_broker_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def get_adapter_class(name: str) -> Type[BaseBrokerAdapter]:
    key = normalize_broker_name(name)
    try:
        return _ADAPTER_BY_KEY[key]
    except KeyError as exc:
        raise KeyError(f"Broker adapter '{name}' is not registered") from exc


def get_adapter(name: str, **kwargs) -> BaseBrokerAdapter:
    adapter_cls = get_adapter_class(name)
    return adapter_cls(**kwargs)


def list_supported_brokers() -> list[str]:
    return sorted({cls.broker_name for cls in _REGISTERED_ADAPTERS})


__all__ = [
    "get_adapter",
    "get_adapter_class",
    "list_supported_brokers",
    "normalize_broker_name",
]
