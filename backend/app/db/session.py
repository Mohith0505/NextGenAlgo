from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    future=True,
    echo=settings.sqlalchemy_echo,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
