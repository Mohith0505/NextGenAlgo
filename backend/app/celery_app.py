from __future__ import annotations

import os

from celery import Celery

from app.core.config import settings

broker_url = settings.celery_broker_url or settings.redis_url
backend_url = settings.celery_result_backend or settings.redis_url

celery_app = Celery(
    "nextgen_algo",
    broker=broker_url,
    backend=backend_url,
)

celery_app.conf.update(
    task_default_queue="strategy",
    task_acks_late=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(["app.tasks"])
