from src.domain.models.food_item import FoodItem
class UpdateFoodItemUseCase:
    def __init__(self, inventory_repository, calculator_service):
        self.inventory_repository = inventory_repository
        self.calculator_service = calculator_service

    def execute(self, user_uid: str, food_item_data: dict):
        expiration_date = self.calculator_service.calculate_expiration_date(
            food_item_data["added_at"], food_item_data["expiration_time"], food_item_data["time_unit"]
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
            added_at=food_item_data["added_at"],
            expiration_date=expiration_date
        )

        self.inventory_repository.update_food_item(user_uid, food_item)