
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import Response

from app.api.dependencies import get_current_user, get_scheduler_service
from app.models.user import User
from app.schemas.webhook import WebhookConnectorCreate, WebhookConnectorRead, WebhookEventIn
from app.services.scheduler import StrategySchedulerService
from app.services.webhook import webhook_service

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _require_user(current_user: Optional[User]) -> User:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return current_user


@router.get("/connectors", response_model=list[WebhookConnectorRead])
def list_connectors(current_user: Optional[User] = Depends(get_current_user)) -> list[WebhookConnectorRead]:
    user = _require_user(current_user)
    return webhook_service.list_connectors(user.id)


@router.post("/connectors", response_model=WebhookConnectorRead, status_code=status.HTTP_201_CREATED)
def create_connector(
    payload: WebhookConnectorCreate,
    current_user: Optional[User] = Depends(get_current_user),
) -> WebhookConnectorRead:
    user = _require_user(current_user)
    return webhook_service.create_connector(user.id, payload)


@router.delete("/connectors/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connector(
    connector_id: UUID,
    current_user: Optional[User] = Depends(get_current_user),
) -> Response:
    user = _require_user(current_user)
    success = webhook_service.delete_connector(user.id, connector_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/connectors/{connector_id}/events", status_code=status.HTTP_202_ACCEPTED)
def ingest_event(
    connector_id: UUID,
    event: WebhookEventIn,
    background_tasks: BackgroundTasks,
    scheduler: StrategySchedulerService = Depends(get_scheduler_service),
) -> dict[str, str]:
    try:
        connector = webhook_service.dispatch_event(connector_id, event, background_tasks)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid webhook signature")

    raw_strategy_id = event.payload.get("strategy_id")
    strategy_uuid: UUID | None = None
    if isinstance(raw_strategy_id, str):
        try:
            strategy_uuid = UUID(raw_strategy_id)
        except ValueError:
            strategy_uuid = None

    scheduled_job = scheduler.enqueue_webhook_job(
        user_id=connector.user_id,
        provider=connector.provider.value,
        strategy_id=strategy_uuid,
        context=event.payload,
    )

    return {"status": "accepted", "job_id": str(scheduled_job.id)}
