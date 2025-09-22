from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.scheduler_job import SchedulerJob
from app.schemas.scheduler import ScheduledJobCreate
from app.tasks.strategy import trigger_strategy_run

ALLOWED_SPECIAL_CRON = {"@once", "@hourly", "@daily", "@weekly", "@monthly"}


def _now() -> datetime:
    return datetime.utcnow()


class StrategySchedulerService:
    """Database-backed scheduler service for strategy jobs."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def list_jobs(self, user_id: uuid.UUID, strategy_id: uuid.UUID | None = None) -> list[SchedulerJob]:
        stmt = select(SchedulerJob).where(SchedulerJob.user_id == user_id)
        if strategy_id is not None:
            stmt = stmt.where(SchedulerJob.strategy_id == strategy_id)
        return self.session.execute(stmt).scalars().all()

    def create_job(self, user_id: uuid.UUID, payload: ScheduledJobCreate) -> SchedulerJob:
        self._validate_cron(payload.cron_expression)
        job = SchedulerJob(
            user_id=user_id,
            strategy_id=payload.strategy_id,
            name=payload.name,
            cron_expression=payload.cron_expression,
            is_active=payload.is_active,
            context=payload.context,
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def delete_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> bool:
        job = self.session.get(SchedulerJob, job_id)
        if job is None or job.user_id != user_id:
            return False
        self.session.delete(job)
        self.session.commit()
        return True

    def trigger_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> SchedulerJob:
        job = self.session.get(SchedulerJob, job_id)
        if job is None or job.user_id != user_id:
            raise KeyError("Job not found")
        job.last_triggered_at = _now()
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)

        trigger_strategy_run.delay(
            user_id=str(job.user_id),
            strategy_id=str(job.strategy_id) if job.strategy_id else None,
            context=job.context or {},
        )
        return job

    def enqueue_webhook_job(
        self,
        *,
        user_id: uuid.UUID,
        provider: str,
        strategy_id: uuid.UUID | None,
        context: dict[str, Any] | None = None,
    ) -> SchedulerJob:
        job_data = ScheduledJobCreate(
            name=f"Webhook dispatch ({provider})",
            cron_expression='@once',
            strategy_id=strategy_id,
            is_active=False,
            context=context,
        )
        job = self.create_job(user_id, job_data)
        return self.trigger_job(user_id, job.id)

    @staticmethod
    def _validate_cron(cron_expression: str) -> None:
        if cron_expression.startswith("@"):
            if cron_expression in ALLOWED_SPECIAL_CRON:
                return
            raise ValueError(f"Unsupported cron shortcut: {cron_expression}")
        parts = cron_expression.split()
        if len(parts) != 5:
            raise ValueError("Cron expression must contain 5 fields (minute hour day month weekday)")
        for part in parts:
            if part == "*":
                continue
            if part.isdigit():
                continue
            if any(token in part for token in {"/", "-", ","}):
                continue
            raise ValueError(f"Unsupported cron token: {part}")


__all__ = ["StrategySchedulerService"]
