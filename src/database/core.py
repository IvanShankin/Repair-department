from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.service.config.core import get_config


Base_sqlalchemy = declarative_base()
_SessionLocal: Any = None


class Base(Base_sqlalchemy):
    __abstract__ = True

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


def init_db():
    global _SessionLocal
    conf = get_config()

    # СЃРѕР·РґР°С‘Рј engine РѕРґРёРЅ СЂР°Р·
    engine = create_engine(
        conf.sqlite_url,
        echo=True,
        connect_args={"check_same_thread": False},
    )

    _SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        raise RuntimeError("Сессия не инициализирована")
    return _SessionLocal


@contextmanager
def get_db():
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
