from datetime import datetime, timezone


class MarkIngredientStackConsumedUseCase:
    """Caso de uso para marcar un stack específico de ingrediente como consumido"""
    
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository
    
    def execute(self, user_uid: str, ingredient_name: str, added_at: str, consumed_quantity: float = None) -> dict:
        """
        Marca un stack específico de ingrediente como consumido.
        
        Args:
            user_uid: UID del usuario
            ingredient_name: Nombre del ingrediente
            added_at: Timestamp del stack (ISO format)
            consumed_quantity: Cantidad consumida (opcional, por defecto consume to/do el stack)
            
        Returns:
            dict: Información sobre lo que se marcó como consumido
        """
        print(f"🍽️ [MARK INGREDIENT CONSUMED] Processing for user: {user_uid}")
        print(f"   └─ Ingredient: {ingredient_name}")
        print(f"   └─ Stack added at: {added_at}")
        print(f"   └─ Consumed quantity: {consumed_quantity or 'ALL'}")
        
        # Verificar que el stack existe
        existing_stack = self.inventory_repository.get_ingredient_stack(user_uid, ingredient_name, added_at)
        
        if not existing_stack:
            raise ValueError(f"Ingredient stack '{ingredient_name}' not found (added at: {added_at})")
        
        current_quantity = existing_stack['quantity']
        
        # Determinar cantidad a consumir
        if consumed_quantity is None:
            # Consumir to/do el stack
            consumed_quantity = current_quantity
            action = "full_consumption"
        else:
            # Validar cantidad
            if consumed_quantity <= 0:
                raise ValueError("Consumed quantity must be greater than 0")
            if consumed_quantity > current_quantity:
                raise ValueError(f"Cannot consume {consumed_quantity} {existing_stack['type_unit']} - only {current_quantity} {existing_stack['type_unit']} available")
            
            action = "partial_consumption" if consumed_quantity < current_quantity else "full_consumption"
        
        print(f"   └─ Action: {action}")
        print(f"   └─ Available: {current_quantity} {existing_stack['type_unit']}")
        print(f"   └─ To consume: {consumed_quantity} {existing_stack['type_unit']}")
        
        if action == "full_consumption":
            # Eliminar el stack completamente
            self.inventory_repository.delete_ingredient_stack(user_uid, ingredient_name, added_at)
            print(f"   └─ Stack completely consumed and removed")
            
            return {
                "message": "Ingredient stack marked as consumed",
                "action": "full_consumption",
                "ingredient": ingredient_name,
                "consumed_quantity": consumed_quantity,
                "unit": existing_stack['type_unit'],
                "stack_removed": True,
                "consumed_at": datetime.now(timezone.utc).isoformat(),
                "original_added_at": added_at
            }
        
        else:
            # Actualizar la cantidad del stack
            remaining_quantity = current_quantity - consumed_quantity
            
            # Crear stack actualizado
            from src.domain.models.ingredient import IngredientStack, Ingredient
            
            # Convertir added_at a datetime
            try:
                added_at_datetime = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
            except ValueError:
                added_at_datetime = datetime.strptime(added_at, '%Y-%m-%d %H:%M:%S')
            
            updated_stack = IngredientStack(
                quantity=remaining_quantity,
                type_unit=existing_stack['type_unit'],
                added_at=added_at_datetime,
                expiration_date=existing_stack['expiration_date']
            )
            
            updated_ingredient = Ingredient(
                name=ingredient_name,
                type_unit=existing_stack['type_unit'],
                storage_type=existing_stack['storage_type'],
                tips=existing_stack['tips'],
                image_path=existing_stack['image_path']
            )
            
            # Actualizar en el repositorio
            self.inventory_repository.update_ingredient_stack(
                user_uid=user_uid,
                ingredient_name=ingredient_name,
                added_at=added_at,
                new_stack=updated_stack,
                new_meta=updated_ingredient
            )
            
            print(f"   └─ Stack updated: {remaining_quantity} {existing_stack['type_unit']} remaining")
            
            return {
                "message": "Ingredient partially consumed",
                "action": "partial_consumption",
                "ingredient": ingredient_name,
                "consumed_quantity": consumed_quantity,
                "remaining_quantity": remaining_quantity,
                "unit": existing_stack['type_unit'],
                "stack_removed": False,
                "consumed_at": datetime.now(timezone.utc).isoformat(),
                "original_added_at": added_at
            } 