from src.domain.models.ingredient import Ingredient, IngredientStack
class UpdateIngredientStackUseCase:
    def __init__(self, inventory_repository, calculator_service):
        self.inventory_repository = inventory_repository
        self.calculator_service = calculator_service

    def execute(
        self,
        user_uid: str,
        ingredient_name: str,
        added_at: str,
        updated_data: dict
    ):
        new_expiration = self.calculator_service.calculate_expiration_date(
            updated_data["added_at"], updated_data["expiration_time"], updated_data["time_unit"]
        )

        new_stack = IngredientStack(
            quantity=updated_data["quantity"],
            type_unit=updated_data["type_unit"],
            added_at=updated_data["added_at"],
            expiration_date=new_expiration
        )

        new_meta = Ingredient(
            name=ingredient_name,
            type_unit=updated_data["type_unit"],
            storage_type=updated_data["storage_type"],
            tips=updated_data["tips"],
            image_path=updated_data["image_path"]
        )

        self.inventory_repository.update_ingredient_stack(
            user_uid=user_uid,
            ingredient_name=ingredient_name,
            added_at=added_at,
            new_stack=new_stack,
            new_meta=new_meta
        )
