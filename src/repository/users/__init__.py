from src.repository.users.users import UserRepository


def get_user_repository() -> UserRepository:
    return UserRepository()
