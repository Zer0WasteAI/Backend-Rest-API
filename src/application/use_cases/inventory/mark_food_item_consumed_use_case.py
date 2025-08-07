from datetime import datetime, timezone


class MarkFoodItemConsumedUseCase:
    """Caso de uso para marcar un food item como consumido"""
    
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository
    
    def execute(self, user_uid: str, food_name: str, added_at: str, consumed_portions: float = None) -> dict:
        """
        Marca un food item como consumido.
        
        Args:
            user_uid: UID del usuario
            food_name: Nombre de la comida
            added_at: Timestamp del food item (ISO format)
            consumed_portions: Porciones consumidas (opcional, por defecto consume to/do)
            
        Returns:
            dict: Información sobre lo que se marcó como consumido
        """
        print(f"🍽️ [MARK FOOD CONSUMED] Processing for user: {user_uid}")
        print(f"   └─ Food: {food_name}")
        print(f"   └─ Added at: {added_at}")
        print(f"   └─ Consumed portions: {consumed_portions or 'ALL'}")
        
        # Verificar que el food item existe
        existing_food = self.inventory_repository.get_food_item(user_uid, food_name, added_at)
        
        if not existing_food:
            raise ValueError(f"Food item '{food_name}' not found (added at: {added_at})")
        
        current_portions = existing_food['serving_quantity']
        
        # Determinar porciones a consumir
        if consumed_portions is None:
            # Consumir to/do el food item
            consumed_portions = current_portions
            action = "full_consumption"
        else:
            # Validar porciones
            if consumed_portions <= 0:
                raise ValueError("Consumed portions must be greater than 0")
            if consumed_portions > current_portions:
                raise ValueError(f"Cannot consume {consumed_portions} portions - only {current_portions} portions available")
            
            action = "partial_consumption" if consumed_portions < current_portions else "full_consumption"
        
        print(f"   └─ Action: {action}")
        print(f"   └─ Available: {current_portions} portions")
        print(f"   └─ To consume: {consumed_portions} portions")
        
        if action == "full_consumption":
            # Eliminar el food item completamente
            self.inventory_repository.delete_food_item(user_uid, food_name, added_at)
            print(f"   └─ Food item completely consumed and removed")
            
            return {
                "message": "Food item marked as consumed",
                "action": "full_consumption",
                "food": food_name,
                "consumed_portions": consumed_portions,
                "food_removed": True,
                "consumed_at": datetime.now(timezone.utc).isoformat(),
                "original_added_at": added_at,
                "food_details": {
                    "category": existing_food.get('category'),
                    "main_ingredients": existing_food.get('main_ingredients'),
                    "calories": existing_food.get('calories'),
                    "description": existing_food.get('description')
                }
            }
        
        else:
            # Actualizar las porciones del food item
            remaining_portions = current_portions - consumed_portions
            
            # Crear food item actualizado
            from src.domain.models.food_item import FoodItem
            
            # Convertir added_at a datetime
            try:
                added_at_datetime = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
            except ValueError:
                added_at_datetime = datetime.strptime(added_at, '%Y-%m-%d %H:%M:%S')
            
            updated_food_item = FoodItem(
                name=food_name,
                main_ingredients=existing_food['main_ingredients'],
                category=existing_food['category'],
                calories=existing_food['calories'],
                description=existing_food['description'],
                storage_type=existing_food['storage_type'],
                expiration_time=existing_food['expiration_time'],
                time_unit=existing_food['time_unit'],
                tips=existing_food['tips'],
                serving_quantity=remaining_portions,  # Nueva cantidad
                image_path=existing_food['image_path'],
                added_at=added_at_datetime,
                expiration_date=existing_food['expiration_date']
            )
            
            # Actualizar en el repositorio
            self.inventory_repository.update_food_item(user_uid, updated_food_item)
            
            print(f"   └─ Food item updated: {remaining_portions} portions remaining")
            
            return {
                "message": "Food item partially consumed",
                "action": "partial_consumption",
                "food": food_name,
                "consumed_portions": consumed_portions,
                "remaining_portions": remaining_portions,
                "food_removed": False,
                "consumed_at": datetime.now(timezone.utc).isoformat(),
                "original_added_at": added_at,
                "food_details": {
                    "category": existing_food.get('category'),
                    "main_ingredients": existing_food.get('main_ingredients'),
                    "calories": existing_food.get('calories'),
                    "description": existing_food.get('description')
                }
            } 