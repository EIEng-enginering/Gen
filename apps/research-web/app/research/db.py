"""Database session boundary. Production: local private PostgreSQL; tests: SQLite."""
import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def database_url():
    explicit = os.getenv('GEN_DB_URL')
    if explicit:
        return explicit
    user = quote_plus(os.getenv('GEN_DB_USER','gen24'))
    password = quote_plus(os.getenv('GEN_DB_PASSWORD',''))
    host = os.getenv('GEN_DB_HOST','research_db')
    db = os.getenv('GEN_DB_NAME','gen24')
    port = int(os.getenv('GEN_DB_PORT','5432'))
    return f'postgresql+psycopg://{user}:{password}@{host}:{port}/{db}'


_engine = None


def engine():
    global _engine
    if _engine is None:
        _engine = create_engine(database_url(), pool_pre_ping=True, future=True)
    return _engine


def session():
    with sessionmaker(bind=engine(), expire_on_commit=False)() as db:
        yield db


def close_engine():
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None
