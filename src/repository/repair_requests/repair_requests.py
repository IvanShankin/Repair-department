from typing import Optional, List

from src.database.core import get_db
from src.database.models import RepairRequests, RequestStatus


class RepairRequestRepository:

    def create(
        self,
        created_by: int,
        equipment_name: str,
        description_problem: str,
        assigned_master: Optional[int] = None,
    ) -> RepairRequests:

        request = RepairRequests(
            created_by=created_by,
            assigned_master=assigned_master,
            equipment_name=equipment_name,
            description_problem=description_problem,
        )

        with get_db() as session:
            try:
                session.add(request)
                session.commit()
                session.refresh(request)
            except Exception:
                session.rollback()
                raise

        return request

    def get_by_id(self, request_id: int) -> Optional[RepairRequests]:
        with get_db() as session:
            return session.query(RepairRequests).get(request_id)

    def get_all(self) -> List[RepairRequests]:
        with get_db() as session:
            return (
                session.query(RepairRequests)
                .order_by(RepairRequests.created_by.desc())
                .all()
            )

    def get_by_creator(self, user_id: int) -> List[RepairRequests]:
        with get_db() as session:
            return (
                session.query(RepairRequests)
                .filter(RepairRequests.created_by == user_id)
                .order_by(RepairRequests.created_by.desc())
                .all()
            )

    def get_by_master(self, master_id: int) -> List[RepairRequests]:
        with get_db() as session:
            return (
                session.query(RepairRequests)
                .filter(RepairRequests.assigned_master == master_id)
                .order_by(RepairRequests.created_by.desc())
                .all()
            )

    def update(self, request: RepairRequests, **kwargs) -> RepairRequests:
        for key, value in kwargs.items():
            setattr(request, key, value)

        with get_db() as session:
            try:
                merged = session.merge(request)
                session.commit()
                session.refresh(merged)
            except Exception:
                session.rollback()
                raise

        return merged

    def update_status(
        self,
        request: RepairRequests,
        status: RequestStatus
    ) -> RepairRequests:
        request.status = status

        with get_db() as session:
            try:
                merged = session.merge(request)
                session.commit()
                session.refresh(merged)
            except Exception:
                session.rollback()
                raise

        return merged

    def delete(self, request_id: int) -> None:
        with get_db() as session:
            try:
                session.query(RepairRequests).filter(
                    RepairRequests.id == request_id
                ).delete(synchronize_session=False)
                session.commit()
            except Exception:
                session.rollback()
                raise
