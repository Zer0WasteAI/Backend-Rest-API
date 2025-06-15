import re
from typing import Optional, List

class RecipeImageGeneratorService:
    """
    Servicio para obtener o generar imágenes de recetas.
    Inspirado en FoodImageGeneratorService pero adaptado a recetas generadas.
    """
    def __init__(self, ai_service, storage_adapter, ai_image_service):
        self.ai_service = ai_service
        self.storage_adapter = storage_adapter
        self.ai_image_service = ai_image_service
        self.recipes_folder = "recipes"

    def get_or_generate_recipe_image(self, recipe_title: str, user_uid: str, description: str = "", ingredients: List[dict] = None) -> str:
        print(f"👩‍🍳 Getting/generating image for recipe: {recipe_title}")

        existing_image_url = self._check_existing_recipe_image(recipe_title)
        if existing_image_url:
            print(f"✅ Found existing recipe image: {existing_image_url}")
            return existing_image_url

        try:
            return self._generate_new_recipe_image(recipe_title, description, ingredients)
        except Exception as e:
            print(f"🚨 Error generating image for {recipe_title}: {str(e)}")
            return self._get_fallback_recipe_image_url(recipe_title)

    def _check_existing_recipe_image(self, recipe_title: str) -> Optional[str]:
        normalized_name = self._normalize_recipe_title(recipe_title)
        extensions = ['jpg', 'jpeg', 'png', 'webp']

        for ext in extensions:
            try:
                image_path = f"{self.recipes_folder}/{normalized_name}.{ext}"
                blob = self.storage_adapter.bucket.blob(image_path)
                if blob.exists():
                    return f"https://storage.googleapis.com/{self.storage_adapter.bucket.name}/{image_path}"
            except Exception as e:
                print(f"⚠️ Error checking {image_path}: {str(e)}")
        return None

    def _generate_new_recipe_image(self, recipe_title: str, description: str = "", ingredients: List[dict] = None) -> str:
        print(f"🎨 Generating image for recipe: {recipe_title}")

        image_buffer = self.ai_image_service.generate_food_image(
            #title=recipe_title,
            food_name=recipe_title,
            description=description,
            main_ingredients=[i.get("name", "") for i in ingredients] if ingredients else []
        )

        if image_buffer is None:
            raise Exception("AI service returned None")

        normalized_name = self._normalize_recipe_title(recipe_title)
        filename = f"{normalized_name}.jpg"
        image_path = f"{self.recipes_folder}/{filename}"

        blob = self.storage_adapter.bucket.blob(image_path)
        image_buffer.seek(0)
        blob.upload_from_file(image_buffer, content_type='image/jpeg')

        image_url = f"https://storage.googleapis.com/{self.storage_adapter.bucket.name}/{image_path}"
        print(f"✅ Recipe image generated and saved: {image_path}")
        return image_url

    def _normalize_recipe_title(self, title: str) -> str:
        normalized = title.lower()
        replacements = {
            'ñ': 'n', 'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u', 'ç': 'c'
        }
        for char, rep in replacements.items():
            normalized = normalized.replace(char, rep)
        normalized = re.sub(r'[^a-z0-9]', '_', normalized)
        normalized = re.sub(r'_+', '_', normalized).strip('_')
        return normalized[:50].rstrip('_')

    def _get_fallback_recipe_image_url(self, recipe_title: str) -> str:
        encoded = recipe_title.replace(' ', '+')
        return f"https://via.placeholder.com/300x300/fde3e3/666666?text={encoded}"
