from datetime import datetime, timezone
from src.domain.models.inventory import Inventory
from src.domain.models.ingredient import Ingredient, IngredientStack
from src.domain.models.food_item import FoodItem

class AddIngredientsAndFoodsToInventoryUseCase:
    def __init__(self, inventory_repository, calculator_service):
        self.inventory_repository = inventory_repository
        self.calculator_service = calculator_service

    def execute(self, user_uid: str, ingredients_data: list[dict], food_items_data: list[dict]) -> None:
        print(f"🏗️ [ADD INGREDIENTS AND FOODS USE CASE] Starting execution for user: {user_uid}")
        print(f"📦 [ADD INGREDIENTS AND FOODS USE CASE] {len(ingredients_data)} ingredients, {len(food_items_data)} foods")
        
        inventory = self.inventory_repository.get_by_user_uid(user_uid)
        if not inventory:
            inventory = Inventory(user_uid=user_uid)
            self.inventory_repository.save(inventory)

        now = datetime.now(timezone.utc)

        # Agregar ingredientes
        for i, ingredient_data in enumerate(ingredients_data):
            print(f"🥬 [INGREDIENT {i+1}] Processing: {ingredient_data['name']}")
            
            # ⭐ MEJORADO: Usar expiration_date del reconocimiento si existe, sino calcular
            if "expiration_date" in ingredient_data and ingredient_data["expiration_date"]:
                # Formato de reconocimiento: usar fecha pre-calculada
                expiration_date_str = ingredient_data["expiration_date"]
                if expiration_date_str.endswith('Z'):
                    expiration_date_str = expiration_date_str.replace('Z', '+00:00')
                expiration_date = datetime.fromisoformat(expiration_date_str)
                print(f"   └─ ✅ Using pre-calculated expiration: {expiration_date}")
            elif "expiration_time" in ingredient_data and "time_unit" in ingredient_data:
                # Formato manual: calcular fecha de vencimiento
                expiration_date = self.calculator_service.calculate_expiration_date(
                    now, ingredient_data['expiration_time'], ingredient_data['time_unit']
                )
                print(f"   └─ ⏳ Calculated new expiration: {expiration_date}")
            else:
                # Error: falta información de vencimiento
                raise ValueError(f"Ingredient '{ingredient_data['name']}' requires either 'expiration_date' or both 'expiration_time' and 'time_unit'")

            stack = IngredientStack(
                quantity=ingredient_data['quantity'],
                type_unit=ingredient_data['type_unit'],
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
            print(f"   └─ ✅ Successfully added ingredient: {ingredient_data['name']}")

        # Agregar platos
        for i, food_item_data in enumerate(food_items_data):
            print(f"🍽️ [FOOD {i+1}] Processing: {food_item_data['name']}")
            
            # ⭐ MEJORADO: Usar expiration_date del reconocimiento si existe, sino calcular
            if "expiration_date" in food_item_data and food_item_data["expiration_date"]:
                # Formato de reconocimiento: usar fecha pre-calculada
                expiration_date_str = food_item_data["expiration_date"]
                if expiration_date_str.endswith('Z'):
                    expiration_date_str = expiration_date_str.replace('Z', '+00:00')
                expiration_date = datetime.fromisoformat(expiration_date_str)
                print(f"   └─ ✅ Using pre-calculated expiration: {expiration_date}")
            elif "expiration_time" in food_item_data and "time_unit" in food_item_data:
                # Formato manual: calcular fecha de vencimiento
                expiration_date = self.calculator_service.calculate_expiration_date(
                    now, food_item_data['expiration_time'], food_item_data['time_unit']
                )
                print(f"   └─ ⏳ Calculated new expiration: {expiration_date}")
            else:
                # Error: falta información de vencimiento
                raise ValueError(f"Food item '{food_item_data['name']}' requires either 'expiration_date' or both 'expiration_time' and 'time_unit'")

            food_item = FoodItem(
                name=food_item_data["name"],
                main_ingredients=food_item_data["main_ingredients"],
                category=food_item_data["category"],
                calories=food_item_data.get("calories"),
                description=food_item_data["description"],
                storage_type=food_item_data["storage_type"],
                expiration_time=food_item_data.get("expiration_time"),
                time_unit=food_item_data.get("time_unit"),
                tips=food_item_data["tips"],
                serving_quantity=food_item_data["serving_quantity"],
                image_path=food_item_data["image_path"],
                added_at=now,
                expiration_date=expiration_date
            )

            inventory.add_food_item(food_item)
            print(f"   └─ ✅ Successfully added food: {food_item_data['name']}")

        self.inventory_repository.update(inventory)
        print(f"🎉 [ADD INGREDIENTS AND FOODS USE CASE] Successfully processed all items")
