class DeleteIngredientStackUseCase:
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository

    def execute(self, user_uid: str, ingredient_name: str, added_at: str):
        self.inventory_repository.delete_ingredient_stack(user_uid, ingredient_name, added_at)