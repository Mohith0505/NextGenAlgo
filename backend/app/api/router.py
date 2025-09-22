from fastapi import APIRouter

from app.api.routers import (
    analytics,
    auth,
    brokers,
    execution_groups,
    orders,
    risk,
    strategies,
    users,
    webhooks,
    scheduler,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(brokers.router)
api_router.include_router(execution_groups.router)
api_router.include_router(orders.router)
api_router.include_router(strategies.router)
api_router.include_router(risk.router)
api_router.include_router(analytics.router)
api_router.include_router(webhooks.router)
api_router.include_router(scheduler.router)
