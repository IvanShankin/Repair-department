import hashlib
import hmac
import os
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Users, UserRole


class UserRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    def _hash_password(self, password: str) -> str:
        salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100_000,
        )
        return f"pbkdf2_sha256${salt.hex()}${key.hex()}"

    def verify_password(self, password: str, stored: str) -> bool:
        """
        :param password: пароль, который вводит пользователь
        :param stored: пароль из БД
        :return:
        """
        if stored.startswith("pbkdf2_sha256$"):
            _, salt_hex, hash_hex = stored.split("$", 2)
            salt = bytes.fromhex(salt_hex)
            test_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                100_000,
            )
            return hmac.compare_digest(test_hash.hex(), hash_hex)

        return hmac.compare_digest(password, stored)

    async def create(
        self,
        login: str,
        password: str,
        full_name: str,
        role: UserRole,
        department: Optional[str] = None,
    ) -> Users:
        user = Users(
            login=login,
            hash_password=self._hash_password(password),
            full_name=full_name,
            role=role,
            department=department,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def get_by_id(self, user_id: int) -> Optional[Users]:
        return await self.session.get(Users, user_id)

    async def get_by_login(self, login: str) -> Optional[Users]:
        stmt = select(Users).where(Users.login == login)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Users]:
        stmt = select(Users)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, user: Users, **kwargs) -> Users:
        for key, value in kwargs.items():
            setattr(user, key, value)

        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def delete(self, user: Users) -> None:
        await self.session.delete(user)
        await self.session.commit()