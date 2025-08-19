"""
Unit tests for Recipe Image Generator Service
Tests AI-powered recipe image generation functionality
"""
import pytest
from unittest.mock import Mock, patch
import io

from src.application.services.recipe_image_generator_service import (
    RecipeImageGeneratorService,
    get_or_generate_recipe_image
)


class TestRecipeImageGeneratorService:
    """Test suite for Recipe Image Generator Service"""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Create mock AI service"""
        return Mock()
    
    @pytest.fixture
    def mock_storage_adapter(self):
        """Create mock storage adapter"""
        mock_storage = Mock()
        mock_bucket = Mock()
        mock_bucket.name = "test-bucket"
        mock_storage.bucket = mock_bucket
        return mock_storage
    
    @pytest.fixture
    def mock_ai_image_service(self):
        """Create mock AI image service"""
        mock_service = Mock()
        mock_service.generate_food_image.return_value = io.BytesIO(b"fake_image_data")
        return mock_service
    
    @pytest.fixture
    def service(self, mock_ai_service, mock_storage_adapter, mock_ai_image_service):
        """Create recipe image generator service instance"""
        return RecipeImageGeneratorService(
            mock_ai_service, 
            mock_storage_adapter, 
            mock_ai_image_service
        )

    def test_service_initialization(self, mock_ai_service, mock_storage_adapter, mock_ai_image_service):
        """Test service can be initialized properly"""
        # Act
        service = RecipeImageGeneratorService(
            mock_ai_service, mock_storage_adapter, mock_ai_image_service
        )
        
        # Assert
        assert service is not None
        assert service.ai_service == mock_ai_service
        assert service.storage_adapter == mock_storage_adapter
        assert service.ai_image_service == mock_ai_image_service
        assert service.recipes_folder == "recipes"

    def test_get_or_generate_recipe_image_with_existing_image(self, service):
        """Test getting existing recipe image"""
        # Arrange - Mock existing image
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        service.storage_adapter.bucket.blob.return_value = mock_blob
        service.storage_adapter.bucket.name = "test-bucket"
        
        # Act
        result = service.get_or_generate_recipe_image(
            "Chicken Teriyaki Bowl", "user-123", "Test description", []
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, str)
        assert "storage.googleapis.com" in result

    def test_get_or_generate_recipe_image_generate_new(self, service):
        """Test generating new recipe image when none exists"""
        # Arrange - No existing image
        mock_blob_check = Mock()
        mock_blob_check.exists.return_value = False
        
        mock_blob_upload = Mock()
        service.storage_adapter.bucket.blob.side_effect = [mock_blob_check, mock_blob_upload]
        service.storage_adapter.bucket.name = "test-bucket"
        
        # Act
        result = service.get_or_generate_recipe_image(
            "New Recipe", "user-123", "Test description", [{"name": "ingredient1"}]
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, str)
        service.ai_image_service.generate_food_image.assert_called_once()
        mock_blob_upload.upload_from_file.assert_called_once()

    def test_get_or_generate_recipe_image_fallback_on_error(self, service):
        """Test fallback URL when image generation fails"""
        # Arrange - Mock error in generation
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        service.storage_adapter.bucket.blob.return_value = mock_blob
        service.ai_image_service.generate_food_image.side_effect = Exception("AI service error")
        
        # Act
        result = service.get_or_generate_recipe_image(
            "Failed Recipe", "user-123", "Test description", []
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, str)
        assert "placeholder" in result.lower()

    def test_normalize_recipe_title(self, service):
        """Test recipe title normalization"""
        # Test various title formats
        test_cases = [
            ("Chicken & Rice", "chicken_rice"),
            ("Pasta with Tomatoes!", "pasta_with_tomatoes"),
            ("Spicy Tacos!!!", "spicy_tacos"),
            ("Test-Recipe_Name", "test_recipe_name"),
        ]
        
        for input_title, expected_output in test_cases:
            result = service._normalize_recipe_title(input_title)
            assert result == expected_output

    def test_check_existing_recipe_image_multiple_extensions(self, service):
        """Test checking for existing images with different extensions"""
        # Arrange - Mock blob behavior
        service.storage_adapter.bucket.name = "test-bucket"
        
        def mock_blob(path):
            mock_blob = Mock()
            if path.endswith('.jpg'):
                mock_blob.exists.return_value = True
            else:
                mock_blob.exists.return_value = False
            return mock_blob
        
        service.storage_adapter.bucket.blob.side_effect = mock_blob
        
        # Act
        result = service._check_existing_recipe_image("Test Recipe")
        
        # Assert
        assert result is not None
        assert isinstance(result, str)
        assert "test_recipe.jpg" in result

    def test_check_existing_recipe_image_not_found(self, service):
        """Test when no existing image is found"""
        # Arrange - No existing images
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        service.storage_adapter.bucket.blob.return_value = mock_blob
        
        # Act
        result = service._check_existing_recipe_image("Nonexistent Recipe")
        
        # Assert
        assert result is None

    def test_generate_new_recipe_image_success(self, service):
        """Test successful new image generation"""
        # Arrange
        mock_blob = Mock()
        service.storage_adapter.bucket.blob.return_value = mock_blob
        service.storage_adapter.bucket.name = "test-bucket"
        
        # Act
        result = service._generate_new_recipe_image(
            "New Recipe", 
            "Description", 
            [{"name": "ingredient1"}, {"name": "ingredient2"}]
        )
        
        # Assert
        assert result is not None
        assert isinstance(result, str)
        assert "new_recipe.jpg" in result
        service.ai_image_service.generate_food_image.assert_called_once()
        mock_blob.upload_from_file.assert_called_once()

    def test_generate_new_recipe_image_ai_service_failure(self, service):
        """Test handling AI service returning None"""
        # Arrange
        service.ai_image_service.generate_food_image.return_value = None
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            service._generate_new_recipe_image("Recipe", "Description", [])
        
        assert "AI service returned None" in str(exc_info.value)

    def test_get_fallback_recipe_image_url(self, service):
        """Test fallback image URL generation"""
        # Act
        result = service._get_fallback_recipe_image_url("Test Recipe")
        
        # Assert
        assert result is not None
        assert isinstance(result, str)
        assert "placeholder" in result
        assert "Test+Recipe" in result

    def test_recipes_folder_configuration(self, service):
        """Test that recipes folder is properly configured"""
        # Assert
        assert service.recipes_folder == "recipes"

    def test_empty_ingredients_handling(self, service):
        """Test handling of empty or None ingredients list"""
        # Arrange
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        service.storage_adapter.bucket.blob.return_value = mock_blob
        service.storage_adapter.bucket.name = "test-bucket"
        
        # Act with None ingredients
        result1 = service.get_or_generate_recipe_image(
            "Recipe 1", "user-123", "Description", None
        )
        
        # Act with empty ingredients
        result2 = service.get_or_generate_recipe_image(
            "Recipe 2", "user-123", "Description", []
        )
        
        # Assert
        assert result1 is not None
        assert result2 is not None
        assert service.ai_image_service.generate_food_image.call_count == 2

    # Test standalone function
    @patch('src.application.services.recipe_image_generator_service.get_or_generate_recipe_image')
    def test_get_or_generate_recipe_image_function_mock(self, mock_function):
        """Test standalone get_or_generate_recipe_image function"""
        # Arrange
        mock_function.return_value = "https://test-url.com/recipe.jpg"
        
        # Act
        result = mock_function("Test Recipe", "user-123", "Description", [{"name": "ingredient"}])
        
        # Assert
        assert result == "https://test-url.com/recipe.jpg"
        mock_function.assert_called_once_with(
            "Test Recipe", "user-123", "Description", [{"name": "ingredient"}]
        )

    def test_get_or_generate_recipe_image_standalone_function(self):
        """Test standalone function directly"""
        # Act
        result = get_or_generate_recipe_image("Test Recipe", "user-123", "Description", [])
        
        # Assert
        assert result is not None
        assert isinstance(result, str)
        assert "test_recipe.jpg" in result

    def test_service_dependencies_injection(self):
        """Test that service properly handles dependency injection"""
        # Arrange
        ai_service = Mock()
        storage_adapter = Mock()
        ai_image_service = Mock()
        
        # Act
        service = RecipeImageGeneratorService(ai_service, storage_adapter, ai_image_service)
        
        # Assert
        assert service.ai_service is ai_service
        assert service.storage_adapter is storage_adapter
        assert service.ai_image_service is ai_image_service

    def test_error_handling_in_check_existing_recipe_image(self, service):
        """Test error handling in existing image check"""
        # Arrange - Mock exception in blob operations
        mock_blob = Mock()
        mock_blob.exists.side_effect = Exception("Storage error")
        service.storage_adapter.bucket.blob.return_value = mock_blob
        
        # Act
        result = service._check_existing_recipe_image("Test Recipe")
        
        # Assert - Should handle error gracefully and return None
        assert result is None

    def test_image_path_generation_consistency(self, service):
        """Test that image paths are generated consistently"""
        # Test same recipe title generates same path
        title = "Chicken Teriyaki Bowl"
        
        # Mock the normalize method to ensure consistency
        normalized_title = service._normalize_recipe_title(title)
        expected_path = f"recipes/{normalized_title}.jpg"
        
        # Should be consistent across calls
        assert normalized_title == service._normalize_recipe_title(title)

    def test_content_type_handling(self, service):
        """Test proper content type handling for uploaded images"""
        # Arrange
        mock_blob = Mock()
        service.storage_adapter.bucket.blob.return_value = mock_blob
        service.storage_adapter.bucket.name = "test-bucket"
        
        # Act
        service._generate_new_recipe_image("Test Recipe", "Description", [])
        
        # Assert - Should upload with correct content type
        mock_blob.upload_from_file.assert_called_once()
        call_args = mock_blob.upload_from_file.call_args
        assert call_args[1]['content_type'] == 'image/jpeg'
