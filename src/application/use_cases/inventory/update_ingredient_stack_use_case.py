from datetime import datetime
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
        # ⭐ MEJORADO: Manejar ambos formatos de fecha de vencimiento
        if "expiration_date" in updated_data and updated_data["expiration_date"]:
            # Formato de reconocimiento: usar fecha pre-calculada
            expiration_date_str = updated_data["expiration_date"]
            if expiration_date_str.endswith('Z'):
                expiration_date_str = expiration_date_str.replace('Z', '+00:00')
            new_expiration = datetime.fromisoformat(expiration_date_str)
        elif "expiration_time" in updated_data and "time_unit" in updated_data:
            # Formato manual: calcular fecha de vencimiento
            new_expiration = self.calculator_service.calculate_expiration_date(
                updated_data["added_at"], updated_data["expiration_time"], updated_data["time_unit"]
            )
        else:
            # Error: falta información de vencimiento
            raise ValueError(f"Update data requires either 'expiration_date' or both 'expiration_time' and 'time_unit'")

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
