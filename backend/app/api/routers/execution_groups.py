from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.broker_adapters import BrokerAuthenticationError, BrokerError
from app.api.dependencies import get_account_registry_service, get_broker_service, get_current_user
from app.models.user import User
from app.schemas.account_registry import (
    ExecutionAllocationPreview,
    ExecutionGroupAccountCreate,
    ExecutionGroupAccountRead,
    ExecutionGroupAccountUpdate,
    ExecutionGroupCreate,
    ExecutionGroupRead,
    ExecutionGroupUpdate,
    ExecutionRunRead,
    ExecutionRunEventRead,
)
from app.schemas.order import ExecutionGroupOrderCreate, ExecutionGroupOrderResponse
from app.services.account_registry import AccountRegistryService
from app.services.brokers import BrokerService
from app.services.rms import RmsViolationError

router = APIRouter(prefix="/execution-groups", tags=["Execution Groups"])


def _require_user(current_user: User | None) -> User:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return current_user


@router.get("", response_model=list[ExecutionGroupRead])
def list_groups(
    registry: AccountRegistryService = Depends(get_account_registry_service),
    current_user: User | None = Depends(get_current_user),
) -> list[ExecutionGroupRead]:
    user = _require_user(current_user)
    return registry.list_groups(user.id)


@router.post("", response_model=ExecutionGroupRead, status_code=status.HTTP_201_CREATED)
def create_group(
    payload: ExecutionGroupCreate,
    registry: AccountRegistryService = Depends(get_account_registry_service),
    current_user: User | None = Depends(get_current_user),
) -> ExecutionGroupRead:
    user = _require_user(current_user)
    return registry.create_group(user.id, payload)


@router.patch("/{group_id}", response_model=ExecutionGroupRead)
def update_group(
    group_id: UUID,
    payload: ExecutionGroupUpdate,
    registry: AccountRegistryService = Depends(get_account_registry_service),
    current_user: User | None = Depends(get_current_user),
) -> ExecutionGroupRead:
    user = _require_user(current_user)
    try:
        return registry.update_group(user.id, group_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: UUID,
    registry: AccountRegistryService = Depends(get_account_registry_service),
    current_user: User | None = Depends(get_current_user),
) -> None:
    user = _require_user(current_user)
    try:
        registry.delete_group(user.id, group_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{group_id}/accounts", response_model=ExecutionGroupAccountRead, status_code=status.HTTP_201_CREATED)
def add_account(
    group_id: UUID,
    payload: ExecutionGroupAccountCreate,
    registry: AccountRegistryService = Depends(get_account_registry_service),
    current_user: User | None = Depends(get_current_user),
) -> ExecutionGroupAccountRead:
    user = _require_user(current_user)
    try:
        return registry.add_account(user.id, group_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/{group_id}/accounts/{mapping_id}", response_model=ExecutionGroupAccountRead)
def update_account(
    group_id: UUID,
    mapping_id: UUID,
    payload: ExecutionGroupAccountUpdate,
    registry: AccountRegistryService = Depends(get_account_registry_service),
    current_user: User | None = Depends(get_current_user),
) -> ExecutionGroupAccountRead:
    user = _require_user(current_user)
    try:
        return registry.update_account(user.id, group_id, mapping_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{group_id}/accounts/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_account(
    group_id: UUID,
    mapping_id: UUID,
    registry: AccountRegistryService = Depends(get_account_registry_service),
    current_user: User | None = Depends(get_current_user),
) -> None:
    user = _require_user(current_user)
    try:
        registry.remove_account(user.id, group_id, mapping_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc




@router.get("/{group_id}/runs", response_model=list[ExecutionRunRead])

def list_runs(
    group_id: UUID,
    registry: AccountRegistryService = Depends(get_account_registry_service),
    current_user: User | None = Depends(get_current_user),
) -> list[ExecutionRunRead]:
    user = _require_user(current_user)
    try:
        return registry.get_group_runs(user.id, group_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{group_id}/runs/{run_id}/events", response_model=list[ExecutionRunEventRead])

def list_run_events(
    group_id: UUID,
    run_id: UUID,
    registry: AccountRegistryService = Depends(get_account_registry_service),
    current_user: User | None = Depends(get_current_user),
) -> list[ExecutionRunEventRead]:
    user = _require_user(current_user)
    try:
        return registry.get_run_events(user.id, group_id, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{group_id}/preview", response_model=list[ExecutionAllocationPreview])
def preview_allocation(
    group_id: UUID,
    lots: int = Query(..., gt=0, description="Total lots to allocate across the group"),
    registry: AccountRegistryService = Depends(get_account_registry_service),
    current_user: User | None = Depends(get_current_user),
) -> list[ExecutionAllocationPreview]:
    user = _require_user(current_user)
    try:
        return registry.preview_allocation(user.id, group_id, lots)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{group_id}/orders", response_model=ExecutionGroupOrderResponse, status_code=status.HTTP_201_CREATED)
def place_group_order(
    group_id: UUID,
    payload: ExecutionGroupOrderCreate,
    broker_service: BrokerService = Depends(get_broker_service),
    current_user: User | None = Depends(get_current_user),
) -> ExecutionGroupOrderResponse:
    user = _require_user(current_user)
    try:
        return broker_service.place_execution_group_order(user.id, group_id, payload)
    except RmsViolationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    except BrokerAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except BrokerError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
