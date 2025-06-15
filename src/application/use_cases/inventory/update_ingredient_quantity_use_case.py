from datetime import datetime
from src.domain.models.ingredient import Ingredient, IngredientStack

class UpdateIngredientQuantityUseCase:
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository

    def execute(self, user_uid: str, ingredient_name: str, added_at: str, new_quantity: float):
        """
        Actualiza únicamente la cantidad de un stack específico de ingrediente.
        Mantiene todos los demás datos intactos.
        
        Args:
            user_uid: ID del usuario
            ingredient_name: Nombre del ingrediente
            added_at: Timestamp del stack a actualizar (ISO format)
            new_quantity: Nueva cantidad
        """
        print(f"📦 [UPDATE QUANTITY] Updating quantity for {ingredient_name}")
        print(f"   └─ User: {user_uid}")
        print(f"   └─ Stack added at: {added_at}")
        print(f"   └─ New quantity: {new_quantity}")
        
        # Obtener el stack actual para preservar otros datos
        current_stack_data = self.inventory_repository.get_ingredient_stack(
            user_uid=user_uid,
            ingredient_name=ingredient_name,
            added_at=added_at
        )
        
        if not current_stack_data:
            raise ValueError(f"Stack not found for ingredient '{ingredient_name}' added at '{added_at}'")
        
        # Crear nuevo stack con cantidad actualizada pero manteniendo otros datos
        try:
            added_at_datetime = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
        except ValueError:
            added_at_datetime = datetime.strptime(added_at, '%Y-%m-%d %H:%M:%S')
        
        updated_stack = IngredientStack(
            quantity=new_quantity,  # ← Solo esto cambia
            type_unit=current_stack_data['type_unit'],
            added_at=added_at_datetime,
            expiration_date=current_stack_data['expiration_date']
        )
        
        updated_ingredient = Ingredient(
            name=ingredient_name,
            type_unit=current_stack_data['type_unit'],
            storage_type=current_stack_data['storage_type'],
            tips=current_stack_data['tips'],
            image_path=current_stack_data['image_path']
        )
        
        # Actualizar en el repositorio
        self.inventory_repository.update_ingredient_stack(
            user_uid=user_uid,
            ingredient_name=ingredient_name,
            added_at=added_at,
            new_stack=updated_stack,
            new_meta=updated_ingredient
        )
        
        print(f"✅ [UPDATE QUANTITY] Successfully updated quantity for {ingredient_name}") 