class DeleteIngredientStackUseCase:
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository

    def execute(self, user_uid: str, ingredient_name: str, added_at: str):
        """
        Elimina un stack específico de ingrediente del inventario.
        Si es el último stack, elimina también el ingrediente completo.
        
        Args:
            user_uid: ID del usuario
            ingredient_name: Nombre del ingrediente
            added_at: Timestamp del stack a eliminar
        """
        print(f"🗑️ [DELETE INGREDIENT STACK] Deleting stack: {ingredient_name}")
        print(f"   └─ User: {user_uid}")
        print(f"   └─ Stack added at: {added_at}")
        
        # Verificar si el stack existe
        existing_stack = self.inventory_repository.get_ingredient_stack(user_uid, ingredient_name, added_at)
        
        if not existing_stack:
            raise ValueError(f"Ingredient stack '{ingredient_name}' not found (added at: {added_at})")
        
        print(f"   └─ Found stack to delete: {ingredient_name}")
        
        # Eliminar el stack
        self.inventory_repository.delete_ingredient_stack(user_uid, ingredient_name, added_at)
        
        print(f"✅ [DELETE INGREDIENT STACK] Successfully deleted stack: {ingredient_name}")