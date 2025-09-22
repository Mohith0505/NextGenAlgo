from __future__ import annotations

import enum
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class WebhookProvider(str, enum.Enum):
    tradingview = "tradingview"
    generic_http = "http"


class WebhookConnectorBase(BaseModel):
    name: str = Field(..., max_length=120)
    provider: WebhookProvider
    target_url: HttpUrl = Field(..., description="Internal callback URL that will receive webhook payloads")
    secret: str | None = Field(default=None, description="Shared secret or token for signature validation")
    config: dict[str, Any] | None = Field(default=None, description="Provider-specific configuration")
    is_active: bool = Field(default=True)


class WebhookConnectorCreate(WebhookConnectorBase):
    pass


class WebhookConnectorRead(WebhookConnectorBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookEventIn(BaseModel):
    connector_id: UUID
    payload: dict[str, Any]
    signature: str | None = None
    headers: dict[str, str] | None = None
    received_at: datetime | None = None

