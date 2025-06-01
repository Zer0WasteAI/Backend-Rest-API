class DeleteFoodItemUseCase:
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository

    def execute(self, user_uid: str, food_name: str, added_at: str):
        self.inventory_repository.delete_food_item(user_uid, food_name, added_at)