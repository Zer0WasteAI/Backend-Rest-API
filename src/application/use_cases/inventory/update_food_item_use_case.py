from datetime import datetime
from src.domain.models.food_item import FoodItem

class UpdateFoodItemUseCase:
    def __init__(self, inventory_repository, calculator_service):
        self.inventory_repository = inventory_repository
        self.calculator_service = calculator_service

    def execute(self, user_uid: str, food_item_data: dict):
        # ⭐ MEJORADO: Manejar ambos formatos de fecha de vencimiento
        if "expiration_date" in food_item_data and food_item_data["expiration_date"]:
            # Formato de reconocimiento: usar fecha pre-calculada
            expiration_date_str = food_item_data["expiration_date"]
            if expiration_date_str.endswith('Z'):
                expiration_date_str = expiration_date_str.replace('Z', '+00:00')
            expiration_date = datetime.fromisoformat(expiration_date_str)
        elif "expiration_time" in food_item_data and "time_unit" in food_item_data:
            # Formato manual: calcular fecha de vencimiento
            expiration_date = self.calculator_service.calculate_expiration_date(
                food_item_data["added_at"], food_item_data["expiration_time"], food_item_data["time_unit"]
            )
        else:
            # Error: falta información de vencimiento
            raise ValueError(f"Food item data requires either 'expiration_date' or both 'expiration_time' and 'time_unit'")

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
            added_at=food_item_data["added_at"],
            expiration_date=expiration_date
        )

        self.inventory_repository.update_food_item(user_uid, food_item)