from datetime import datetime, timezone
from typing import Dict, Any
from src.domain.models.ingredient import Ingredient, IngredientStack
from src.domain.models.food_item import FoodItem


class AddItemToInventoryUseCase:
    """Caso de uso unificado para agregar items al inventario con enriquecimiento de IA"""
    
    def __init__(self, inventory_repository, calculator_service, ai_service):
        self.inventory_repository = inventory_repository
        self.calculator_service = calculator_service
        self.ai_service = ai_service
    
    def execute(self, user_uid: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agrega un item (ingrediente o comida) al inventario del usuario.
        
        Args:
            user_uid: UID del usuario
            item_data: Datos del item desde el frontend
                - name: nombre del item (required)
                - quantity: cantidad (required)
                - unit: unidad de cantidad (required)
                - storage_type: tipo de almacenamiento (required)
                - category: 'ingredient' o 'food' (required)
                - image_url: URL de la imagen (optional, nullable)
                
        Returns:
            Dict con información del item agregado
        """
        print(f"🎯 [ADD ITEM] Starting execution for user: {user_uid}")
        print(f"   └─ Item: {item_data.get('name')}")
        print(f"   └─ Category: {item_data.get('category')}")
        print(f"   └─ Quantity: {item_data.get('quantity')} {item_data.get('unit')}")
        
        # Validar datos básicos
        self._validate_basic_data(item_data)
        
        # Obtener o crear inventario
        inventory = self.inventory_repository.get_by_user_uid(user_uid)
        if not inventory:
            print(f"   └─ 📝 Creating new inventory for user")
            self.inventory_repository.save(self._create_empty_inventory(user_uid))
        
        # Procesar según el tipo de item
        category = item_data['category'].lower()
        now = datetime.now(timezone.utc)
        
        if category == 'ingredient':
            return self._add_ingredient(user_uid, item_data, now)
        elif category == 'food':
            return self._add_food(user_uid, item_data, now)
        else:
            raise ValueError(f"Invalid category: {category}. Must be 'ingredient' or 'food'")
    
    def _validate_basic_data(self, item_data: Dict[str, Any]) -> None:
        """Valida que los datos básicos estén presentes"""
        required_fields = ['name', 'quantity', 'unit', 'storage_type', 'category']
        
        for field in required_fields:
            if field not in item_data or item_data[field] is None:
                raise ValueError(f"Field '{field}' is required")
        
        # Validar tipos específicos
        if not isinstance(item_data['quantity'], (int, float)) or item_data['quantity'] <= 0:
            raise ValueError("Quantity must be a positive number")
        
        if item_data['category'].lower() not in ['ingredient', 'food']:
            raise ValueError("Category must be 'ingredient' or 'food'")
    
    def _add_ingredient(self, user_uid: str, item_data: Dict[str, Any], now: datetime) -> Dict[str, Any]:
        """Agrega un ingrediente al inventario con enriquecimiento de IA"""
        print(f"🥬 [ADD INGREDIENT] Processing ingredient: {item_data['name']}")
        
        # Enriquecer datos con IA
        enriched_data = self._enrich_ingredient_with_ai(item_data)
        print(f"   └─ ✨ AI enrichment completed")
        
        # Calcular fecha de vencimiento
        expiration_date = self.calculator_service.calculate_expiration_date(
            now, 
            enriched_data.get('expiration_time', 7),  # Default 7 días
            enriched_data.get('time_unit', 'days')    # Default días
        )
        print(f"   └─ ⏳ Expiration calculated: {expiration_date}")
        
        # Crear stack del ingrediente
        stack = IngredientStack(
            quantity=item_data['quantity'],
            type_unit=item_data['unit'],
            added_at=now,
            expiration_date=expiration_date
        )
        
        # Crear ingrediente (manejando nulos correctamente)
        tips = enriched_data.get('tips')
        if tips is None:
            tips = ''  # Ingredient model expects string, not null
            
        ingredient = Ingredient(
            name=item_data['name'],
            type_unit=item_data['unit'],
            storage_type=item_data['storage_type'],
            tips=tips,
            image_path=item_data.get('image_url', '') or ''
        )
        
        # Guardar en repositorio
        self.inventory_repository.add_ingredient_stack(user_uid, stack, ingredient)
        print(f"   └─ ✅ Ingredient saved successfully")
        
        return {
            "message": "Ingredient added successfully",
            "item_type": "ingredient",
            "item_data": {
                "name": ingredient.name,
                "quantity": stack.quantity,
                "unit": stack.type_unit,
                "storage_type": ingredient.storage_type,
                "expiration_date": expiration_date.isoformat(),
                "tips": enriched_data.get('tips') or ingredient.tips,  # Show enriched or fallback
                "image_path": ingredient.image_path,
                "environmental_impact": enriched_data.get('environmental_impact'),
                "utilization_ideas": enriched_data.get('utilization_ideas'),
                "enriched_fields": list(enriched_data.keys())
            }
        }
    
    def _add_food(self, user_uid: str, item_data: Dict[str, Any], now: datetime) -> Dict[str, Any]:
        """Agrega una comida al inventario con enriquecimiento de IA"""
        print(f"🍽️ [ADD FOOD] Processing food: {item_data['name']}")
        
        # Enriquecer datos con IA
        enriched_data = self._enrich_food_with_ai(item_data)
        print(f"   └─ ✨ AI enrichment completed")
        
        # Calcular fecha de vencimiento
        expiration_date = self.calculator_service.calculate_expiration_date(
            now,
            enriched_data.get('expiration_time', 3),  # Default 3 días para comidas
            enriched_data.get('time_unit', 'days')    # Default días
        )
        print(f"   └─ ⏳ Expiration calculated: {expiration_date}")
        
        # Crear food item (manejando nulos correctamente)
        main_ingredients = enriched_data.get('main_ingredients')
        if main_ingredients is None:
            main_ingredients = []  # FoodItem model expects list, not null
            
        description = enriched_data.get('description')
        if description is None:
            description = ''  # FoodItem model expects string, not null
            
        tips = enriched_data.get('tips')
        if tips is None:
            tips = ''  # FoodItem model expects string, not null
        
        food_item = FoodItem(
            name=item_data['name'],
            main_ingredients=main_ingredients,
            category=enriched_data.get('food_category', 'otros'),
            calories=enriched_data.get('calories'),
            description=description,
            storage_type=item_data['storage_type'],
            expiration_time=enriched_data.get('expiration_time', 3),
            time_unit=enriched_data.get('time_unit', 'days'),
            tips=tips,
            serving_quantity=item_data['quantity'],  # La cantidad se usa como serving_quantity
            image_path=item_data.get('image_url', '') or '',
            added_at=now,
            expiration_date=expiration_date
        )
        
        # Guardar en repositorio
        self.inventory_repository.add_food_item(user_uid, food_item)
        print(f"   └─ ✅ Food saved successfully")
        
        return {
            "message": "Food added successfully",
            "item_type": "food",
            "item_data": {
                "name": food_item.name,
                "serving_quantity": food_item.serving_quantity,
                "storage_type": food_item.storage_type,
                "expiration_date": expiration_date.isoformat(),
                "main_ingredients": enriched_data.get('main_ingredients'),  # Show original (nullable) value
                "category": food_item.category,
                "calories": food_item.calories,
                "description": enriched_data.get('description'),  # Show original (nullable) value
                "tips": enriched_data.get('tips') or food_item.tips,  # Show enriched or fallback
                "image_path": food_item.image_path,
                "nutritional_analysis": enriched_data.get('nutritional_analysis'),
                "consumption_ideas": enriched_data.get('consumption_ideas'),
                "enriched_fields": list(enriched_data.keys())
            }
        }
    
    def _enrich_ingredient_with_ai(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquece datos del ingrediente usando IA"""
        try:
            print(f"   └─ 🤖 Generating AI data for ingredient: {item_data['name']}")
            
            # Usar el servicio de IA para generar datos del ingrediente
            ai_data = self.ai_service.generate_ingredient_data(
                ingredient_name=item_data['name'],
                storage_type=item_data['storage_type']
            )
            
            # Estructura esperada del AI service para ingredientes
            enriched = {
                'tips': ai_data.get('tips', ''),
                'expiration_time': ai_data.get('expiration_time', 7),
                'time_unit': ai_data.get('time_unit', 'days'),
                'environmental_impact': ai_data.get('environmental_impact', ''),
                'utilization_ideas': ai_data.get('utilization_ideas', [])
            }
            
            print(f"      └─ Generated tips: {len(enriched['tips'])} chars")
            print(f"      └─ Expiration: {enriched['expiration_time']} {enriched['time_unit']}")
            
            return enriched
            
        except Exception as e:
            print(f"   └─ ⚠️ AI enrichment failed: {str(e)}")
            # Retornar datos por defecto si falla la IA
            return {
                'tips': 'Almacenar en lugar fresco y seco.',
                'expiration_time': 7,
                'time_unit': 'days',
                'environmental_impact': None,  # Explicitly null when AI fails
                'utilization_ideas': None      # Explicitly null when AI fails
            }
    
    def _enrich_food_with_ai(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquece datos de la comida usando IA"""
        try:
            print(f"   └─ 🤖 Generating AI data for food: {item_data['name']}")
            
            # Usar el servicio de IA para generar datos de la comida
            ai_data = self.ai_service.generate_food_data(
                food_name=item_data['name'],
                storage_type=item_data['storage_type']
            )
            
            # Estructura esperada del AI service para comidas
            enriched = {
                'main_ingredients': ai_data.get('main_ingredients', []),
                'food_category': ai_data.get('category', 'otros'),
                'calories': ai_data.get('calories'),
                'description': ai_data.get('description', ''),
                'tips': ai_data.get('tips', ''),
                'expiration_time': ai_data.get('expiration_time', 3),
                'time_unit': ai_data.get('time_unit', 'days'),
                'nutritional_analysis': ai_data.get('nutritional_analysis', ''),
                'consumption_ideas': ai_data.get('consumption_ideas', [])
            }
            
            print(f"      └─ Generated main ingredients: {len(enriched['main_ingredients'])}")
            print(f"      └─ Category: {enriched['food_category']}")
            print(f"      └─ Calories: {enriched['calories']}")
            
            return enriched
            
        except Exception as e:
            print(f"   └─ ⚠️ AI enrichment failed: {str(e)}")
            # Retornar datos por defecto si falla la IA
            return {
                'main_ingredients': None,        # Explicitly null when AI fails
                'food_category': 'otros',
                'calories': None,               # Explicitly null when AI fails
                'description': None,            # Explicitly null when AI fails
                'tips': 'Refrigerar y consumir pronto.',
                'expiration_time': 3,
                'time_unit': 'days',
                'nutritional_analysis': None,   # Explicitly null when AI fails
                'consumption_ideas': None       # Explicitly null when AI fails
            }
    
    def _create_empty_inventory(self, user_uid: str):
        """Crea un inventario vacío para el usuario"""
        from src.domain.models.inventory import Inventory
        return Inventory(user_uid=user_uid) 