class GetIngredientsListUseCase:
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository

    def execute(self, user_uid: str) -> dict:
        """
        Obtiene únicamente la lista de ingredientes del inventario del usuario,
        con información básica de cada ingrediente y sus stacks.
        
        Args:
            user_uid: ID del usuario
            
        Returns:
            dict: Lista de ingredientes con información básica
        """
        print(f"📋 [GET INGREDIENTS LIST] Fetching ingredients list for user: {user_uid}")
        
        # Obtener el inventario completo
        inventory = self.inventory_repository.get_by_user_uid(user_uid)
        
        if not inventory:
            print(f"❌ [GET INGREDIENTS LIST] No inventory found for user: {user_uid}")
            return {
                "ingredients": [],
                "total_ingredients": 0,
                "total_stacks": 0,
                "message": "No inventory found"
            }
        
        ingredients_list = []
        total_stacks = 0
        
        print(f"📊 [GET INGREDIENTS LIST] Found {len(inventory.ingredients)} ingredient types")
        
        for name, ingredient in inventory.ingredients.items():
            # Calcular estadísticas del ingrediente
            total_quantity = sum(stack.quantity for stack in ingredient.stacks)
            stack_count = len(ingredient.stacks)
            total_stacks += stack_count
            
            # Encontrar el stack más próximo a vencer
            nearest_expiration = ingredient.get_nearest_expiration()
            
            # Preparar información de stacks
            stacks_info = []
            for stack in ingredient.stacks:
                from datetime import datetime
                current_time = datetime.now()
                days_to_expire = (stack.expiration_date - current_time).days if stack.expiration_date > current_time else 0
                
                stack_info = {
                    "quantity": stack.quantity,
                    "type_unit": ingredient.type_unit,
                    "expiration_date": stack.expiration_date.isoformat(),
                    "added_at": stack.added_at.isoformat(),
                    "days_to_expire": days_to_expire,
                    "is_expired": stack.expiration_date < current_time
                }
                stacks_info.append(stack_info)
            
            # Crear información del ingrediente
            ingredient_info = {
                "name": ingredient.name,
                "type_unit": ingredient.type_unit,
                "storage_type": ingredient.storage_type,
                "tips": ingredient.tips,
                "image_path": ingredient.image_path,
                "stacks": stacks_info,
                
                # Estadísticas calculadas
                "total_quantity": total_quantity,
                "stack_count": stack_count,
                "nearest_expiration": nearest_expiration.isoformat() if nearest_expiration else None,
                "average_quantity_per_stack": total_quantity / stack_count if stack_count > 0 else 0
            }
            
            ingredients_list.append(ingredient_info)
            
            print(f"   • {name}: {stack_count} stacks, total: {total_quantity} {ingredient.type_unit}")
        
        # Ordenar por nombre para consistencia
        ingredients_list.sort(key=lambda x: x['name'])
        
        result = {
            "ingredients": ingredients_list,
            "total_ingredients": len(ingredients_list),
            "total_stacks": total_stacks,
            "summary": {
                "ingredient_types": len(ingredients_list),
                "total_stacks": total_stacks,
                "average_stacks_per_ingredient": total_stacks / len(ingredients_list) if len(ingredients_list) > 0 else 0
            }
        }
        
        print(f"✅ [GET INGREDIENTS LIST] Successfully prepared list: {len(ingredients_list)} ingredients, {total_stacks} total stacks")
        return result 