from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.service.config.core import get_config


Base_sqlalchemy = declarative_base()
_AsyncSessionLocal: Any = None

class Base(Base_sqlalchemy):
    __abstract__ = True

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


async def init_db():
    global _AsyncSessionLocal
    conf = get_config()

    # создаём engine один раз
    engine = create_async_engine(conf.sqlite_url, echo=True)

    _AsyncSessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


def get_async_session():
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        raise RuntimeError("Сессия не инициализированна")
    return _AsyncSessionLocal


@asynccontextmanager
async def get_db() -> AsyncSession:
    session_factory = get_async_session()

    async with session_factory() as session:
        yield session
