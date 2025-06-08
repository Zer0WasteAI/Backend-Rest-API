class DeleteFoodItemUseCase:
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository

    def execute(self, user_uid: str, food_name: str, added_at: str):
        """
        Elimina un food item específico del inventario.
        
        Args:
            user_uid: ID del usuario
            food_name: Nombre de la comida a eliminar
            added_at: Timestamp del food item
        """
        print(f"🗑️ [DELETE FOOD ITEM] Deleting food item: {food_name}")
        print(f"   └─ User: {user_uid}")
        print(f"   └─ Added at: {added_at}")
        
        # Verificar si el food item existe
        existing_food = self.inventory_repository.get_food_item(user_uid, food_name, added_at)
        
        if not existing_food:
            raise ValueError(f"Food item '{food_name}' not found for deletion (added at: {added_at})")
        
        print(f"   └─ Found food item to delete: {food_name}")
        
        # Eliminar el food item
        self.inventory_repository.delete_food_item(user_uid, food_name, added_at)
        
        print(f"✅ [DELETE FOOD ITEM] Successfully deleted food item: {food_name}")