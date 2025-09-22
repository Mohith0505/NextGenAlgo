from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import (
    Account,
    Broker,
    BrokerStatus,
    LogEntry,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    RmsRule,
    Trade,
    User,
)
from app.services.rms import RmsService
from app.utils.dt import utcnow


@pytest.fixture()
def user(session):
    test_user = User(
        id=uuid4(),
        name="RMS Tester",
        email="rms.tester@example.com",
        password_hash="hashed",
    )
    session.add(test_user)
    session.commit()
    return test_user


def _seed_core_entities(session, user):
    broker = Broker(
        user_id=user.id,
        broker_name="MockBroker",
        client_code="ABC123",
        status=BrokerStatus.connected,
    )
    session.add(broker)
    session.flush()

    account = Account(broker_id=broker.id, margin=100_000)
    session.add(account)
    session.flush()

    order = Order(
        account_id=account.id,
        symbol="NIFTY24SEP",
        side=OrderSide.buy,
        qty=50,
        price=1000,
        order_type=OrderType.market,
        status=OrderStatus.filled,
    )
    session.add(order)
    session.flush()

    trade = Trade(
        order_id=order.id,
        fill_price=995,
        qty=50,
        pnl=-940,
        timestamp=utcnow(),
    )
    session.add(trade)

    position = Position(
        account_id=account.id,
        symbol="NIFTY24SEP",
        qty=50,
        avg_price=1000,
        pnl=-20,
        updated_at=utcnow(),
    )
    session.add(position)

    session.commit()
    return account


def test_rms_status_reports_automation_cues(session, user):
    account = _seed_core_entities(session, user)

    rule = RmsRule(
        user_id=user.id,
        max_daily_loss=1000,
        auto_square_off_enabled=True,
        auto_square_off_buffer_pct=5,
        auto_hedge_enabled=True,
        auto_hedge_ratio=0.5,
        exposure_limit=50_000,
        notify_email=True,
    )
    session.add(rule)
    session.commit()

    service = RmsService(session)
    status = service.get_status(user.id)

    assert status.automations, "Expected automation cues to be surfaced in RMS status"
    assert any("Auto square-off" in entry for entry in status.automations)
    assert any("Auto hedge" in entry for entry in status.automations)


def test_auto_enforce_triggers_actions_and_notifications(session, user):
    account = _seed_core_entities(session, user)

    rule = RmsRule(
        user_id=user.id,
        max_daily_loss=1000,
        auto_square_off_enabled=True,
        auto_square_off_buffer_pct=5,
        auto_hedge_enabled=True,
        auto_hedge_ratio=0.5,
        exposure_limit=50_000,
        notify_email=True,
        notify_telegram=True,
    )
    session.add(rule)
    session.commit()

    service = RmsService(session)

    actions = service.auto_enforce(user.id)

    assert any("Auto square-off" in action for action in actions)
    assert any("Auto hedge" in action for action in actions)

    logs = session.execute(select(LogEntry).where(LogEntry.user_id == user.id)).scalars().all()
    messages = [log.message for log in logs]
    assert any("Automated RMS square-off" in message for message in messages)
    assert any("Auto hedge queued" in message for message in messages)
    assert any("Notification queued via email" in message for message in messages)
    assert any("Notification queued via telegram" in message for message in messages)
