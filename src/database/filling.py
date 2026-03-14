import logging

from sqlalchemy import text, create_engine

from src.service.config.core import get_config
from src.database.core import Base, get_db
from src.database.models import UserRole, Users
from src.repository.users import get_user_repository


def filling_db():
    _create_database()
    _create_table()
    _ensure_soft_delete_column()

    _filling_only_one_admin()


def _create_database():
    conf = get_config()
    engine = create_engine(
        conf.sqlite_url,
        echo=True,
        connect_args={"check_same_thread": False},
    )

    try:
        logging.info(f"Creating database tables at {conf.data_base_path}...")
        Base.metadata.create_all(engine)
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating tables: {e}")
        raise
    finally:
        engine.dispose()


def _create_table():
    engine = create_engine(
        get_config().sqlite_url,
        connect_args={"check_same_thread": False},
    )
    try:
        logging.info("Creating core tables...")
        Base.metadata.create_all(engine)
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating tables: {e}")
        raise
    finally:
        engine.dispose()


def _filling_only_one_admin():
    with get_db() as session_db:
        admins = (
            session_db.query(Users)
            .filter(Users.role == UserRole.ADMIN)
            .all()
        )

    if not admins:
        user_repo = get_user_repository()
        user_repo.create(
            login="admin",
            password="admin",
            full_name="admin",
            role=UserRole.ADMIN,
        )


def _ensure_soft_delete_column():
    engine = create_engine(
        get_config().sqlite_url,
        connect_args={"check_same_thread": False},
    )
    try:
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result.fetchall()]

            if "is_deleted" not in columns:
                logging.info("Adding users.is_deleted column...")
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT 0")
                )
                logging.info("users.is_deleted column added")
    finally:
        engine.dispose()
