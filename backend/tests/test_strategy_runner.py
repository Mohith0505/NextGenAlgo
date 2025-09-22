from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from app.broker_adapters import get_adapter
from app.models.account import Account
from app.models.broker import Broker, BrokerStatus
from app.models.execution_group import ExecutionGroup
from app.models.execution_group_account import ExecutionGroupAccount, LotAllocationPolicy
from app.models.execution_run import ExecutionRun
from app.models.strategy import Strategy, StrategyStatus, StrategyType
from app.models.strategy_run import StrategyMode, StrategyRun, StrategyRunStatus
from app.models.user import User, UserRole, UserStatus
from app.schemas.strategy import StrategyModeEnum
from app.services.strategy_runner import StrategyRunner


def _create_user(session) -> User:
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash="hashed-password",
        role=UserRole.owner,
        status=UserStatus.active,
    )
    session.add(user)
    session.flush()
    return user


def _create_paper_broker_setup(session, user: User) -> tuple[Broker, Account, ExecutionGroup]:
    paper_adapter = get_adapter("paper_trading")
    session_token = paper_adapter.connect({"client_code": "paper-demo"}).token

    broker = Broker(
        user_id=user.id,
        broker_name="paper_trading",
        client_code="paper-demo",
        session_token=session_token,
        status=BrokerStatus.connected,
    )
    session.add(broker)
    session.flush()

    account = Account(broker_id=broker.id, margin=1_000_000, currency="INR")
    session.add(account)
    session.flush()

    group = ExecutionGroup(user_id=user.id, name="Primary Group")
    session.add(group)
    session.flush()

    mapping = ExecutionGroupAccount(
        group_id=group.id,
        account_id=account.id,
        allocation_policy=LotAllocationPolicy.proportional,
        weight=1.0,
    )
    session.add(mapping)
    session.flush()

    return broker, account, group


def _create_strategy(session, user: User, params: dict) -> Strategy:
    strategy = Strategy(
        user_id=user.id,
        name="Strategy Alpha",
        type=StrategyType.built_in,
        status=StrategyStatus.active,
        params=params,
    )
    session.add(strategy)
    session.flush()
    return strategy


def _create_run(session, strategy: Strategy, mode: StrategyMode, parameters: dict) -> StrategyRun:
    run = StrategyRun(
        strategy_id=strategy.id,
        mode=mode,
        status=StrategyRunStatus.running,
        parameters=parameters,
        started_at=datetime.utcnow(),
    )
    session.add(run)
    session.flush()
    return run


def test_strategy_runner_paper_execution_creates_execution_run(session):
    user = _create_user(session)
    _, account, group = _create_paper_broker_setup(session, user)

    configuration = {
        "symbol": "NIFTY23SEP",
        "side": "BUY",
        "lots": 2,
        "lot_size": 25,
        "price": 100.5,
        "execution_group_id": str(group.id),
    }

    strategy = _create_strategy(session, user, params=configuration)
    run = _create_run(session, strategy, StrategyMode.paper, configuration)
    session.commit()

    runner = StrategyRunner(session)
    result = runner.run(
        strategy=strategy,
        run=run,
        user_id=user.id,
        mode=StrategyModeEnum.paper,
        configuration=configuration,
        extras={},
    )

    assert result.metrics["orders"] == 1
    assert result.metrics["trades"] == 1
    assert result.metrics["execution_run_id"]
    assert result.logs, "Expected strategy runner to emit log entries"

    execution_run_id = uuid.UUID(result.metrics["execution_run_id"])
    execution_run = session.get(ExecutionRun, execution_run_id)
    assert execution_run is not None
    assert execution_run.strategy_run_id == run.id
    assert execution_run.group_id == group.id
    assert execution_run.status == "completed"

    leg_status_counts = result.metrics.get("leg_status_counts", {})
    assert leg_status_counts, "Expected leg status counts to be recorded"
    assert sum(leg_status_counts.values()) >= 1


def test_strategy_runner_backtest_simulation_computes_metrics(session):
    user = _create_user(session)
    base_configuration = {
        "symbol": "BANKNIFTY",
        "side": "SELL",
        "lots": 1,
        "lot_size": 15,
        "entry_price": 450.0,
        "exit_price": 440.0,
    }

    strategy = _create_strategy(session, user, params=base_configuration)
    run = _create_run(session, strategy, StrategyMode.backtest, base_configuration)
    session.commit()

    runner = StrategyRunner(session)
    result = runner.run(
        strategy=strategy,
        run=run,
        user_id=user.id,
        mode=StrategyModeEnum.backtest,
        configuration=dict(base_configuration),
        extras={},
    )

    assert pytest.approx(result.metrics["pnl"], rel=1e-6) == 150.0  # (450-440)*15 for SELL
    assert result.metrics["orders"] == 1
    assert result.metrics["trades"] == 1
    assert result.logs, "Expected backtest to emit log entries"
