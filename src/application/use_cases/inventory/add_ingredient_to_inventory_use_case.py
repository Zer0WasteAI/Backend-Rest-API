from datetime import datetime

from src.domain.models.ingredient import IngredientStack


class AddIngredientToInventoryUseCase:
    def __init__(self, inventory_repository, calculator_service):
        self.inventory_repository = inventory_repository
        self.calculator_service = calculator_service

    def execute(
            self,
            user_uid: str,
            name: str,
            quantity: float,
            expiration_time: int,
            time_unit: str,
            type_unit: str,
            storage_type: str,
            tips: str,
            image_path: str,
    ):
        now = datetime.now()
        expiration_date = self.calculator_service.calculate_expiration_date(now, expiration_time, time_unit)

        #Cargar o crear inventario
        inventory = self.inventory_repository.get_by_user_uid(user_uid)
        if not inventory:
            from src.domain.models.inventory import Inventory  # evita import circular
            inventory = Inventory(user_uid=user_uid)
            self.inventory_repository.save(inventory)

        #Agregar nuevo Stack
        stack = IngredientStack(
            quantity=quantity,
            added_at=now,
            expiration_date=expiration_date,
        )

        #Guardando cambios
        self.inventory_repository.update(inventory)