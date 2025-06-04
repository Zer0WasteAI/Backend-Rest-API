import uuid
import os
from io import BytesIO
from pathlib import Path
from typing import Optional

from src.domain.models.image_reference import ImageReference


class IngredientImageGeneratorService:
    """
    Service to handle ingredient image generation with strategic storage:
    1. Check if image exists in global 'images_ingredients' folder
    2. If exists: copy to user's personal folder
    3. If doesn't exist: generate new image with Gemini, save to both locations
    """
    
    def __init__(self, ai_service, storage_adapter, image_repository):
        self.ai_service = ai_service
        self.storage_adapter = storage_adapter
        self.image_repository = image_repository
        
    def get_or_generate_ingredient_image(self, ingredient_name: str, user_uid: str) -> str:
        """
        Gets or generates an image for an ingredient following the storage strategy.
        
        Args:
            ingredient_name: Name of the ingredient
            user_uid: User's unique identifier
            
        Returns:
            String: URL path to the ingredient image
        """
        try:
            # Step 1: Check if image exists in global folder
            global_image_path = self._check_global_ingredient_image(ingredient_name)
            
            if global_image_path:
                print(f"📸 Found existing image for {ingredient_name} in global folder")
                # Step 2: Copy to user's personal folder
                user_image_path = self._copy_to_user_folder(global_image_path, ingredient_name, user_uid)
                return user_image_path
            else:
                print(f"🆕 No existing image for {ingredient_name}, generating new one")
                # Step 3: Generate new image and save to both locations
                return self._generate_and_save_image(ingredient_name, user_uid)
                
        except Exception as e:
            print(f"🚨 Error in get_or_generate_ingredient_image for {ingredient_name}: {str(e)}")
            return self._get_fallback_image()
    
    def _check_global_ingredient_image(self, ingredient_name: str) -> Optional[str]:
        """
        Check if an image exists in the global 'images_ingredients' folder.
        
        Returns:
            Optional[str]: Path to the global image if it exists, None otherwise
        """
        try:
            # Look for existing image in global folder
            global_path_jpg = f"images_ingredients/{self._normalize_filename(ingredient_name)}.jpg"
            global_path_png = f"images_ingredients/{self._normalize_filename(ingredient_name)}.png"
            
            # Check both JPG and PNG extensions
            for global_path in [global_path_jpg, global_path_png]:
                try:
                    blob = self.storage_adapter.bucket.blob(global_path)
                    if blob.exists():
                        return global_path
                except Exception:
                    continue
                    
            return None
            
        except Exception as e:
            print(f"🚨 Error checking global image for {ingredient_name}: {str(e)}")
            return None
    
    def _copy_to_user_folder(self, global_image_path: str, ingredient_name: str, user_uid: str) -> str:
        """
        Copy an existing image from global folder to user's personal folder.
        
        Args:
            global_image_path: Path to the existing global image
            ingredient_name: Name of the ingredient
            user_uid: User's unique identifier
            
        Returns:
            str: URL to the copied image in user's folder
        """
        try:
            # Get the file extension from global path
            file_extension = Path(global_image_path).suffix
            
            # Define user's personal image path
            user_image_path = f"uploads/{user_uid}/ingredient/{self._normalize_filename(ingredient_name)}{file_extension}"
            
            # Get the source blob
            source_blob = self.storage_adapter.bucket.blob(global_image_path)
            
            # Copy to user's folder
            destination_blob = self.storage_adapter.bucket.blob(user_image_path)
            destination_blob.upload_from_string(
                source_blob.download_as_bytes(),
                content_type=source_blob.content_type
            )
            destination_blob.make_public()
            
            print(f"📋 Copied image from {global_image_path} to {user_image_path}")
            return destination_blob.public_url
            
        except Exception as e:
            print(f"🚨 Error copying image for {ingredient_name}: {str(e)}")
            return self._get_fallback_image()
    
    def _generate_and_save_image(self, ingredient_name: str, user_uid: str) -> str:
        """
        Generate a new image using Gemini and save to both global and user folders.
        
        Args:
            ingredient_name: Name of the ingredient
            user_uid: User's unique identifier
            
        Returns:
            str: URL to the generated image in user's folder
        """
        try:
            # Generate image using Gemini
            print(f"🎨 Generating image for {ingredient_name} using Gemini...")
            generated_image = self.ai_service.generate_ingredient_image(ingredient_name)
            
            if not generated_image:
                print(f"❌ Failed to generate image for {ingredient_name}")
                return self._get_fallback_image()
            
            # Read the image data once and create copies for both saves
            image_bytes = generated_image.read()
            generated_image.close()
            
            # Save to both global and user folders
            global_image_url = self._save_to_global_folder(BytesIO(image_bytes), ingredient_name)
            user_image_url = self._save_to_user_folder(BytesIO(image_bytes), ingredient_name, user_uid)
            
            # Register in image repository for future reference
            self._register_image_in_repository(ingredient_name, global_image_url)
            
            print(f"✅ Successfully generated and saved image for {ingredient_name}")
            return user_image_url
            
        except Exception as e:
            print(f"🚨 Error generating image for {ingredient_name}: {str(e)}")
            return self._get_fallback_image()
    
    def _save_to_global_folder(self, image_data: BytesIO, ingredient_name: str) -> str:
        """Save generated image to global 'images_ingredients' folder."""
        try:
            global_path = f"images_ingredients/{self._normalize_filename(ingredient_name)}.jpg"
            
            blob = self.storage_adapter.bucket.blob(global_path)
            image_data.seek(0)  # Reset stream position
            blob.upload_from_file(image_data, content_type="image/jpeg")
            blob.make_public()
            
            print(f"💾 Saved to global folder: {global_path}")
            return blob.public_url
            
        except Exception as e:
            print(f"🚨 Error saving to global folder: {str(e)}")
            raise e
    
    def _save_to_user_folder(self, image_data: BytesIO, ingredient_name: str, user_uid: str) -> str:
        """Save generated image to user's personal folder."""
        try:
            user_path = f"uploads/{user_uid}/ingredient/{self._normalize_filename(ingredient_name)}.jpg"
            
            blob = self.storage_adapter.bucket.blob(user_path)
            image_data.seek(0)  # Reset stream position
            blob.upload_from_file(image_data, content_type="image/jpeg")
            blob.make_public()
            
            print(f"💾 Saved to user folder: {user_path}")
            return blob.public_url
            
        except Exception as e:
            print(f"🚨 Error saving to user folder: {str(e)}")
            raise e
    
    def _register_image_in_repository(self, ingredient_name: str, image_url: str) -> None:
        """Register the generated image in the image repository."""
        try:
            # Check if already exists to avoid duplicates
            existing_image = self.image_repository.find_by_name(ingredient_name)
            if not existing_image:
                image_ref = ImageReference(
                    uid=str(uuid.uuid4()),
                    name=ingredient_name.lower(),
                    image_path=image_url,
                    image_type="ingredient"
                )
                self.image_repository.save(image_ref)
                print(f"📝 Registered {ingredient_name} in image repository")
            
        except Exception as e:
            print(f"🚨 Error registering image in repository: {str(e)}")
            # Don't raise the error, as this is not critical
    
    def _normalize_filename(self, ingredient_name: str) -> str:
        """Normalize ingredient name for filename."""
        return ingredient_name.lower().replace(' ', '_').replace('-', '_')
    
    def _get_fallback_image(self) -> str:
        """Return fallback image URL when generation fails."""
        fallback_image = self.image_repository.find_by_name("imagen defecto")
        if fallback_image:
            return fallback_image.image_path
        return "https://via.placeholder.com/150x150/cccccc/666666?text=No+Image" 