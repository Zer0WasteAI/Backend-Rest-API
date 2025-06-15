"""
Servicio para generar y gestionar imágenes de platos de comida.
Similar al servicio de ingredientes pero optimizado para foods/platos preparados.
"""
import re
from pathlib import Path
from typing import Optional, List
import time


class FoodImageGeneratorService:
    """
    Servicio para obtener o generar imágenes de platos de comida.
    
    Flujo:
    1. Buscar imagen existente en /foods/
    2. Si no existe, generar nueva imagen
    3. Retornar URL directa
    """
    
    def __init__(self, ai_service, storage_adapter):
        self.ai_service = ai_service
        self.storage_adapter = storage_adapter
        self.foods_folder = "foods"
    
    def get_or_generate_food_image(self, food_name: str, user_uid: str, description: str = "", main_ingredients: List[str] = None) -> str:
        """
        Obtiene o genera una imagen para un plato de comida.
        
        Args:
            food_name: Nombre del plato
            user_uid: UID del usuario (para logs)
            description: Descripción del plato
            main_ingredients: Lista de ingredientes principales
            
        Returns:
            str: URL de la imagen
        """
        print(f"🍽️ Getting/generating image for food: {food_name}")
        
        # 1. Buscar imagen existente
        existing_image_url = self._check_existing_food_image(food_name)
        if existing_image_url:
            print(f"✅ Found existing food image: {existing_image_url}")
            return existing_image_url
        
        # 2. Generar nueva imagen si no existe
        print(f"🎨 Generating new image for food: {food_name}")
        try:
            return self._generate_new_food_image(food_name, description, main_ingredients)
        except Exception as e:
            print(f"🚨 Error generating image for {food_name}: {str(e)}")
            return self._get_fallback_food_image_url(food_name)
    
    def _check_existing_food_image(self, food_name: str) -> Optional[str]:
        """
        Busca una imagen existente del plato en Firebase Storage.
        
        Args:
            food_name: Nombre del plato
            
        Returns:
            Optional[str]: URL de la imagen si existe, None si no
        """
        normalized_name = self._normalize_food_name(food_name)
        
        # Intentar diferentes extensiones
        extensions = ['jpg', 'jpeg', 'png', 'webp']
        
        for ext in extensions:
            try:
                # Ruta en el bucket: foods/nombre_normalizado.ext
                image_path = f"{self.foods_folder}/{normalized_name}.{ext}"
                
                # Verificar si existe usando el storage adapter
                blob = self.storage_adapter.bucket.blob(image_path)
                if blob.exists():
                    # Generar URL pública
                    image_url = f"https://storage.googleapis.com/{self.storage_adapter.bucket.name}/{image_path}"
                    print(f"✅ Found existing food image: {image_path}")
                    return image_url
                    
            except Exception as e:
                print(f"⚠️ Error checking {image_path}: {str(e)}")
                continue
        
        print(f"❌ No existing image found for food: {food_name}")
        return None
    
    def _generate_new_food_image(self, food_name: str, description: str = "", main_ingredients: List[str] = None) -> str:
        """
        Genera una nueva imagen para el plato usando AI.
        
        Args:
            food_name: Nombre del plato
            description: Descripción del plato
            main_ingredients: Lista de ingredientes principales
            
        Returns:
            str: URL de la imagen generada
        """
        print(f"🎨 Generating image for food: {food_name}")
        
        try:
            # Generar imagen usando el servicio AI
            image_buffer = self.ai_service.generate_food_image(
                food_name=food_name,
                description=description,
                main_ingredients=main_ingredients or []
            )
            
            if image_buffer is None:
                print(f"🚨 AI service failed to generate image for {food_name}")
                raise Exception("AI service returned None")
            
            # Preparar nombre de archivo normalizado
            normalized_name = self._normalize_food_name(food_name)
            filename = f"{normalized_name}.jpg"
            image_path = f"{self.foods_folder}/{filename}"
            
            # Subir a Firebase Storage desde el BytesIO buffer
            blob = self.storage_adapter.bucket.blob(image_path)
            image_buffer.seek(0)  # Reset buffer position
            blob.upload_from_file(image_buffer, content_type='image/jpeg')
            
            # Generar URL pública
            image_url = f"https://storage.googleapis.com/{self.storage_adapter.bucket.name}/{image_path}"
            
            print(f"✅ Food image generated and saved: {image_path}")
            return image_url
            
        except Exception as e:
            print(f"🚨 Error generating food image: {str(e)}")
            raise
    
    def _normalize_food_name(self, name: str) -> str:
        """
        Normaliza el nombre del plato para usar como nombre de archivo.
        
        Args:
            name: Nombre original del plato
            
        Returns:
            str: Nombre normalizado
        """
        # Convertir a minúsculas
        normalized = name.lower()
        
        # Reemplazar caracteres especiales
        replacements = {
            'ñ': 'n', 'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ü': 'u', 'ç': 'c'
        }
        
        for char, replacement in replacements.items():
            normalized = normalized.replace(char, replacement)
        
        # Reemplazar espacios y caracteres especiales con guiones bajos
        normalized = re.sub(r'[^a-z0-9]', '_', normalized)
        
        # Eliminar guiones bajos múltiples
        normalized = re.sub(r'_+', '_', normalized)
        
        # Eliminar guiones bajos al principio y final
        normalized = normalized.strip('_')
        
        # Limitar longitud
        if len(normalized) > 50:
            normalized = normalized[:50].rstrip('_')
        
        return normalized
    
    def _get_fallback_food_image_url(self, food_name: str) -> str:
        """
        Retorna una URL de imagen de fallback cuando no se puede generar.
        
        Args:
            food_name: Nombre del plato
            
        Returns:
            str: URL de imagen de fallback
        """
        # URL de placeholder con el nombre del plato
        encoded_name = food_name.replace(' ', '+')
        fallback_url = f"https://via.placeholder.com/300x300/e8f5e8/666666?text={encoded_name}"
        
        print(f"🔄 Using fallback image for food: {food_name}")
        return fallback_url
    
    def list_existing_foods_images(self) -> list:
        """
        Lista todas las imágenes existentes en la carpeta foods.
        Útil para debugging y monitoreo.
        
        Returns:
            list: Lista de nombres de archivos de imágenes
        """
        try:
            images = []
            blobs = self.storage_adapter.bucket.list_blobs(prefix=f"{self.foods_folder}/")
            
            for blob in blobs:
                if blob.name.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    # Extraer solo el nombre del archivo
                    filename = blob.name.split('/')[-1]
                    images.append({
                        'filename': filename,
                        'path': blob.name,
                        'url': f"https://storage.googleapis.com/{self.storage_adapter.bucket.name}/{blob.name}"
                    })
            
            print(f"📋 Found {len(images)} food images")
            return images
            
        except Exception as e:
            print(f"🚨 Error listing food images: {str(e)}")
            return [] 