# src/application/use_cases/inventory/get_inventory_content_use_case.py

from typing import Optional
from src.domain.models.inventory import Inventory
from src.domain.repositories.inventory_repository import InventoryRepository

class GetInventoryContentUseCase:
    def __init__(self, repository: InventoryRepository):
        self.repository = repository

    def execute(self, user_uid: str) -> Optional[Inventory]:
        return self.repository.get_by_user_uid(user_uid)
