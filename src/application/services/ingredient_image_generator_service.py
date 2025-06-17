"""
Servicio simplificado para generar y gestionar imágenes de ingredientes.
Solo usa la carpeta /ingredients/ y almacena URLs directamente.
"""
import re
from pathlib import Path
from typing import Optional
import time


class IngredientImageGeneratorService:
    """
    Servicio para obtener o generar imágenes de ingredientes.
    
    Flujo simplificado:
    1. Buscar imagen existente en /ingredients/
    2. Si no existe, generar nueva imagen
    3. Retornar URL directa
    """
    
    def __init__(self, ai_service, storage_adapter):
        self.ai_service = ai_service
        self.storage_adapter = storage_adapter
        self.ingredients_folder = "ingredients"
    
    def get_or_generate_ingredient_image(self, ingredient_name: str, user_uid: str, descripcion: str = "") -> str:
        """
        Obtiene o genera una imagen para un ingrediente.
        
        Args:
            ingredient_name: Nombre del ingrediente
            user_uid: UID del usuario (para logs)
            descripcion: Descripción del ingrediente (opcional)
            
        Returns:
            str: URL de la imagen
        """
        print(f"🔍 Getting/generating image for ingredient: {ingredient_name}")
        
        # 1. Buscar imagen existente
        existing_image_url = self._check_existing_ingredient_image(ingredient_name)
        if existing_image_url:
            print(f"✅ Found existing image: {existing_image_url}")
            return existing_image_url
        
        # 2. Generar nueva imagen si no existe
        print(f"🎨 Generating new image for: {ingredient_name}")
        try:
            return self._generate_new_ingredient_image(ingredient_name, descripcion)
        except Exception as e:
            print(f"🚨 Error generating image for {ingredient_name}: {str(e)}")
            return self._get_fallback_image_url(ingredient_name)
    
    def _check_existing_ingredient_image(self, ingredient_name: str) -> Optional[str]:
        """
        Busca una imagen existente del ingrediente en Firebase Storage.
        
        Args:
            ingredient_name: Nombre del ingrediente
            
        Returns:
            Optional[str]: URL de la imagen si existe, None si no
        """
        normalized_name = self._normalize_ingredient_name(ingredient_name)
        
        # Intentar diferentes extensiones
        extensions = ['jpg', 'jpeg', 'png', 'webp']
        
        for ext in extensions:
            try:
                # Ruta en el bucket: ingredients/nombre_normalizado.ext
                image_path = f"{self.ingredients_folder}/{normalized_name}.{ext}"
                
                # Verificar si existe usando el storage adapter
                blob = self.storage_adapter.bucket.blob(image_path)
                if blob.exists():
                    # Generar URL firmada para imagen existente
                    from datetime import datetime, timedelta
                    expiration = datetime.utcnow() + timedelta(days=7)
                    
                    image_url = blob.generate_signed_url(
                        expiration=expiration,
                        method='GET'
                    )
                    print(f"✅ Found existing image: {image_path}")
                    return image_url
                    
            except Exception as e:
                print(f"⚠️ Error checking {image_path}: {str(e)}")
                continue
        
        print(f"❌ No existing image found for: {ingredient_name}")
        return None
    
    def _generate_new_ingredient_image(self, ingredient_name: str, descripcion: str = "") -> str:
        """
        Genera una nueva imagen para el ingrediente usando AI.
        
        Args:
            ingredient_name: Nombre del ingrediente
            descripcion: Descripción del ingrediente
            
        Returns:
            str: URL de la imagen generada
        """
        print(f"🎨 Generating image for: {ingredient_name}")
        
        try:
            # Generar imagen usando el servicio AI
            image_buffer = self.ai_service.generate_ingredient_image(
                ingredient_name=ingredient_name,
                descripcion=descripcion
            )
            
            if image_buffer is None:
                print(f"🚨 AI service failed to generate image for {ingredient_name}")
                raise Exception("AI service returned None")
            
            # Preparar nombre de archivo normalizado
            normalized_name = self._normalize_ingredient_name(ingredient_name)
            filename = f"{normalized_name}.jpg"
            image_path = f"{self.ingredients_folder}/{filename}"
            
            # Subir a Firebase Storage desde el BytesIO buffer
            blob = self.storage_adapter.bucket.blob(image_path)
            image_buffer.seek(0)  # Reset buffer position
            blob.upload_from_file(image_buffer, content_type='image/jpeg')
            
            # Generar URL firmada (válida por 7 días)
            from datetime import datetime, timedelta
            expiration = datetime.utcnow() + timedelta(days=7)
            
            image_url = blob.generate_signed_url(
                expiration=expiration,
                method='GET'
            )
            
            print(f"✅ Image generated and saved: {image_path}")
            return image_url
            
        except Exception as e:
            print(f"🚨 Error generating image: {str(e)}")
            raise
    
    def _normalize_ingredient_name(self, name: str) -> str:
        """
        Normaliza el nombre del ingrediente para usar como nombre de archivo.
        
        Args:
            name: Nombre original del ingrediente
            
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
    
    def _get_fallback_image_url(self, ingredient_name: str) -> str:
        """
        Retorna una URL de imagen de fallback cuando no se puede generar.
        
        Args:
            ingredient_name: Nombre del ingrediente
            
        Returns:
            str: URL de imagen de fallback
        """
        # URL de placeholder con el nombre del ingrediente
        encoded_name = ingredient_name.replace(' ', '+')
        fallback_url = f"https://via.placeholder.com/300x300/f0f0f0/666666?text={encoded_name}"
        
        print(f"🔄 Using fallback image for: {ingredient_name}")
        return fallback_url
    
    def list_existing_ingredients_images(self) -> list:
        """
        Lista todas las imágenes existentes en la carpeta ingredients.
        Útil para debugging y monitoreo.
        
        Returns:
            list: Lista de nombres de archivos de imágenes
        """
        try:
            images = []
            blobs = self.storage_adapter.bucket.list_blobs(prefix=f"{self.ingredients_folder}/")
            
            for blob in blobs:
                if blob.name.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    # Extraer solo el nombre del archivo
                    filename = blob.name.split('/')[-1]
                    images.append({
                        'filename': filename,
                        'path': blob.name,
                        'url': f"https://storage.googleapis.com/{self.storage_adapter.bucket.name}/{blob.name}"
                    })
            
            print(f"📋 Found {len(images)} ingredient images")
            return images
            
        except Exception as e:
            print(f"🚨 Error listing ingredient images: {str(e)}")
            return [] 