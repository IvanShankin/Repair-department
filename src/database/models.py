from datetime import datetime, UTC
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from src.database.core import Base


class UserRole(str, Enum):
    WORKER = "рабочий"
    MASTER = "мастер"
    ADMIN = "админ"


class RequestStatus(str, Enum):
    NEW = "Новая"
    IN_PROGRESS = "В процессе"
    DONE = "Готова"
    CANCELED = "Отменена"


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    login = Column(String(50), unique=True, nullable=False)
    hash_password = Column(String(500), nullable=False)
    full_name = Column(String(500), nullable=False)

    role = Column(SqlEnum(UserRole), nullable=False)

    department = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)

    # Relationships
    created_requests = relationship(
        "RepairRequests",
        back_populates="creator",
        foreign_keys="RepairRequests.created_by",
    )

    assigned_requests = relationship(
        "RepairRequests",
        back_populates="master",
        foreign_keys="RepairRequests.assigned_master",
    )


class RepairRequests(Base):
    __tablename__ = "repair_requests"

    id = Column(Integer, primary_key=True)

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    assigned_master = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    equipment_name = Column(String(255), nullable=False)
    description_problem = Column(String(1000), nullable=False)

    status = Column(
        SqlEnum(RequestStatus),
        nullable=False,
        default=RequestStatus.NEW,
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    creator = relationship(
        "Users",
        back_populates="created_requests",
        foreign_keys=[created_by],
    )

    master = relationship(
        "Users",
        back_populates="assigned_requests",
        foreign_keys=[assigned_master],
    )
