import uuid

import pytest

from app.broker_adapters import BrokerAuthenticationError
from app.models.broker import Broker, BrokerStatus
from app.models.user import User
from app.schemas.broker import BrokerConnectRequest, BrokerStatusEnum
from app.services.brokers import BrokerService
from app.utils.crypto import decrypt_credentials


@pytest.fixture()
def user(session):
    user = User(
        name="Test User",
        email="test-user@example.com",
        password_hash="hashed",
    )
    session.add(user)
    session.commit()
    return user


def test_connect_persists_credentials(session, user):
    service = BrokerService(session)
    payload = BrokerConnectRequest(
        broker_name="paper_trading",
        client_code="demo",
        credentials={"api_key": "secret"},
    )

    broker_read = service.connect(user.id, payload)

    stored = session.get(Broker, broker_read.id)
    assert stored is not None
    assert stored.credentials_encrypted

    decrypted = decrypt_credentials(stored.credentials_encrypted)
    assert decrypted["api_key"] == "secret"
    assert decrypted["client_code"] == "demo"


def test_login_uses_stored_credentials(session, user):
    service = BrokerService(session)
    payload = BrokerConnectRequest(
        broker_name="paper_trading",
        client_code="demo",
        credentials={"api_key": "login"},
    )

    broker_read = service.connect(user.id, payload)
    service.logout(user.id, broker_read.id)

    reconnected = service.login(user.id, broker_read.id)
    assert reconnected.status == BrokerStatusEnum.connected

    stored = session.get(Broker, broker_read.id)
    assert stored is not None
    assert stored.status == BrokerStatus.connected
    assert stored.session_token is not None


def test_login_without_credentials_fails(session, user):
    broker = Broker(
        id=uuid.uuid4(),
        user_id=user.id,
        broker_name="paper_trading",
        client_code="demo",
        status=BrokerStatus.disconnected,
    )
    session.add(broker)
    session.commit()

    service = BrokerService(session)

    with pytest.raises(BrokerAuthenticationError):
        service.login(user.id, broker.id)


