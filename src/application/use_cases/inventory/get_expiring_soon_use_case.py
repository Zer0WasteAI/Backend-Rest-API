class GetExpiringSoonUseCase:
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository
    def execute(self, user_uid: str, within_days: int = 3) -> list[str]:
        inventory = self.inventory_repository.get_by_user_uid(user_uid)
        if not inventory:
            return []
        return inventory.get_expiring_soon(within_days)