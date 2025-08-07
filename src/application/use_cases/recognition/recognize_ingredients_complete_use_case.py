import uuid
from datetime import datetime, timezone, timedelta
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from src.domain.models.recognition import Recognition

class RecognizeIngredientsCompleteUseCase:
    def __init__(self, ai_service, recognition_repository, storage_adapter, ingredient_image_generator_service, calculator_service, fallback_name: str = "imagen defecto"):
        self.ai_service = ai_service
        self.recognition_repository = recognition_repository
        self.storage_adapter = storage_adapter
        self.ingredient_image_generator_service = ingredient_image_generator_service
        self.calculator_service = calculator_service
        self.fallback_name = fallback_name

    def execute(self, user_uid: str, images_paths: List[str]) -> dict:
        """
        Ejecuta reconocimiento completo de ingredientes con toda la información:
        - Datos básicos (nombre, cantidad, descripción, etc.)
        - Impacto ambiental (CO2, agua)
        - Ideas de aprovechamiento
        - Imágenes generadas/asignadas
        - Fechas de vencimiento calculadas
        """
        images_files = []
        for path in images_paths:
            file = self.storage_adapter.get_image(path)
            images_files.append(file)

        # Usar el nuevo méto/do de reconocimiento completo (ya incluye environmental + utilization en paralelo)
        result = self.ai_service.recognize_ingredients_complete(images_files)
        print(f"🎯 AI processing complete for {len(result['ingredients'])} ingredients")

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

        # ⚡ SUPER OPTIMIZACIÓN: Procesar imágenes Y datos finales en paralelo total
        current_time = datetime.now(timezone.utc)
        print(f"🚀 Final processing for {len(result['ingredients'])} ingredients with MAXIMUM parallelization...")
        
        # 1. Función para procesar TO/DO de cada ingrediente en paralelo
        def process_complete_ingredient(ingredient_data):
            ingredient, user_uid, current_time = ingredient_data
            ingredient_name = ingredient["name"]
            descripcion = ingredient.get("description", "")
            
            print(f"🔥 [Thread] Complete processing for: {ingredient_name}")
            try:
                # Generar imagen
                image_path = self.ingredient_image_generator_service.get_or_generate_ingredient_image(
                    ingredient_name=ingredient_name,
                    user_uid=user_uid,
                    descripcion=descripcion
                )
                
                # Calcular fecha de vencimiento
                expiration_date = self.calculator_service.calculate_expiration_date(
                    added_at=current_time,
                    time_value=ingredient["expiration_time"],
                    time_unit=ingredient["time_unit"]
                )
                
                print(f"✅ [Thread] Complete data ready for {ingredient_name}")
                return ingredient_name, {
                    "image_path": image_path,
                    "expiration_date": expiration_date.isoformat(),
                    "added_at": current_time.isoformat()
                }, None
                
            except Exception as e:
                print(f"🚨 [Thread] Error processing {ingredient_name}: {str(e)}")
                fallback_date = current_time + timedelta(days=ingredient.get("expiration_time", 7))
                return ingredient_name, {
                    "image_path": self._get_default_image_path(),
                    "expiration_date": fallback_date.isoformat(),
                    "added_at": current_time.isoformat()
                }, str(e)
        
        # 2. Procesar TO/DO en paralelo (máximo 3 threads)
        final_results = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            thread_data = [(ingredient, user_uid, current_time) for ingredient in result["ingredients"]]
            
            future_to_ingredient = {
                executor.submit(process_complete_ingredient, data): data[0]["name"] 
                for data in thread_data
            }
            
            for future in as_completed(future_to_ingredient):
                ingredient_name, final_data, error = future.result()
                final_results[ingredient_name] = final_data
                if error:
                    print(f"⚠️ Fallback used for {ingredient_name}")
                else:
                    print(f"🎯 Everything ready for {ingredient_name}")
        
        # 3. Aplicar resultados finales (súper rápido)
        for ingredient in result["ingredients"]:
            ingredient_name = ingredient["name"]
            if ingredient_name in final_results:
                ingredient.update(final_results[ingredient_name])
                print(f"✅ COMPLETE: {ingredient_name} → Image ✅ Environmental ✅ Utilization ✅ Expiration ✅")
        
        print(f"🚀 ULTRA-FAST: All {len(result['ingredients'])} ingredients ready with maximum parallelization!")

        return result
    
    def _get_default_image_path(self) -> str:
        """
        Retorna una imagen por defecto cuando no se encuentra ninguna referencia.
        Puede ser una URL de imagen placeholder o None.
        """
        return "https://via.placeholder.com/150x150/cccccc/666666?text=No+Image" 