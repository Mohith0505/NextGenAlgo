from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.api.dependencies import get_broker_service, get_current_user
from app.broker_adapters import BrokerAuthenticationError
from app.models.user import User
from app.schemas.order import OrderCreate, OrderListResponse, OrderRead
from app.services.brokers import BrokerService
from app.services.rms import RmsViolationError

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def place_order(
    payload: OrderCreate,
    broker_service: BrokerService = Depends(get_broker_service),
    current_user: User | None = Depends(get_current_user),
) -> OrderRead:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return broker_service.place_order(current_user.id, payload)
    except RmsViolationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    except BrokerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("", response_model=OrderListResponse)
def list_orders(
    broker_service: BrokerService = Depends(get_broker_service),
    current_user: User | None = Depends(get_current_user),
) -> OrderListResponse:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    orders = broker_service.list_orders(current_user.id)
    return OrderListResponse(orders=orders)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: UUID,
    broker_service: BrokerService = Depends(get_broker_service),
    current_user: User | None = Depends(get_current_user),
) -> OrderRead:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    order = broker_service.get_order(current_user.id, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.delete("/{order_id}", response_model=OrderRead)
def cancel_order(
    order_id: UUID,
    broker_service: BrokerService = Depends(get_broker_service),
    current_user: User | None = Depends(get_current_user),
) -> OrderRead:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    cancelled = broker_service.cancel_order(current_user.id, order_id)
    if cancelled is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return cancelled
