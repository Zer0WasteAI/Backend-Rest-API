"""
Servicio optimizado para generar y gestionar imágenes de ingredientes.
Solo usa la carpeta /ingredients/ y almacena URLs directamente.
Inclye optimizaciones de batch processing y async operations.
"""
import re
import asyncio
from pathlib import Path
from typing import Optional, List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class IngredientImageGeneratorService:
    """
    Servicio optimizado para obtener o generar imágenes de ingredientes.
    
    Flujo optimizado:
    1. Batch check de imágenes existentes
    2. Generación paralela de imágenes faltantes
    3. Upload concurrente con rate limiting
    4. Cache en memoria para sesión actual
    """
    
    def __init__(self, ai_service, storage_adapter):
        self.ai_service = ai_service
        self.storage_adapter = storage_adapter
        self.ingredients_folder = "ingredients"
        self.performance_mode = True
        self.max_concurrent_generations = 5  # Increased for better throughput
        self.max_concurrent_uploads = 10     # Increased storage upload limit
        self.session_cache = {}             # In-memory cache for current session
    
    def get_or_generate_ingredient_image(self, ingredient_name: str, user_uid: str, descripcion: str = "") -> str:
        """
        Obtiene o genera una imagen para un ingrediente (modo estándar).
        
        Args:
            ingredient_name: Nombre del ingrediente
            user_uid: UID del usuario (para logs)
            descripcion: Descripción del ingrediente (opcional)
            
        Returns:
            str: URL de la imagen
        """
        print(f"🔍 Getting/generating image for ingredient: {ingredient_name}")
        
        # Check session cache first
        if ingredient_name in self.session_cache:
            print(f"⚡ [SESSION CACHE] Using cached URL for {ingredient_name}")
            return self.session_cache[ingredient_name]
        
        # 1. Buscar imagen existente
        existing_image_url = self._check_existing_ingredient_image(ingredient_name)
        if existing_image_url:
            print(f"✅ Found existing image: {existing_image_url}")
            self.session_cache[ingredient_name] = existing_image_url
            return existing_image_url
        
        # 2. Generar nueva imagen si no existe
        print(f"🎨 Generating new image for: {ingredient_name}")
        try:
            image_url = self._generate_new_ingredient_image(ingredient_name, descripcion)
            self.session_cache[ingredient_name] = image_url
            return image_url
        except Exception as e:
            print(f"🚨 Error generating image for {ingredient_name}: {str(e)}")
            fallback_url = self._get_fallback_image_url(ingredient_name)
            self.session_cache[ingredient_name] = fallback_url
            return fallback_url
    
    async def get_or_generate_ingredient_images_batch(self, ingredients: List[Dict], user_uid: str) -> Dict[str, str]:
        """
        ULTRA-OPTIMIZED: Generate multiple ingredient images in parallel with smart caching
        
        Args:
            ingredients: List of ingredient dicts with 'name' and optional 'description'
            user_uid: User ID for logging
            
        Returns:
            Dict mapping ingredient names to image URLs
        """
        print(f"🚀 [BATCH OPTIMIZED] Processing {len(ingredients)} ingredient images")
        
        # 1. Check session cache first
        image_urls = {}
        uncached_ingredients = []
        
        for ingredient in ingredients:
            name = ingredient.get('name', '')
            if name in self.session_cache:
                image_urls[name] = self.session_cache[name]
                print(f"⚡ [SESSION CACHE] Found {name}")
            else:
                uncached_ingredients.append(ingredient)
        
        if not uncached_ingredients:
            print(f"🎯 [ALL CACHED] All {len(ingredients)} images found in session cache")
            return image_urls
        
        print(f"📋 [CACHE MISS] Need to process {len(uncached_ingredients)} images")
        
        # 2. Batch check existing images in parallel
        existing_checks = []
        with ThreadPoolExecutor(max_workers=self.max_concurrent_uploads) as executor:
            for ingredient in uncached_ingredients:
                future = executor.submit(self._check_existing_ingredient_image, ingredient['name'])
                existing_checks.append((ingredient['name'], future))
        
        # 3. Collect existing images and identify missing ones
        missing_ingredients = []
        for ingredient_name, future in existing_checks:
            try:
                existing_url = future.result(timeout=5)  # 5 second timeout per check
                if existing_url:
                    image_urls[ingredient_name] = existing_url
                    self.session_cache[ingredient_name] = existing_url
                    print(f"✅ Found existing: {ingredient_name}")
                else:
                    # Find the ingredient data for missing ones
                    ingredient_data = next(ing for ing in uncached_ingredients if ing['name'] == ingredient_name)
                    missing_ingredients.append(ingredient_data)
            except Exception as e:
                print(f"⚠️ Error checking {ingredient_name}: {e}")
                ingredient_data = next(ing for ing in uncached_ingredients if ing['name'] == ingredient_name)
                missing_ingredients.append(ingredient_data)
        
        # 4. Generate missing images in parallel batches (respecting API limits)
        if missing_ingredients:
            print(f"🎨 [BATCH GENERATION] Generating {len(missing_ingredients)} new images")
            
            # Process in smaller batches to respect AI API rate limits
            batch_size = self.max_concurrent_generations
            for i in range(0, len(missing_ingredients), batch_size):
                batch = missing_ingredients[i:i + batch_size]
                
                # Generate batch concurrently
                generation_tasks = []
                with ThreadPoolExecutor(max_workers=batch_size) as executor:
                    for ingredient in batch:
                        future = executor.submit(
                            self._generate_new_ingredient_image,
                            ingredient['name'],
                            ingredient.get('description', '')
                        )
                        generation_tasks.append((ingredient['name'], future))
                
                # Collect results from batch
                for ingredient_name, future in generation_tasks:
                    try:
                        image_url = future.result(timeout=30)  # 30 second timeout per generation
                        image_urls[ingredient_name] = image_url
                        self.session_cache[ingredient_name] = image_url
                        print(f"✅ Generated: {ingredient_name}")
                    except Exception as e:
                        print(f"🚨 Failed to generate {ingredient_name}: {e}")
                        fallback_url = self._get_fallback_image_url(ingredient_name)
                        image_urls[ingredient_name] = fallback_url
                        self.session_cache[ingredient_name] = fallback_url
                
                # Small delay between batches to respect rate limits
                if i + batch_size < len(missing_ingredients):
                    await asyncio.sleep(0.5)
        
        print(f"🎉 [BATCH COMPLETED] Processed {len(image_urls)} ingredient images")
        return image_urls
    
    def clear_session_cache(self) -> int:
        """
        Clear the session cache and return number of cleared entries
        """
        count = len(self.session_cache)
        self.session_cache.clear()
        print(f"🧹 Cleared {count} cached image URLs")
        return count
    
    def get_cache_stats(self) -> Dict[str, any]:
        """
        Get session cache statistics
        """
        return {
            'cached_images': len(self.session_cache),
            'cache_keys': list(self.session_cache.keys()),
            'performance_mode': self.performance_mode,
            'max_concurrent_generations': self.max_concurrent_generations,
            'max_concurrent_uploads': self.max_concurrent_uploads
        }
    
    def get_or_generate_ingredient_images_sync_batch(self, ingredients: List[Dict], user_uid: str) -> Dict[str, str]:
        """
        Synchronous version of batch image generation for compatibility
        """
        if self.performance_mode:
            # Run async version in event loop
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.get_or_generate_ingredient_images_batch(ingredients, user_uid)
                )
                loop.close()
                return result
            except Exception as e:
                print(f"🚨 Async batch failed, falling back to standard: {e}")
        
        # Fallback to individual processing
        image_urls = {}
        for ingredient in ingredients:
            name = ingredient.get('name', '')
            description = ingredient.get('description', '')
            image_urls[name] = self.get_or_generate_ingredient_image(name, user_uid, description)
        
        return image_urls
    
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