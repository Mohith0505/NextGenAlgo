from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BrokerStatusEnum(str, Enum):
    connected = "connected"
    expired = "expired"
    error = "error"


class BrokerConnectRequest(BaseModel):
    broker_name: str = Field(..., description="Canonical broker identifier, e.g. zerodha")
    client_code: str = Field(..., description="Broker client code or login id")
    credentials: dict[str, Any] = Field(default_factory=dict, description="Adapter specific credentials")


class BrokerRefreshRequest(BaseModel):
    credentials: dict[str, Any] = Field(default_factory=dict)


class BrokerAccountRead(BaseModel):
    id: UUID
    margin: float
    currency: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BrokerRead(BaseModel):
    id: UUID
    broker_name: str
    client_code: str
    status: BrokerStatusEnum
    created_at: datetime
    accounts: list[BrokerAccountRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class BrokerListResponse(BaseModel):
    brokers: list[BrokerRead]
