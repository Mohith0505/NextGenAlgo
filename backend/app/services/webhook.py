from __future__ import annotations

import hmac
import uuid
from datetime import datetime
from typing import Any

from fastapi import BackgroundTasks
from loguru import logger


from app.schemas.webhook import (
    WebhookConnectorCreate,
    WebhookConnectorRead,
    WebhookEventIn,
    WebhookProvider,
)


class WebhookService:
    """In-memory prototype for managing webhook connectors and events."""

    def __init__(self) -> None:
        self._connectors: dict[uuid.UUID, WebhookConnectorRead] = {}

    def list_connectors(self, user_id: uuid.UUID) -> list[WebhookConnectorRead]:
        return [connector for connector in self._connectors.values() if connector.user_id == user_id]

    def create_connector(self, user_id: uuid.UUID, payload: WebhookConnectorCreate) -> WebhookConnectorRead:
        connector_id = uuid.uuid4()
        connector = WebhookConnectorRead(
            id=connector_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            **payload.model_dump(),
        )
        self._connectors[connector_id] = connector
        return connector

    def delete_connector(self, user_id: uuid.UUID, connector_id: uuid.UUID) -> bool:
        connector = self._connectors.get(connector_id)
        if connector is None or connector.user_id != user_id:
            return False
        del self._connectors[connector_id]
        return True

    def dispatch_event(
        self,
        connector_id: uuid.UUID,
        event: WebhookEventIn,
        background_tasks: BackgroundTasks,
    ) -> None:
        connector = self._connectors.get(connector_id)
        if connector is None or not connector.is_active:
            raise KeyError("Connector not found")
        if not self._validate_event(connector, event):
            raise PermissionError("Webhook signature validation failed")

        background_tasks.add_task(self._handle_event, connector, event)
        return connector

    def _validate_event(self, connector: WebhookConnectorRead, event: WebhookEventIn) -> bool:
        if connector.secret is None:
            return True
        candidate = event.signature or (event.headers or {}).get("X-Webhook-Signature")
        if candidate is None:
            return False
        payload_bytes = str(event.payload).encode("utf-8")
        secret_bytes = connector.secret.encode("utf-8")
        expected = hmac.new(secret_bytes, payload_bytes, "sha256").hexdigest()
        return hmac.compare_digest(expected, candidate)

    @staticmethod
    def _handle_event(connector: WebhookConnectorRead, event: WebhookEventIn) -> None:
        logger.info(
            "Webhook accepted",
            connector_id=str(connector.id),
            provider=connector.provider,
            received_at=event.received_at or datetime.utcnow(),
        )
        logger.bind(connector_id=str(connector.id)).info(
            "[stub] schedule strategy run for provider=%s payload=%s", connector.provider, event.payload
        )


webhook_service = WebhookService()
