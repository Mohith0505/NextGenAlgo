from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_rms_service
from app.models.user import User
from app.schemas.rms import RmsConfigRead, RmsConfigUpdate, RmsSquareOffResponse, RmsStatusRead
from app.services.rms import RmsService

router = APIRouter(prefix="/rms", tags=["RMS"])


def _require_user(current_user: Optional[User]) -> User:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return current_user


@router.get("/config", response_model=RmsConfigRead)
def get_rms_config(
    rms_service: RmsService = Depends(get_rms_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> RmsConfigRead:
    user = _require_user(current_user)
    return rms_service.get_config(user.id)


@router.post("/config", response_model=RmsConfigRead)
def update_rms_config(
    payload: RmsConfigUpdate = Body(...),
    rms_service: RmsService = Depends(get_rms_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> RmsConfigRead:
    user = _require_user(current_user)
    return rms_service.update_config(user.id, payload)


@router.get("/status", response_model=RmsStatusRead)
def rms_status(
    rms_service: RmsService = Depends(get_rms_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> RmsStatusRead:
    user = _require_user(current_user)
    return rms_service.get_status(user.id)


@router.post("/squareoff", response_model=RmsSquareOffResponse)
def rms_square_off(
    rms_service: RmsService = Depends(get_rms_service),
    current_user: Optional[User] = Depends(get_current_user),
) -> RmsSquareOffResponse:
    user = _require_user(current_user)
    return rms_service.trigger_square_off(user.id)
