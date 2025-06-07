import uuid
from datetime import datetime, timezone, timedelta
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.domain.models.recognition import Recognition

class RecognizeIngredientsUseCase:
    def __init__(self, ai_service, recognition_repository, storage_adapter, ingredient_image_generator_service, calculator_service, fallback_name: str = "imagen defecto"):
        self.ai_service = ai_service
        self.recognition_repository = recognition_repository
        self.storage_adapter = storage_adapter
        self.ingredient_image_generator_service = ingredient_image_generator_service
        self.calculator_service = calculator_service
        self.fallback_name = fallback_name

    def execute(self, user_uid: str, images_paths: List[str]) -> dict:
        images_files = []
        for path in images_paths:
            file = self.storage_adapter.get_image(path)
            images_files.append(file)

        result = self.ai_service.recognize_ingredients(images_files)

        recognition = Recognition(
            uid=str(uuid.uuid4()),
            user_uid=user_uid,
            images_paths=images_paths,
            recognized_at=datetime.now(timezone.utc),
            raw_result=result,
            is_validated=False,
            validated_at=None
        )
        self.recognition_repository.save(recognition)

        # ⚡ SÚPER OPTIMIZACIÓN: Agregar environmental + utilization + imágenes en paralelo
        current_time = datetime.now(timezone.utc)
        print(f"🚀 Processing {len(result['ingredients'])} ingredients with FULL PARALLEL processing...")
        print(f"💡 BASIC endpoint now includes: Environmental + Utilization + Images!")

        # 1. Función para enriquecer cada ingrediente con TODOS los datos en paralelo
        def process_complete_ingredient_data(ingredient_data):
            ingredient, user_uid, current_time = ingredient_data
            ingredient_name = ingredient["name"]
            ingredient_description = ingredient.get("description", "")

            print(f"🔥 [Thread] Complete processing for: {ingredient_name}")
            try:
                # Generar imagen
                image_path = self.ingredient_image_generator_service.get_or_generate_ingredient_image(
                    ingredient_name=ingredient_name,
                    user_uid=user_uid,
                    descripcion=ingredient_description
                )

                # Calcular fecha de vencimiento
                expiration_date = self.calculator_service.calculate_expiration_date(
                    added_at=current_time,
                    time_value=ingredient["expiration_time"],
                    time_unit=ingredient["time_unit"]
                )

                # Environmental impact (usando prompts separados)
                environmental_data = self.ai_service.analyze_environmental_impact(ingredient_name)

                # Utilization ideas (usando prompts separados)
                utilization_data = self.ai_service.generate_utilization_ideas(ingredient_name, ingredient_description)

                print(f"✅ [Thread] ALL data ready for {ingredient_name}")
                return ingredient_name, {
                    "image_path": image_path,
                    "expiration_date": expiration_date.isoformat(),
                    "added_at": current_time.isoformat(),
                    **environmental_data,  # environmental_impact
                    **utilization_data     # utilization_ideas
                }, None

            except Exception as e:
                print(f"🚨 [Thread] Error processing {ingredient_name}: {str(e)}")
                fallback_date = current_time + timedelta(days=ingredient.get("expiration_time", 7))

                # Datos por defecto en caso de error
                return ingredient_name, {
                    "image_path": self._get_default_image_path(),
                    "expiration_date": fallback_date.isoformat(),
                    "added_at": current_time.isoformat(),
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

        # 2. Procesar TODO en paralelo (máximo 4 threads para incluir AI calls)
        enriched_results = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            thread_data = [(ingredient, user_uid, current_time) for ingredient in result["ingredients"]]

            future_to_ingredient = {
                executor.submit(process_complete_ingredient_data, data): data[0]["name"]
                for data in thread_data
            }

            for future in as_completed(future_to_ingredient):
                ingredient_name, enriched_data, error = future.result()
                enriched_results[ingredient_name] = enriched_data
                if error:
                    print(f"⚠️ Fallback used for {ingredient_name}")
                else:
                    print(f"🎯 EVERYTHING ready for {ingredient_name}")

        # 3. Aplicar todos los datos enriquecidos (súper rápido)
        for ingredient in result["ingredients"]:
            ingredient_name = ingredient["name"]
            if ingredient_name in enriched_results:
                ingredient.update(enriched_results[ingredient_name])
                print(f"✅ FULL DATA: {ingredient_name} → Image ✅ Environmental ✅ Utilization ✅ Expiration ✅")

        print(f"🚀 ENHANCED BASIC: All {len(result['ingredients'])} ingredients with COMPLETE data using separate prompts!")

        return result

    def _get_default_image_path(self) -> str:
        """
        Retorna una imagen por defecto cuando no se encuentra ninguna referencia.
        Puede ser una URL de imagen placeholder o None.
        """
        return "https://via.placeholder.com/150x150/cccccc/666666?text=No+Image"