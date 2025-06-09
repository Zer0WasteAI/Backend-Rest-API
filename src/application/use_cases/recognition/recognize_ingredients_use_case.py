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

        # ⚡ OPTIMIZACIÓN: Generar imágenes en paralelo para acelerar el proceso
        current_time = datetime.now(timezone.utc)
        print(f"🚀 Processing {len(result['ingredients'])} ingredients with parallel image generation...")
        print(f"📝 BASIC endpoint: Recognition data + Images only (Environmental/Utilization will be generated when adding to inventory)")

        # 1. Función para generar imágenes en paralelo
        def process_ingredient_image(ingredient_data):
            ingredient, user_uid = ingredient_data
            ingredient_name = ingredient["name"]
            descripcion = ingredient.get("description", "")

            print(f"🎨 [Thread] Processing image for: {ingredient_name}")
            try:
                image_path = self.ingredient_image_generator_service.get_or_generate_ingredient_image(
                    ingredient_name=ingredient_name,
                    user_uid=user_uid,
                    descripcion=descripcion
                )
                print(f"✅ [Thread] Image ready for {ingredient_name}: {image_path[:50]}...")
                return ingredient_name, image_path, None
            except Exception as e:
                print(f"🚨 [Thread] Error with image for {ingredient_name}: {str(e)}")
                return ingredient_name, self._get_default_image_path(), str(e)

        # 2. Ejecutar generación de imágenes en paralelo
        ingredient_images = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            thread_data = [(ingredient, user_uid) for ingredient in result["ingredients"]]
            
            future_to_ingredient = {
                executor.submit(process_ingredient_image, data): data[0]["name"]
                for data in thread_data
            }
            
            for future in as_completed(future_to_ingredient):
                ingredient_name, image_path, error = future.result()
                ingredient_images[ingredient_name] = image_path
                if error:
                    print(f"⚠️ Image fallback used for {ingredient_name}")
                else:
                    print(f"🖼️ Image ready for {ingredient_name}")

        # 3. Finalizar procesamiento de cada ingrediente
        for ingredient in result["ingredients"]:
            ingredient_name = ingredient["name"]
            print(f"📋 Finalizing basic data for ingredient: {ingredient_name}")

            # Asignar imagen generada en paralelo
            ingredient["image_path"] = ingredient_images.get(ingredient_name, self._get_default_image_path())

            # ⭐ Calcular fecha de vencimiento
            try:
                expiration_date = self.calculator_service.calculate_expiration_date(
                    added_at=current_time,
                    time_value=ingredient["expiration_time"],
                    time_unit=ingredient["time_unit"]
                )
                ingredient["expiration_date"] = expiration_date.isoformat()
                print(f"📅 Expiration calculated for {ingredient_name}: {expiration_date}")

            except Exception as e:
                print(f"🚨 Error calculating expiration for {ingredient_name}: {str(e)}")
                fallback_date = current_time + timedelta(days=ingredient.get("expiration_time", 7))
                ingredient["expiration_date"] = fallback_date.isoformat()

            # ⭐ Agregar timestamp
            ingredient["added_at"] = current_time.isoformat()
            print(f"✅ Basic data ready for {ingredient_name}: Image ✅ | Expiration ✅")

        print(f"🎉 All {len(result['ingredients'])} ingredients processed with optimized recognition flow!")

        return result
    
    def _get_default_image_path(self) -> str:
        """
        Retorna una imagen por defecto cuando no se encuentra ninguna referencia.
        Puede ser una URL de imagen placeholder o None.
        """
        return "https://via.placeholder.com/150x150/cccccc/666666?text=No+Image"