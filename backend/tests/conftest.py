from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker


@compiles(PGUUID, "sqlite")
def _compile_uuid(element, compiler, **kwargs) -> str:  # pragma: no cover - dialect shim
    return "CHAR(36)"


@pytest.fixture()
def session():
    """Provide an isolated in-memory database session for tests."""

    from app import models  # noqa: F401  Ensures all model metadata is registered.
    from app.models import Base

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    session = TestingSession()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
