from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.api.dependencies import get_current_user, get_strategy_service
from app.models.user import User
from app.schemas.auth import Message
from app.schemas.strategy import (
    StrategyCreate,
    StrategyListResponse,
    StrategyLogListResponse,
    StrategyPerformanceResponse,
    StrategyRead,
    StrategyRunRead,
    StrategyStartRequest,
    StrategyStopRequest,
    StrategyUpdate,
)
from app.services.strategies import StrategyService

router = APIRouter(prefix="/strategies", tags=["Strategies"])


def _require_user(current_user: Optional[User]) -> User:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return current_user


@router.post("", response_model=StrategyRead, status_code=status.HTTP_201_CREATED)
def create_strategy(
    payload: StrategyCreate,
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> StrategyRead:
    user = _require_user(current_user)
    return strategy_service.create_strategy(user.id, payload)


@router.get("", response_model=StrategyListResponse)
def list_strategies(
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> StrategyListResponse:
    user = _require_user(current_user)
    return strategy_service.list_strategies(user.id)


@router.get("/{strategy_id}", response_model=StrategyRead)
def get_strategy(
    strategy_id: UUID,
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> StrategyRead:
    user = _require_user(current_user)
    try:
        return strategy_service.get_strategy(user.id, strategy_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{strategy_id}", response_model=StrategyRead)
def update_strategy(
    strategy_id: UUID,
    payload: StrategyUpdate,
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> StrategyRead:
    user = _require_user(current_user)
    try:
        return strategy_service.update_strategy(user.id, strategy_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{strategy_id}", response_model=Message)
def delete_strategy(
    strategy_id: UUID,
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> Message:
    user = _require_user(current_user)
    try:
        strategy_service.delete_strategy(user.id, strategy_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Message(detail="Strategy removed")


@router.post("/{strategy_id}/start", response_model=StrategyRunRead)
def start_strategy(
    strategy_id: UUID,
    payload: StrategyStartRequest,
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> StrategyRunRead:
    user = _require_user(current_user)
    try:
        return strategy_service.start_strategy(user.id, strategy_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{strategy_id}/stop", response_model=StrategyRunRead)
def stop_strategy(
    strategy_id: UUID,
    payload: StrategyStopRequest | None = Body(default=None),
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> StrategyRunRead:
    user = _require_user(current_user)
    try:
        return strategy_service.stop_strategy(user.id, strategy_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{strategy_id}/logs", response_model=StrategyLogListResponse)
def strategy_logs(
    strategy_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> StrategyLogListResponse:
    user = _require_user(current_user)
    return strategy_service.get_logs(user.id, strategy_id, limit=limit)


@router.get("/{strategy_id}/pnl", response_model=StrategyPerformanceResponse)
def strategy_performance(
    strategy_id: UUID,
    strategy_service: StrategyService = Depends(get_strategy_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> StrategyPerformanceResponse:
    user = _require_user(current_user)
    return strategy_service.get_performance(user.id, strategy_id)
