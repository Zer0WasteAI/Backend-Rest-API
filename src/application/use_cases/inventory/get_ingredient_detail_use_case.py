class GetIngredientDetailUseCase:
    def __init__(self, inventory_repository):
        self.inventory_repository = inventory_repository

    def execute(self, user_uid: str, ingredient_name: str) -> dict:
        """
        Obtiene todos los detalles de un ingrediente específico del inventario,
        incluyendo todos sus stacks, imagen, impacto ambiental y ideas de aprovechamiento.
        
        Args:
            user_uid: ID del usuario
            ingredient_name: Nombre del ingrediente
            
        Returns:
            dict: Información completa del ingrediente con datos enriquecidos
        """
        print(f"🔍 [GET INGREDIENT DETAIL] Fetching ingredient: {ingredient_name}")
        print(f"   └─ User: {user_uid}")
        
        # Obtener el inventario completo para acceder al ingrediente
        inventory = self.inventory_repository.get_by_user_uid(user_uid)
        
        if not inventory:
            raise ValueError(f"Inventory not found for user")
        
        # Buscar el ingrediente específico
        ingredient = inventory.ingredients.get(ingredient_name)
        
        if not ingredient:
            raise ValueError(f"Ingredient '{ingredient_name}' not found in inventory")
        
        print(f"   └─ Found ingredient with {len(ingredient.stacks)} stacks")
        
        # Construir información básica del ingrediente
        ingredient_detail = {
            "name": ingredient.name,
            "type_unit": ingredient.type_unit,
            "storage_type": ingredient.storage_type,
            "tips": ingredient.tips,
            "image_path": ingredient.image_path,
            "stacks": []
        }
        
        # Agregar todos los stacks con sus detalles
        total_quantity = 0
        for stack in ingredient.stacks:
            stack_info = {
                "quantity": stack.quantity,
                "type_unit": ingredient.type_unit,
                "expiration_date": stack.expiration_date.isoformat(),
                "added_at": stack.added_at.isoformat(),
                "days_to_expire": (stack.expiration_date - stack.added_at).days if stack.expiration_date > stack.added_at else 0,
                "is_expired": stack.expiration_date < stack.added_at
            }
            ingredient_detail["stacks"].append(stack_info)
            total_quantity += stack.quantity
        
        # Agregar estadísticas calculadas
        ingredient_detail["total_quantity"] = total_quantity
        ingredient_detail["stack_count"] = len(ingredient.stacks)
        ingredient_detail["nearest_expiration"] = ingredient.get_nearest_expiration().isoformat() if ingredient.get_nearest_expiration() else None
        
        # Enriquecer con IA
        try:
            from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
            ai_service = GeminiAdapterService()
            
            print(f"🤖 [GET INGREDIENT DETAIL] Enriching {ingredient_name} with AI data...")
            
            # Obtener impacto ambiental
            environmental_data = ai_service.analyze_environmental_impact(ingredient.name)
            ingredient_detail["environmental_impact"] = environmental_data.get("environmental_impact", {})
            
            # Obtener ideas de aprovechamiento
            utilization_data = ai_service.generate_utilization_ideas(ingredient.name, ingredient.tips)
            ingredient_detail["utilization_ideas"] = utilization_data.get("utilization_ideas", [])
            
            # Obtener consejos de consumo
            consumption_data = ai_service.generate_consumption_advice(ingredient.name, ingredient.tips)
            ingredient_detail["consumption_advice"] = consumption_data.get("consumption_advice", {})
            ingredient_detail["before_consumption_advice"] = consumption_data.get("before_consumption_advice", {})
            
            print(f"✅ [GET INGREDIENT DETAIL] Successfully enriched {ingredient_name}")
            
        except Exception as e:
            print(f"⚠️ [GET INGREDIENT DETAIL] Error enriching {ingredient_name}: {str(e)}")
            # Datos por defecto en caso de error de IA
            ingredient_detail["environmental_impact"] = {
                "carbon_footprint": {"value": 0.5, "unit": "kg", "description": "CO2 estimado"},
                "water_footprint": {"value": 100, "unit": "l", "description": "agua estimada"},
                "sustainability_message": "Consume de manera responsable y evita el desperdicio."
            }
            ingredient_detail["utilization_ideas"] = [
                {
                    "title": "Consume fresco",
                    "description": "Utiliza el ingrediente lo antes posible para aprovechar sus nutrientes.",
                    "type": "conservación"
                }
            ]
            ingredient_detail["consumption_advice"] = {
                "optimal_consumption": "Consume fresco para aprovechar al máximo sus nutrientes.",
                "preparation_tips": "Lava bien antes de consumir y mantén refrigerado.",
                "nutritional_benefits": "Rico en vitaminas y minerales esenciales."
            }
            ingredient_detail["before_consumption_advice"] = {
                "quality_check": "Verifica que esté fresco y sin signos de deterioro.",
                "safety_tips": "Lava con agua corriente antes de consumir."
            }
        
        # Agregar metadatos de enriquecimiento
        ingredient_detail["enriched_with"] = [
            "environmental_impact", 
            "utilization_ideas", 
            "consumption_advice", 
            "before_consumption_advice",
            "statistics"
        ]
        from datetime import datetime
        ingredient_detail["fetched_at"] = datetime.now().isoformat()
        
        print(f"✅ [GET INGREDIENT DETAIL] Successfully prepared complete detail for {ingredient_name}")
        return ingredient_detail 