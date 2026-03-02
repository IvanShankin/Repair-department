import logging

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

from src.service.config.core import get_config

from src.database.core import Base, get_db
from src.database.models import UserRole, Users
from src.repository.users import get_user_repository


async def filling_db():
    await _create_database()
    await _create_table()
    await _ensure_soft_delete_column()

    await _filling_only_one_admin()


async def _create_database():
    """
    Создаёт файл SQLite базы данных и все таблицы.
    Если файл существует — ничего не ломает.
    """
    conf = get_config()
    engine = create_async_engine(conf.sqlite_url, echo=True)

    try:
        async with engine.begin() as conn:
            logging.info(f"Creating database tables at {conf.data_base_path}...")
            await conn.run_sync(Base.metadata.create_all)
            logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating tables: {e}")
        raise
    finally:
        await engine.dispose()


async def _create_table():
    """создает таблицы в целевой базе данных"""
    engine = create_async_engine(get_config().sqlite_url)
    try:
        async with engine.begin() as conn:
            logging.info("Creating core tables...")
            await conn.run_sync(Base.metadata.create_all)
            logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating tables: {e}")
        raise
    finally:
        await engine.dispose()


async def _filling_only_one_admin():
    async with get_db() as session_db:
        result_db = await session_db.execute(select(Users).where(Users.role == UserRole.ADMIN))
        admins = result_db.scalars().all()

        if not admins:
            user_repo = await get_user_repository()
            await user_repo.create(
                login="admin",
                password="admin",
                full_name="admin",
                role=UserRole.ADMIN,
            ),


async def _ensure_soft_delete_column():
    engine = create_async_engine(get_config().sqlite_url)
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]

            if "is_deleted" not in columns:
                logging.info("Adding users.is_deleted column...")
                await conn.execute(
                    text("ALTER TABLE users ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT 0")
                )
                logging.info("users.is_deleted column added")
    finally:
        await engine.dispose()
