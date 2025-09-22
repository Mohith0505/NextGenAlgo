from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.api.dependencies import (
    get_current_user,
    get_scheduler_service,
    get_strategy_dispatcher,
)
from app.models.user import User
from app.schemas.scheduler import ScheduledJobCreate, ScheduledJobRead
from app.services.scheduler import StrategySchedulerService
from app.services.strategy_dispatcher import StrategyDispatcher

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


def _require_user(current_user: Optional[User]) -> User:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return current_user


@router.get("/jobs", response_model=list[ScheduledJobRead])
def list_jobs(
    strategy_id: Optional[UUID] = None,
    current_user: Optional[User] = Depends(get_current_user),
    scheduler: StrategySchedulerService = Depends(get_scheduler_service),
) -> list[ScheduledJobRead]:
    user = _require_user(current_user)
    jobs = scheduler.list_jobs(user.id, strategy_id)
    return [ScheduledJobRead.model_validate(job) for job in jobs]


@router.post("/jobs", response_model=ScheduledJobRead, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: ScheduledJobCreate,
    current_user: Optional[User] = Depends(get_current_user),
    scheduler: StrategySchedulerService = Depends(get_scheduler_service),
) -> ScheduledJobRead:
    user = _require_user(current_user)
    job = scheduler.create_job(user.id, payload)
    return ScheduledJobRead.model_validate(job)


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: UUID,
    current_user: Optional[User] = Depends(get_current_user),
    scheduler: StrategySchedulerService = Depends(get_scheduler_service),
) -> Response:
    user = _require_user(current_user)
    success = scheduler.delete_job(user.id, job_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/jobs/{job_id}/trigger", status_code=status.HTTP_202_ACCEPTED)
def trigger_job(
    job_id: UUID,
    current_user: Optional[User] = Depends(get_current_user),
    scheduler: StrategySchedulerService = Depends(get_scheduler_service),
    dispatcher: StrategyDispatcher = Depends(get_strategy_dispatcher),
) -> dict[str, str]:
    user = _require_user(current_user)
    try:
        job = scheduler.trigger_job(user.id, job_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    dispatcher.dispatch(
        user_id=user.id,
        strategy_id=job.strategy_id,
        context=job.context or {},
    )

    return {"status": "queued", "job_id": str(job.id)}
