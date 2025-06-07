import uuid
from datetime import datetime, timezone, timedelta
from src.domain.models.recognition import Recognition
from typing import List


class RecognizeBatchUseCase:
    def __init__(self, ai_service, recognition_repository, storage_adapter, calculator_service):
        self.ai_service = ai_service
        self.recognition_repository = recognition_repository
        self.storage_adapter = storage_adapter
        self.calculator_service = calculator_service

    def execute(self, user_uid: str, images_paths: List[str]) -> dict:
        images_files = []
        for path in images_paths:
            file = self.storage_adapter.get_image(path)
            images_files.append(file)

        result = self.ai_service.recognize_batch(images_files)
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
        
        # ⭐ NUEVO: Calcular y agregar fechas de vencimiento para batch (ingredients y foods)
        current_time = datetime.now(timezone.utc)
        
        # Procesar ingredientes
        for ingredient in result.get("ingredients", []):
            print(f"🔍 Processing expiration for ingredient: {ingredient['name']}")
            
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
        
        # Procesar foods
        for food in result.get("foods", []):
            print(f"🔍 Processing expiration for food: {food['name']}")
            
            try:
                expiration_date = self.calculator_service.calculate_expiration_date(
                    added_at=current_time,
                    time_value=food["expiration_time"],
                    time_unit=food["time_unit"]
                )
                food["expiration_date"] = expiration_date.isoformat()
                print(f"📅 Calculated expiration for {food['name']}: {expiration_date}")
                
            except Exception as e:
                print(f"🚨 Error calculating expiration for {food['name']}: {str(e)}")
                # Fallback: agregar días como default
                fallback_date = current_time + timedelta(days=food.get("expiration_time", 3))
                food["expiration_date"] = fallback_date.isoformat()
            
            # ⭐ NUEVO: Agregar campo added_at para consistencia temporal
            food["added_at"] = current_time.isoformat()
            print(f"🕐 Added timestamp for {food['name']}: {current_time}")
        
        return result