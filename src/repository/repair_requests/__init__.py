from src.repository.repair_requests.repair_requests import RepairRequestRepository


def get_repair_request_repository() -> RepairRequestRepository:
    return RepairRequestRepository()
