from typing import Optional, List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import RepairRequests, RequestStatus


class RepairRequestRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
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

        self.session.add(request)
        await self.session.commit()
        await self.session.refresh(request)

        return request

    async def get_by_id(self, request_id: int) -> Optional[RepairRequests]:
        return await self.session.get(RepairRequests, request_id)

    async def get_all(self) -> List[RepairRequests]:
        stmt = select(RepairRequests).order_by(RepairRequests.created_by.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_creator(self, user_id: int) -> List[RepairRequests]:
        stmt = select(RepairRequests).where(
            RepairRequests.created_by == user_id
        ).order_by(RepairRequests.created_by.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_master(self, master_id: int) -> List[RepairRequests]:
        stmt = select(RepairRequests).where(
            RepairRequests.assigned_master == master_id
        ).order_by(RepairRequests.created_by.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, request: RepairRequests, **kwargs) -> RepairRequests:
        for key, value in kwargs.items():
            setattr(request, key, value)

        await self.session.commit()
        await self.session.refresh(request)

        return request

    async def update_status(
        self,
        request: RepairRequests,
        status: RequestStatus
    ) -> RepairRequests:
        request.status = status

        await self.session.commit()
        await self.session.refresh(request)

        return request

    async def delete(self, request_id: int) -> None:
        await self.session.execute(delete(RepairRequests).where(RepairRequests.id == request_id))
        await self.session.commit()