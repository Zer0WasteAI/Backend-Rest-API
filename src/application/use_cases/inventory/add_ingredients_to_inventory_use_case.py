from datetime import datetime
from src.domain.models.ingredient import Ingredient, IngredientStack

class AddIngredientsToInventoryUseCase:
    def __init__(self, repository, calculator):
        self.repository = repository
        self.calculator = calculator

    def execute(self, user_uid: str, ingredients_data: list[dict]):
        inventory = self.repository.get_inventory(user_uid)
        if inventory is None:
            self.repository.create_inventory(user_uid)

        now = datetime.now()
        for item in ingredients_data:
            name = item["name"]
            type_unit = item["type_unit"]
            storage_type = item["storage_type"]
            tips = item["tips"]
            image_path = item["image_path"]
            quantity = item["quantity"]
            expiration_time = item["expiration_time"]
            time_unit = item["time_unit"]

            expiration_date = self.calculator.calculate_expiration_date(
                added_at=now,
                time_value=expiration_time,
                time_unit=time_unit
            )

            ingredient = Ingredient(
                name=name,
                type_unit=type_unit,
                storage_type=storage_type,
                tips=tips,
                image_path=image_path
            )

            stack = IngredientStack(
                quantity=quantity,
                expiration_date=expiration_date,
                added_at=now
            )

            self.repository.add_ingredient_stack(user_uid, stack, ingredient)
