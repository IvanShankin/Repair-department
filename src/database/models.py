from datetime import datetime, UTC
from enum import Enum

from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    DateTime,
    Enum as SqlEnum,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src.database.core import Base


class UserRole(str, Enum):
    WORKER = "WORKER"
    MASTER = "MASTER"
    ADMIN = "ADMIN"


class RequestStatus(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELED = "CANCELED"


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    login: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hash_password: Mapped[str] = mapped_column(String(500), nullable=False)
    full_name: Mapped[str] = mapped_column(String(500), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole),
        nullable=False
    )

    department: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    created_requests: Mapped[list["RepairRequests"]] = relationship(
        back_populates="creator",
        foreign_keys="RepairRequests.created_by"
    )

    assigned_requests: Mapped[list["RepairRequests"]] = relationship(
        back_populates="master",
        foreign_keys="RepairRequests.assigned_master"
    )


class RepairRequests(Base):
    __tablename__ = "repair_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    assigned_master: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    equipment_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description_problem: Mapped[str] = mapped_column(String(1000), nullable=False)

    status: Mapped[RequestStatus] = mapped_column(
        SqlEnum(RequestStatus),
        nullable=False,
        default=RequestStatus.NEW
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(UTC)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC)
    )

    # Relationships
    creator: Mapped["Users"] = relationship(
        back_populates="created_requests",
        foreign_keys=[created_by]
    )

    master: Mapped["Users"] = relationship(
        back_populates="assigned_requests",
        foreign_keys=[assigned_master]
    )