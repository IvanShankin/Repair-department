from src.database.core import get_db
from src.repository.repair_requests.repair_requests import RepairRequestRepository


async def get_repair_request_repository() -> RepairRequestRepository:
    async with get_db() as session_db:
        return RepairRequestRepository(
            session=session_db
        )