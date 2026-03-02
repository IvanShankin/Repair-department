from src.database.core import get_db
from src.repository.users.users import UserRepository


async def get_user_repository() -> UserRepository:
    async with get_db() as session_db:
        return UserRepository(
            session=session_db
        )