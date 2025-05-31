from datetime import datetime, timezone
from src.domain.models.inventory import Inventory
from src.domain.models.ingredient import Ingredient, IngredientStack
from src.domain.models.food_item import FoodItem

class AddIngredientsAndFoodsToInventoryUseCase:
    def __init__(self, inventory_repository, calculator_service):
        self.inventory_repository = inventory_repository
        self.calculator_service = calculator_service

    def execute(self, user_uid: str, ingredients_data: list[dict], food_items_data: list[dict]) -> None:
        inventory = self.inventory_repository.get_by_user_uid(user_uid)
        if not inventory:
            inventory = Inventory(user_uid=user_uid)
            self.inventory_repository.save(inventory)

        now = datetime.now(timezone.utc)

        # Agregar ingredientes
        for ingredient_data in ingredients_data:
            now = datetime.now()
            expiration_date = self.calculator_service.calculate_expiration_date(
                now, ingredient_data['expiration_time'], ingredient_data['time_unit']
            )

            stack = IngredientStack(
                quantity=ingredient_data['quantity'],
                added_at=now,
                expiration_date=expiration_date,
            )

            ingredient = Ingredient(
                name=ingredient_data['name'],
                type_unit=ingredient_data['type_unit'],
                storage_type=ingredient_data['storage_type'],
                tips=ingredient_data['tips'],
                image_path=ingredient_data['image_path']
            )

            ingredient.add_stack(stack)
            inventory.add_ingredient_stack(user_uid, stack, ingredient)

        # Agregar platos
        for food_item_data in food_items_data:
            added_at = now
            expiration_date = self.calculator_service.calculate_expiration_date(
                added_at, food_item_data['expiration_time'], food_item_data['time_unit']
            )

            food_item = FoodItem(
                name=food_item_data["name"],
                main_ingredients=food_item_data["main_ingredients"],
                category=food_item_data["category"],
                calories=food_item_data.get("calories"),
                description=food_item_data["description"],
                storage_type=food_item_data["storage_type"],
                expiration_time=food_item_data["expiration_time"],
                time_unit=food_item_data["time_unit"],
                tips=food_item_data["tips"],
                serving_quantity=food_item_data["serving_quantity"],
                image_path=food_item_data["image_path"],
                added_at=added_at,
                expiration_date=expiration_date
            )

            inventory.add_food_item(food_item)

        self.inventory_repository.update(inventory)
