from src.domain.models.inventory import Inventory

class GetInventoryUseCase:
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository
    def execute(self, user_uid: str) -> Inventory:
        inventory = self.inventory_repository.get_by_user_uid(user_uid)
        if not inventory:
            inventory = Inventory(user_uid=user_uid)
        return inventory