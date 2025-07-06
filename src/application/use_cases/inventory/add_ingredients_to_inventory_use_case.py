from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.domain.models.ingredient import Ingredient, IngredientStack

class AddIngredientsToInventoryUseCase:
    def __init__(self, repository, calculator, ai_service=None, ingredient_image_generator_service=None):
        self.repository = repository
        self.calculator = calculator
        self.ai_service = ai_service
        self.ingredient_image_generator_service = ingredient_image_generator_service

    def execute(self, user_uid: str, ingredients_data: list[dict]):
        print(f"🏗️ [ADD INGREDIENTS USE CASE] Starting execution for user: {user_uid}")
        
        inventory = self.repository.get_inventory(user_uid)
        if inventory is None:
            print(f"📝 [ADD INGREDIENTS USE CASE] Creating new inventory for user: {user_uid}")
            self.repository.create_inventory(user_uid)
        else:
            print(f"📋 [ADD INGREDIENTS USE CASE] Using existing inventory for user: {user_uid}")

        now = datetime.now()
        print(f"⏰ [ADD INGREDIENTS USE CASE] Processing timestamp: {now}")
        
        # 🆕 NUEVA FUNCIONALIDAD: Recuperar imágenes faltantes antes de procesar
        if self.ingredient_image_generator_service:
            print(f"🔍 [IMAGE RECOVERY] Checking for missing images and attempting recovery...")
            self._recover_missing_images(ingredients_data, user_uid)
        
        # 🚀 NUEVA FUNCIONALIDAD: Generar environmental impact y utilization ideas solo para ingredientes que van al inventario
        if self.ai_service:
            print(f"🌱 [ADD INGREDIENTS USE CASE] Generating environmental impact and utilization ideas for {len(ingredients_data)} ingredients...")
            self._enrich_ingredients_with_ai_data(ingredients_data)
        else:
            print(f"⚠️ [ADD INGREDIENTS USE CASE] AI service not available, skipping environmental/utilization data generation")
        
        for i, item in enumerate(ingredients_data):
            name = item["name"]
            type_unit = item["type_unit"]
            storage_type = item["storage_type"]
            tips = item["tips"]
            image_path = item["image_path"]
            quantity = item["quantity"]

            print(f"📦 [ADD INGREDIENTS {i+1}] Processing: {name}")
            print(f"   └─ Quantity: {quantity} {type_unit}")
            print(f"   └─ Storage: {storage_type}")
            print(f"   └─ Image: {image_path[:50]}..." if len(image_path) > 50 else f"   └─ Image: {image_path}")

            try:
                # ⭐ MEJORADO: Manejar ambos formatos de fecha de vencimiento
                if "expiration_date" in item and item["expiration_date"]:
                    # Formato de reconocimiento: usar fecha pre-calculada
                    expiration_date_str = item["expiration_date"]
                    if expiration_date_str.endswith('Z'):
                        expiration_date_str = expiration_date_str.replace('Z', '+00:00')
                    expiration_date = datetime.fromisoformat(expiration_date_str)
                    print(f"   └─ ✅ Using pre-calculated expiration: {expiration_date}")
                elif "expiration_time" in item and "time_unit" in item:
                    # Formato manual: calcular fecha de vencimiento
                    expiration_time = item["expiration_time"]
                    time_unit = item["time_unit"]
                    print(f"   └─ Expiration: {expiration_time} {time_unit}")
                    expiration_date = self.calculator.calculate_expiration_date(
                        added_at=now,
                        time_value=expiration_time,
                        time_unit=time_unit
                    )
                    print(f"   └─ ⏳ Calculated new expiration: {expiration_date}")
                else:
                    # Error: falta información de vencimiento
                    raise ValueError(f"Ingredient '{name}' requires either 'expiration_date' or both 'expiration_time' and 'time_unit'")

                ingredient = Ingredient(
                    name=name,
                    type_unit=type_unit,
                    storage_type=storage_type,
                    tips=tips,
                    image_path=image_path
                )

                stack = IngredientStack(
                    quantity=quantity,
                    type_unit=type_unit,
                    expiration_date=expiration_date,
                    added_at=now
                )

                print(f"   └─ 💾 Saving to repository...")
                self.repository.add_ingredient_stack(user_uid, stack, ingredient)
                print(f"   └─ ✅ Successfully saved: {name}")
                
            except Exception as e:
                print(f"   └─ 🚨 Error processing {name}: {str(e)}")
                raise e
        
        print(f"🎉 [ADD INGREDIENTS USE CASE] Successfully processed all {len(ingredients_data)} ingredients")

    def _recover_missing_images(self, ingredients_data: list[dict], user_uid: str):
        """
        🔍 Recupera imágenes faltantes intentando buscar o generar imágenes para ingredientes que no las tienen
        """
        print(f"🔍 [IMAGE RECOVERY] Starting image recovery for {len(ingredients_data)} ingredients")
        
        missing_image_ingredients = []
        for ingredient in ingredients_data:
            image_path = ingredient.get("image_path", "")
            is_placeholder = "placeholder" in image_path.lower() or "via.placeholder" in image_path.lower()
            is_empty = not image_path or image_path.strip() == ""
            
            if is_empty or is_placeholder:
                missing_image_ingredients.append(ingredient)
                print(f"🔍 [IMAGE RECOVERY] Found ingredient without proper image: {ingredient.get('name')}")
                print(f"   └─ Current image_path: '{image_path}'")
        
        if not missing_image_ingredients:
            print(f"✅ [IMAGE RECOVERY] All ingredients already have proper images")
            return
        
        print(f"🎨 [IMAGE RECOVERY] Attempting to recover images for {len(missing_image_ingredients)} ingredients...")
        
        def recover_ingredient_image(ingredient_data):
            ingredient_name = ingredient_data["name"]
            descripcion = ingredient_data.get("description", "")
            
            print(f"🎨 [RECOVERY THREAD] Processing image for: {ingredient_name}")
            try:
                image_path = self.ingredient_image_generator_service.get_or_generate_ingredient_image(
                    ingredient_name=ingredient_name,
                    user_uid=user_uid,
                    descripcion=descripcion
                )
                print(f"✅ [RECOVERY THREAD] Image recovered for {ingredient_name}: {image_path[:50]}...")
                return ingredient_name, image_path, None
            except Exception as e:
                print(f"🚨 [RECOVERY THREAD] Error recovering image for {ingredient_name}: {str(e)}")
                return ingredient_name, "https://via.placeholder.com/150x150/cccccc/666666?text=No+Image", str(e)
        
        # Recuperar imágenes en paralelo
        recovered_images = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_ingredient = {
                executor.submit(recover_ingredient_image, ingredient): ingredient["name"]
                for ingredient in missing_image_ingredients
            }
            
            for future in as_completed(future_to_ingredient):
                ingredient_name, image_path, error = future.result()
                recovered_images[ingredient_name] = image_path
                if error:
                    print(f"⚠️ [IMAGE RECOVERY] Fallback used for {ingredient_name}")
                else:
                    print(f"🖼️ [IMAGE RECOVERY] Image recovered for {ingredient_name}")
        
        # Aplicar las imágenes recuperadas
        for ingredient in ingredients_data:
            ingredient_name = ingredient["name"]
            if ingredient_name in recovered_images:
                old_image_path = ingredient.get("image_path", "")
                new_image_path = recovered_images[ingredient_name]
                ingredient["image_path"] = new_image_path
                print(f"🔄 [IMAGE RECOVERY] Updated image for {ingredient_name}")
                print(f"   └─ Old: {old_image_path[:50]}..." if len(old_image_path) > 50 else f"   └─ Old: {old_image_path}")
                print(f"   └─ New: {new_image_path[:50]}..." if len(new_image_path) > 50 else f"   └─ New: {new_image_path}")
        
        print(f"✅ [IMAGE RECOVERY] Completed image recovery for all ingredients")

    def _enrich_ingredients_with_ai_data(self, ingredients_data: list[dict]):
        """
        Enriquece los ingredientes con environmental impact y utilization ideas usando prompts separados
        """
        print(f"🧠 [AI ENRICHMENT] Starting parallel processing for {len(ingredients_data)} ingredients...")
        
        def enrich_ingredient(ingredient_data):
            ingredient_name = ingredient_data["name"]
            ingredient_description = ingredient_data.get("description", "")
            
            print(f"🔥 [AI Thread] Processing {ingredient_name}")
            try:
                # Environmental impact (prompt separado)
                environmental_data = self.ai_service.analyze_environmental_impact(ingredient_name)
                
                # Utilization ideas (prompt separado)
                utilization_data = self.ai_service.generate_utilization_ideas(ingredient_name, ingredient_description)
                
                print(f"✅ [AI Thread] Enriched {ingredient_name}")
                return ingredient_name, {
                    **environmental_data,  # environmental_impact
                    **utilization_data     # utilization_ideas
                }, None
                
            except Exception as e:
                print(f"🚨 [AI Thread] Error enriching {ingredient_name}: {str(e)}")
                # Datos por defecto en caso de error
                return ingredient_name, {
                    "environmental_impact": {
                        "carbon_footprint": {"value": 0.0, "unit": "kg", "description": "CO2"},
                        "water_footprint": {"value": 0, "unit": "l", "description": "agua"},
                        "sustainability_message": "Consume de manera responsable y evita el desperdicio."
                    },
                    "utilization_ideas": [
                        {
                            "title": "Consume fresco",
                            "description": "Utiliza el ingrediente lo antes posible para aprovechar sus nutrientes.",
                            "type": "conservación"
                        }
                    ]
                }, str(e)
        
        # Procesar en paralelo con máximo 3 threads
        enriched_results = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_ingredient = {
                executor.submit(enrich_ingredient, ingredient): ingredient["name"] 
                for ingredient in ingredients_data
            }
            
            for future in as_completed(future_to_ingredient):
                ingredient_name, enriched_data, error = future.result()
                enriched_results[ingredient_name] = enriched_data
                if error:
                    print(f"⚠️ [AI ENRICHMENT] Fallback used for {ingredient_name}")
                else:
                    print(f"🌱 [AI ENRICHMENT] Success for {ingredient_name}")
        
        # Aplicar los datos enriquecidos a cada ingrediente
        for ingredient in ingredients_data:
            ingredient_name = ingredient["name"]
            if ingredient_name in enriched_results:
                ingredient.update(enriched_results[ingredient_name])
                print(f"💚 [AI ENRICHMENT] Added environmental + utilization data to {ingredient_name}")
        
        print(f"🎯 [AI ENRICHMENT] Completed enrichment for all {len(ingredients_data)} ingredients!")
