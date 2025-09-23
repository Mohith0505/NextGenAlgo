from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_broker_service, get_current_user
from app.broker_adapters import BrokerAuthenticationError, BrokerError
from app.models.user import User
from app.schemas.portfolio import (
    HoldingsResponse,
    PositionConvertRequest,
    PositionConvertResponse,
    PositionsResponse,
)
from app.services.brokers import BrokerService

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/{broker_id}/positions", response_model=PositionsResponse)
def get_positions(
    broker_id: UUID,
    broker_service: BrokerService = Depends(get_broker_service),
    current_user: User | None = Depends(get_current_user),
) -> PositionsResponse:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return broker_service.get_positions(current_user.id, broker_id)
    except BrokerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BrokerError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/{broker_id}/holdings", response_model=HoldingsResponse)
def get_holdings(
    broker_id: UUID,
    broker_service: BrokerService = Depends(get_broker_service),
    current_user: User | None = Depends(get_current_user),
) -> HoldingsResponse:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return broker_service.get_holdings(current_user.id, broker_id)
    except BrokerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BrokerError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/{broker_id}/positions/convert", response_model=PositionConvertResponse)
def convert_position(
    broker_id: UUID,
    payload: PositionConvertRequest,
    broker_service: BrokerService = Depends(get_broker_service),
    current_user: User | None = Depends(get_current_user),
) -> PositionConvertResponse:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return broker_service.convert_position(current_user.id, broker_id, payload)
    except BrokerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BrokerError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
