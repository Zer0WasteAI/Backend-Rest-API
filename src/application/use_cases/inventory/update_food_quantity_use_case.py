from datetime import datetime
from src.domain.models.food_item import FoodItem

class UpdateFoodQuantityUseCase:
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository

    def execute(self, user_uid: str, food_name: str, added_at: str, new_quantity: int):
        """
        Actualiza únicamente la cantidad de porciones de un food item específico.
        Mantiene todos los demás datos intactos.
        
        Args:
            user_uid: ID del usuario
            food_name: Nombre del plato/comida
            added_at: Timestamp del food item a actualizar (ISO format)
            new_quantity: Nueva cantidad de porciones
        """
        print(f"🍽️ [UPDATE FOOD QUANTITY] Updating quantity for {food_name}")
        print(f"   └─ User: {user_uid}")
        print(f"   └─ Added at: {added_at}")
        print(f"   └─ New quantity: {new_quantity}")
        
        # Obtener el food item actual para preservar otros datos
        current_food_data = self.inventory_repository.get_food_item(
            user_uid=user_uid,
            food_name=food_name,
            added_at=added_at
        )
        
        if not current_food_data:
            raise ValueError(f"Food item not found for '{food_name}' added at '{added_at}'")
        
        # Crear nuevo food item con cantidad actualizada pero manteniendo otros datos
        try:
            added_at_datetime = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
        except ValueError:
            added_at_datetime = datetime.strptime(added_at, '%Y-%m-%d %H:%M:%S')
        
        updated_food_item = FoodItem(
            name=food_name,
            main_ingredients=current_food_data['main_ingredients'],
            category=current_food_data['category'],
            calories=current_food_data['calories'],
            description=current_food_data['description'],
            storage_type=current_food_data['storage_type'],
            expiration_time=current_food_data['expiration_time'],
            time_unit=current_food_data['time_unit'],
            tips=current_food_data['tips'],
            serving_quantity=new_quantity,  # ← Solo esto cambia
            image_path=current_food_data['image_path'],
            added_at=added_at_datetime,
            expiration_date=current_food_data['expiration_date']
        )
        
        # Actualizar en el repositorio
        self.inventory_repository.update_food_item(user_uid, updated_food_item)
        
        print(f"✅ [UPDATE FOOD QUANTITY] Successfully updated quantity for {food_name}") 