from collections.abc import Generator
from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.account_registry import AccountRegistryService
from app.services.analytics import AnalyticsService
from app.services.brokers import BrokerService
from app.services.rms import RmsService
from app.services.scheduler import StrategySchedulerService
from app.services.strategy_dispatcher import StrategyDispatcher
from app.services.strategies import StrategyService
from app.services.users import UserService


def get_user_service(session: Session = Depends(get_db)) -> Generator[UserService, None, None]:
    yield UserService(session)


def get_broker_service(session: Session = Depends(get_db)) -> Generator[BrokerService, None, None]:
    yield BrokerService(session)


def get_strategy_service(session: Session = Depends(get_db)) -> Generator[StrategyService, None, None]:
    yield StrategyService(session)


def get_rms_service(session: Session = Depends(get_db)) -> Generator[RmsService, None, None]:
    yield RmsService(session)


def get_analytics_service(session: Session = Depends(get_db)) -> Generator[AnalyticsService, None, None]:
    yield AnalyticsService(session)




def get_strategy_dispatcher(session: Session = Depends(get_db)) -> StrategyDispatcher:
    return StrategyDispatcher(session)

def get_scheduler_service(session: Session = Depends(get_db)) -> Generator[StrategySchedulerService, None, None]:
    yield StrategySchedulerService(session)

def get_account_registry_service(session: Session = Depends(get_db)) -> Generator[AccountRegistryService, None, None]:
    yield AccountRegistryService(session)


def get_current_user(user_service: UserService = Depends(get_user_service)) -> Optional[User]:
    return user_service.get_first_user()
