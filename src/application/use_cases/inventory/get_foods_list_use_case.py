class GetFoodsListUseCase:
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository

    def execute(self, user_uid: str) -> dict:
        """
        Obtiene únicamente la lista de food items del inventario del usuario,
        con información básica de cada comida preparada.
        
        Args:
            user_uid: ID del usuario
            
        Returns:
            dict: Lista de food items con información básica
        """
        print(f"🍽️ [GET FOODS LIST] Fetching foods list for user: {user_uid}")
        
        # Obtener todos los food items del usuario
        food_items_data = self.inventory_repository.get_all_food_items(user_uid)
        
        if not food_items_data:
            print(f"❌ [GET FOODS LIST] No food items found for user: {user_uid}")
            return {
                "foods": [],
                "total_foods": 0,
                "total_servings": 0,
                "total_calories": 0,
                "message": "No food items found"
            }
        
        foods_list = []
        total_servings = 0
        total_calories = 0
        
        print(f"📊 [GET FOODS LIST] Found {len(food_items_data)} food items")
        
        for food_data in food_items_data:
            from datetime import datetime
            
            # Calcular días hasta vencimiento
            current_time = datetime.now()
            expiration_date = food_data['expiration_date']
            added_at_date = food_data['added_at']
            
            if isinstance(expiration_date, str):
                expiration_date = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
            if isinstance(added_at_date, str):
                added_at_date = datetime.fromisoformat(added_at_date.replace('Z', '+00:00'))
                
            days_to_expire = (expiration_date - current_time).days
            is_expired = expiration_date < current_time
            
            # Calcular estadísticas
            serving_quantity = food_data['serving_quantity']
            calories = food_data['calories']
            calories_per_serving = calories / max(serving_quantity, 1)
            total_item_calories = calories * serving_quantity
            
            total_servings += serving_quantity
            total_calories += total_item_calories
            
            # Crear información del food item
            food_info = {
                "name": food_data['name'],
                "category": food_data['category'],
                "serving_quantity": serving_quantity,
                "calories": calories,
                "description": food_data['description'],
                "storage_type": food_data['storage_type'],
                "tips": food_data['tips'],
                "image_path": food_data['image_path'],
                
                # Fechas y tiempo
                "added_at": added_at_date.isoformat(),
                "expiration_date": expiration_date.isoformat(),
                "expiration_time": food_data['expiration_time'],
                "time_unit": food_data['time_unit'],
                "days_to_expire": max(days_to_expire, 0),
                "is_expired": is_expired,
                
                # Ingredientes principales
                "main_ingredients": food_data['main_ingredients'],
                
                # Estadísticas calculadas
                "calories_per_serving": calories_per_serving,
                "total_calories": total_item_calories,
                
                # Estado del item
                "status": "expired" if is_expired else ("expiring_soon" if days_to_expire <= 1 else "fresh")
            }
            
            foods_list.append(food_info)
            
            print(f"   • {food_data['name']}: {serving_quantity} servings, {total_item_calories} total calories, expires in {days_to_expire} days")
        
        # Ordenar por fecha de vencimiento (más próximos primero) y luego por nombre
        foods_list.sort(key=lambda x: (x['expiration_date'], x['name']))
        
        # Calcular estadísticas de categorías
        categories_summary = {}
        for food in foods_list:
            category = food['category']
            if category not in categories_summary:
                categories_summary[category] = {
                    "count": 0,
                    "total_servings": 0,
                    "total_calories": 0
                }
            categories_summary[category]["count"] += 1
            categories_summary[category]["total_servings"] += food['serving_quantity']
            categories_summary[category]["total_calories"] += food['total_calories']
        
        result = {
            "foods": foods_list,
            "total_foods": len(foods_list),
            "total_servings": total_servings,
            "total_calories": total_calories,
            "summary": {
                "food_items": len(foods_list),
                "total_servings": total_servings,
                "total_calories": total_calories,
                "average_calories_per_food": total_calories / len(foods_list) if len(foods_list) > 0 else 0,
                "average_servings_per_food": total_servings / len(foods_list) if len(foods_list) > 0 else 0,
                "categories": categories_summary
            }
        }
        
        print(f"✅ [GET FOODS LIST] Successfully prepared list: {len(foods_list)} food items, {total_servings} total servings")
        return result 