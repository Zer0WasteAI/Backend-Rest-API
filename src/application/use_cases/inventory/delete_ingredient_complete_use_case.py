class DeleteIngredientCompleteUseCase:
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository

    def execute(self, user_uid: str, ingredient_name: str):
        """
        Elimina un ingrediente completo del inventario (todos sus stacks).
        
        Args:
            user_uid: ID del usuario
            ingredient_name: Nombre del ingrediente a eliminar
        """
        print(f"🗑️ [DELETE INGREDIENT COMPLETE] Deleting complete ingredient: {ingredient_name}")
        print(f"   └─ User: {user_uid}")
        
        # Verificar si el ingrediente existe
        existing_stacks = self.inventory_repository.get_all_ingredient_stacks(user_uid, ingredient_name)
        
        if not existing_stacks:
            raise ValueError(f"Ingredient '{ingredient_name}' not found in inventory")
        
        stack_count = len(existing_stacks)
        print(f"   └─ Found {stack_count} stacks to delete")
        
        # Eliminar el ingrediente completo (esto eliminará todos los stacks por CASCADE)
        self.inventory_repository.delete_ingredient_complete(user_uid, ingredient_name)
        
        print(f"✅ [DELETE INGREDIENT COMPLETE] Successfully deleted {ingredient_name} with {stack_count} stacks") 