import uuid
from datetime import datetime, timezone, timedelta
from typing import List
from src.domain.models.recognition import Recognition

class RecognizeIngredientsUseCase:
    def __init__(self, ai_service, recognition_repository, storage_adapter, image_repository, ingredient_image_generator_service, calculator_service, fallback_name: str = "imagen defecto"):
        self.ai_service = ai_service
        self.recognition_repository = recognition_repository
        self.storage_adapter = storage_adapter
        self.image_repository = image_repository
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

        # Enhanced logic: Generate or retrieve images for each ingredient
        current_time = datetime.now(timezone.utc)
        
        for ingredient in result["ingredients"]:
            print(f"🔍 Processing image for ingredient: {ingredient['name']}")
            
            # First try to find existing image using similarity search
            similars = self.image_repository.find_by_name_similarity(ingredient["name"])
            if similars:
                print(f"✅ Found existing image reference for {ingredient['name']}")
                ingredient["image_path"] = similars[0].image_path
            else:
                print(f"🆕 No existing image reference, using image generator service")
                # Use the new image generation service
                try:
                    ingredient["image_path"] = self.ingredient_image_generator_service.get_or_generate_ingredient_image(
                        ingredient_name=ingredient["name"],
                        user_uid=user_uid
                    )
                except Exception as e:
                    print(f"🚨 Error generating image for {ingredient['name']}: {str(e)}")
                    # Fallback to default logic
                    fallback_image = self.image_repository.find_by_name(self.fallback_name)
                    if fallback_image:
                        ingredient["image_path"] = fallback_image.image_path
                    else:
                        ingredient["image_path"] = self._get_default_image_path()
            
            # ⭐ NUEVO: Calcular y agregar fecha de vencimiento
            try:
                expiration_date = self.calculator_service.calculate_expiration_date(
                    added_at=current_time,
                    time_value=ingredient["expiration_time"],
                    time_unit=ingredient["time_unit"]
                )
                ingredient["expiration_date"] = expiration_date.isoformat()
                print(f"📅 Calculated expiration for {ingredient['name']}: {expiration_date}")
                
            except Exception as e:
                print(f"🚨 Error calculating expiration for {ingredient['name']}: {str(e)}")
                # Fallback: agregar días como default
                fallback_date = current_time + timedelta(days=ingredient.get("expiration_time", 7))
                ingredient["expiration_date"] = fallback_date.isoformat()
            
            # ⭐ NUEVO: Agregar campo added_at para consistencia temporal
            ingredient["added_at"] = current_time.isoformat()
            print(f"🕐 Added timestamp for {ingredient['name']}: {current_time}")

        return result
    
    def _get_default_image_path(self) -> str:
        """
        Retorna una imagen por defecto cuando no se encuentra ninguna referencia.
        Puede ser una URL de imagen placeholder o None.
        """
        return "https://via.placeholder.com/150x150/cccccc/666666?text=No+Image"