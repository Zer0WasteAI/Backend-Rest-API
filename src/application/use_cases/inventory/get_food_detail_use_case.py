class GetFoodDetailUseCase:
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository

    def execute(self, user_uid: str, food_name: str, added_at: str) -> dict:
        """
        Obtiene todos los detalles de un food item específico del inventario,
        incluyendo ingredientes principales, valores nutricionales, consejos y más.
        
        Args:
            user_uid: ID del usuario
            food_name: Nombre de la comida
            added_at: Timestamp de cuando se agregó
            
        Returns:
            dict: Información completa del food item
        """
        print(f"🍽️ [GET FOOD DETAIL] Fetching food item: {food_name}")
        print(f"   └─ User: {user_uid}")
        print(f"   └─ Added at: {added_at}")
        
        # Obtener el food item específico
        food_item_data = self.inventory_repository.get_food_item(user_uid, food_name, added_at)
        
        if not food_item_data:
            raise ValueError(f"Food item '{food_name}' added at '{added_at}' not found in inventory")
        
        print(f"   └─ Found food item with {food_item_data['serving_quantity']} servings")
        
        # Construir información completa del food item
        from datetime import datetime
        
        # Calcular días hasta vencimiento
        expiration_date = food_item_data['expiration_date']
        added_at_date = food_item_data['added_at']
        current_date = datetime.now()
        
        if isinstance(expiration_date, str):
            expiration_date = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
        if isinstance(added_at_date, str):
            added_at_date = datetime.fromisoformat(added_at_date.replace('Z', '+00:00'))
            
        days_to_expire = (expiration_date - current_date).days
        
        food_detail = {
            # Información básica
            "name": food_item_data['name'],
            "category": food_item_data['category'],
            "serving_quantity": food_item_data['serving_quantity'],
            "calories": food_item_data['calories'],
            "description": food_item_data['description'],
            "storage_type": food_item_data['storage_type'],
            "tips": food_item_data['tips'],
            "image_path": food_item_data['image_path'],
            
            # Fechas y tiempo
            "added_at": added_at_date.isoformat(),
            "expiration_date": expiration_date.isoformat(),
            "expiration_time": food_item_data['expiration_time'],
            "time_unit": food_item_data['time_unit'],
            "days_to_expire": max(days_to_expire, 0),
            "is_expired": days_to_expire < 0,
            
            # Ingredientes
            "main_ingredients": food_item_data['main_ingredients'],
            
            # Estadísticas calculadas
            "calories_per_serving": food_item_data['calories'] / max(food_item_data['serving_quantity'], 1),
            "total_calories": food_item_data['calories'] * food_item_data['serving_quantity']
        }
        
        # Enriquecer con IA si es posible
        try:
            from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
            ai_service = GeminiAdapterService()
            
            print(f"🤖 [GET FOOD DETAIL] Enriching {food_name} with AI data...")
            
            # Generar análisis nutricional avanzado
            nutritional_analysis = ai_service.analyze_food_nutrition(
                food_name=food_item_data['name'],
                description=food_item_data['description'],
                main_ingredients=food_item_data['main_ingredients'],
                calories=food_item_data['calories']
            )
            food_detail["nutritional_analysis"] = nutritional_analysis.get("nutritional_analysis", {})
            
            # Generar ideas de consumo y acompañamiento
            consumption_ideas = ai_service.generate_food_consumption_ideas(
                food_name=food_item_data['name'],
                category=food_item_data['category'],
                main_ingredients=food_item_data['main_ingredients']
            )
            food_detail["consumption_ideas"] = consumption_ideas.get("consumption_ideas", [])
            
            # Consejos de recalentamiento y conservación
            storage_advice = ai_service.generate_food_storage_advice(
                food_name=food_item_data['name'],
                storage_type=food_item_data['storage_type'],
                expiration_time=food_item_data['expiration_time']
            )
            food_detail["storage_advice"] = storage_advice.get("storage_advice", {})
            
            print(f"✅ [GET FOOD DETAIL] Successfully enriched {food_name}")
            
        except Exception as e:
            print(f"⚠️ [GET FOOD DETAIL] Error enriching {food_name}: {str(e)}")
            # Datos por defecto en caso de error de IA
            food_detail["nutritional_analysis"] = {
                "macronutrients": {
                    "carbohydrates": "Información no disponible",
                    "proteins": "Información no disponible", 
                    "fats": "Información no disponible"
                },
                "vitamins_minerals": ["Consulta información nutricional específica"],
                "health_benefits": "Proporciona energía y nutrientes esenciales",
                "dietary_considerations": "Consulta con un nutricionista si tienes restricciones alimentarias"
            }
            food_detail["consumption_ideas"] = [
                {
                    "title": "Consume solo",
                    "description": "Disfruta esta comida tal como está preparada.",
                    "type": "individual"
                },
                {
                    "title": "Acompañar con ensalada",
                    "description": "Complementa con una ensalada fresca para mayor balance nutricional.",
                    "type": "acompañamiento"
                }
            ]
            food_detail["storage_advice"] = {
                "optimal_temperature": "Mantén refrigerado si es perecedero",
                "reheating_tips": "Recalienta completamente antes de consumir",
                "shelf_life_extension": "Consume antes de la fecha de vencimiento",
                "quality_indicators": "Verifica olor, color y textura antes de consumir"
            }
        
        # Agregar metadatos de enriquecimiento
        food_detail["enriched_with"] = [
            "nutritional_analysis",
            "consumption_ideas", 
            "storage_advice",
            "statistics"
        ]
        food_detail["fetched_at"] = current_date.isoformat()
        
        print(f"✅ [GET FOOD DETAIL] Successfully prepared complete detail for {food_name}")
        return food_detail 