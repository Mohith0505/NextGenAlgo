from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_broker_service, get_current_user
from app.broker_adapters import BrokerAuthenticationError, list_supported_brokers
from app.models.user import User
from app.schemas.auth import Message
from app.schemas.broker import (
    BrokerConnectRequest,
    BrokerListResponse,
    BrokerRead,
    BrokerRefreshRequest,
)
from app.services.brokers import BrokerService

router = APIRouter(prefix="/brokers", tags=["Brokers"])


@router.get("/supported", response_model=list[str])
def supported_brokers() -> list[str]:
    return list_supported_brokers()


@router.post("/connect", response_model=BrokerRead, status_code=status.HTTP_201_CREATED)
def connect_broker(
    payload: BrokerConnectRequest,
    broker_service: BrokerService = Depends(get_broker_service),
    current_user: User | None = Depends(get_current_user),
) -> BrokerRead:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return broker_service.connect(current_user.id, payload)
    except BrokerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=BrokerListResponse)
def list_connected_brokers(
    broker_service: BrokerService = Depends(get_broker_service),
    current_user: User | None = Depends(get_current_user),
) -> BrokerListResponse:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    brokers = broker_service.list_brokers(current_user.id)
    return BrokerListResponse(brokers=brokers)


@router.post("/{broker_id}/refresh", response_model=BrokerRead)
def refresh_broker_session(
    broker_id: UUID,
    payload: BrokerRefreshRequest,
    broker_service: BrokerService = Depends(get_broker_service),
    current_user: User | None = Depends(get_current_user),
) -> BrokerRead:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return broker_service.refresh(current_user.id, broker_id, payload)
    except BrokerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{broker_id}/logout", response_model=BrokerRead)
def logout_broker(
    broker_id: UUID,
    broker_service: BrokerService = Depends(get_broker_service),
    current_user: User | None = Depends(get_current_user),
) -> BrokerRead:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    broker = broker_service.logout(current_user.id, broker_id)
    if broker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Broker not found")
    return broker

@router.delete("/{broker_id}", response_model=Message, status_code=status.HTTP_200_OK)
def delete_broker(
    broker_id: UUID,
    broker_service: BrokerService = Depends(get_broker_service),
    current_user: User | None = Depends(get_current_user),
) -> Message:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    deleted = broker_service.delete_broker(current_user.id, broker_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Broker not found")
    return Message(detail="Broker removed")
