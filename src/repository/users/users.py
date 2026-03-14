import hashlib
import hmac
import os
from typing import Optional, List

from src.database.core import get_db
from src.database.models import Users, UserRole


class UserRepository:

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

    def create(
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

        with get_db() as session:
            try:
                session.add(user)
                session.commit()
                session.refresh(user)
            except Exception:
                session.rollback()
                raise

        return user

    def get_by_id(self, user_id: int) -> Optional[Users]:
        with get_db() as session:
            return session.query(Users).get(user_id)

    def get_by_login(self, login: str) -> Optional[Users]:
        with get_db() as session:
            return (
                session.query(Users)
                .filter(
                    Users.login == login,
                    Users.is_deleted.is_(False),
                )
                .one_or_none()
            )

    def get_all(self, include_deleted: bool = False) -> List[Users]:
        with get_db() as session:
            query = session.query(Users)

            if not include_deleted:
                query = query.filter(Users.is_deleted.is_(False))

            return query.all()

    def update(self, user: Users, **kwargs) -> Users:
        password = kwargs.pop("password", None)

        for key, value in kwargs.items():
            setattr(user, key, value)

        if password:
            user.hash_password = self._hash_password(password)

        with get_db() as session:
            try:
                merged = session.merge(user)
                session.commit()
                session.refresh(merged)
            except Exception:
                session.rollback()
                raise

        return merged

    def delete(self, user: Users) -> None:
        with get_db() as session:
            try:
                user_in_session = session.merge(user)
                session.delete(user_in_session)
                session.commit()
            except Exception:
                session.rollback()
                raise

    def soft_delete(self, user: Users) -> Users:
        user.full_name = f"[DELETED] {user.full_name}"
        user.login = f"deleted_{user.id}_{user.login}"
        user.hash_password = self._hash_password(os.urandom(12).hex())
        user.department = None
        user.is_deleted = True

        with get_db() as session:
            try:
                merged = session.merge(user)
                session.commit()
                session.refresh(merged)
            except Exception:
                session.rollback()
                raise

        return merged
