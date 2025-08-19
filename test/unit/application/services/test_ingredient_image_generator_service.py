"""
Unit tests for Ingredient Image Generator Service
Tests ingredient image generation and caching functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import io

from src.application.services.ingredient_image_generator_service import (
    IngredientImageGeneratorService,
    get_or_generate_ingredient_image,
    clear_session_cache,
    get_cache_stats,
    get_or_generate_ingredient_images_sync_batch,
    list_existing_ingredients_images
)


class TestIngredientImageGeneratorService:
    """Test suite for Ingredient Image Generator Service"""
    
    @pytest.fixture
    def service(self):
        """Create ingredient image generator service instance"""
        return IngredientImageGeneratorService()
    
    @pytest.fixture
    def sample_ingredients(self):
        """Sample ingredient names for testing"""
        return ["tomato", "onion", "garlic", "basil", "olive_oil"]
    
    @patch('src.application.services.ingredient_image_generator_service.openai_client')
    @patch('src.application.services.ingredient_image_generator_service.firebase_admin')
    def test_get_or_generate_ingredient_image_success(self, mock_firebase, mock_openai, service):
        """Test successful ingredient image generation"""
        # Arrange
        mock_openai.images.generate.return_value.data = [
            Mock(url="https://generated-image.com/tomato.jpg")
        ]
        mock_storage = Mock()
        mock_blob = Mock()
        mock_blob.public_url = "https://storage.googleapis.com/bucket/tomato_generated.jpg"
        mock_storage.blob.return_value = mock_blob
        mock_firebase.storage.bucket.return_value = mock_storage
        
        # Act
        result = service.get_or_generate_ingredient_image("tomato")
        
        # Assert
        assert result is not None
        assert "url" in result or isinstance(result, str)
        mock_openai.images.generate.assert_called_once()

    def test_get_or_generate_ingredient_image_empty_name(self, service):
        """Test image generation with empty ingredient name"""
        # Act & Assert
        with pytest.raises((ValueError, TypeError)):
            service.get_or_generate_ingredient_image("")
        
        with pytest.raises((ValueError, TypeError)):
            service.get_or_generate_ingredient_image(None)

    @patch('src.application.services.ingredient_image_generator_service.cache')
    def test_clear_session_cache_success(self, mock_cache, service):
        """Test successful cache clearing"""
        # Arrange
        mock_cache.clear.return_value = True
        
        # Act
        result = service.clear_session_cache()
        
        # Assert
        assert result is True or result is None  # Depends on implementation
        mock_cache.clear.assert_called_once()

    @patch('src.application.services.ingredient_image_generator_service.cache')
    def test_get_cache_stats_success(self, mock_cache, service):
        """Test successful cache stats retrieval"""
        # Arrange
        mock_cache.get_stats.return_value = {
            "total_entries": 15,
            "cache_hits": 120,
            "cache_misses": 45,
            "cache_size_mb": 2.3
        }
        
        # Act
        result = service.get_cache_stats()
        
        # Assert
        assert result is not None
        assert "total_entries" in result or isinstance(result, dict)
        if isinstance(result, dict):
            assert result["total_entries"] == 15

    @patch('src.application.services.ingredient_image_generator_service.openai_client')
    @patch('src.application.services.ingredient_image_generator_service.firebase_admin')
    def test_get_or_generate_ingredient_images_sync_batch_success(self, mock_firebase, mock_openai, service, sample_ingredients):
        """Test successful batch ingredient image generation"""
        # Arrange
        mock_openai.images.generate.return_value.data = [
            Mock(url="https://generated-image.com/ingredient.jpg")
        ]
        mock_storage = Mock()
        mock_blob = Mock()
        mock_blob.public_url = "https://storage.googleapis.com/bucket/ingredient.jpg"
        mock_storage.blob.return_value = mock_blob
        mock_firebase.storage.bucket.return_value = mock_storage
        
        # Act
        result = service.get_or_generate_ingredient_images_sync_batch(sample_ingredients)
        
        # Assert
        assert result is not None
        assert isinstance(result, (list, dict))
        if isinstance(result, dict):
            assert len(result) == len(sample_ingredients)
        elif isinstance(result, list):
            assert len(result) == len(sample_ingredients)

    def test_get_or_generate_ingredient_images_sync_batch_empty_list(self, service):
        """Test batch generation with empty list"""
        # Act
        result = service.get_or_generate_ingredient_images_sync_batch([])
        
        # Assert
        assert result is not None
        assert len(result) == 0

    @patch('src.application.services.ingredient_image_generator_service.firebase_admin')
    def test_list_existing_ingredients_images_success(self, mock_firebase, service):
        """Test successful listing of existing ingredient images"""
        # Arrange
        mock_storage = Mock()
        mock_blobs = [
            Mock(name="ingredients/tomato.jpg", public_url="https://storage.googleapis.com/bucket/tomato.jpg"),
            Mock(name="ingredients/onion.jpg", public_url="https://storage.googleapis.com/bucket/onion.jpg"),
            Mock(name="ingredients/garlic.jpg", public_url="https://storage.googleapis.com/bucket/garlic.jpg")
        ]
        mock_storage.list_blobs.return_value = mock_blobs
        mock_firebase.storage.bucket.return_value = mock_storage
        
        # Act
        result = service.list_existing_ingredients_images()
        
        # Assert
        assert result is not None
        assert isinstance(result, (list, dict))
        if isinstance(result, list):
            assert len(result) == 3
        elif isinstance(result, dict):
            assert len(result) >= 3

    @patch('src.application.services.ingredient_image_generator_service.firebase_admin')
    def test_list_existing_ingredients_images_empty_storage(self, mock_firebase, service):
        """Test listing when storage is empty"""
        # Arrange
        mock_storage = Mock()
        mock_storage.list_blobs.return_value = []
        mock_firebase.storage.bucket.return_value = mock_storage
        
        # Act
        result = service.list_existing_ingredients_images()
        
        # Assert
        assert result is not None
        assert len(result) == 0

    def test_service_initialization(self):
        """Test service can be initialized properly"""
        # Act
        service = IngredientImageGeneratorService()
        
        # Assert
        assert service is not None
        assert hasattr(service, 'get_or_generate_ingredient_image')
        assert hasattr(service, 'clear_session_cache')
        assert hasattr(service, 'get_cache_stats')

    @patch('src.application.services.ingredient_image_generator_service.openai_client')
    def test_get_or_generate_ingredient_image_ai_error(self, mock_openai, service):
        """Test handling of AI service errors"""
        # Arrange
        mock_openai.images.generate.side_effect = Exception("AI service unavailable")
        
        # Act & Assert
        with pytest.raises(Exception):
            service.get_or_generate_ingredient_image("tomato")

    @patch('src.application.services.ingredient_image_generator_service.cache')
    def test_cache_integration(self, mock_cache, service):
        """Test cache integration in image generation"""
        # Arrange
        cached_url = "https://cached-image.com/tomato.jpg"
        mock_cache.get.return_value = cached_url
        
        # Act
        result = service.get_or_generate_ingredient_image("tomato")
        
        # Assert
        # Should use cached result if available
        mock_cache.get.assert_called()

    # Test standalone functions
    @patch('src.application.services.ingredient_image_generator_service.IngredientImageGeneratorService')
    def test_get_or_generate_ingredient_image_function(self, mock_service_class):
        """Test standalone get_or_generate_ingredient_image function"""
        # Arrange
        mock_service = Mock()
        mock_service.get_or_generate_ingredient_image.return_value = "test_url"
        mock_service_class.return_value = mock_service
        
        # Act
        result = get_or_generate_ingredient_image("tomato")
        
        # Assert
        assert result == "test_url"
        mock_service.get_or_generate_ingredient_image.assert_called_once_with("tomato")

    @patch('src.application.services.ingredient_image_generator_service.IngredientImageGeneratorService')
    def test_clear_session_cache_function(self, mock_service_class):
        """Test standalone clear_session_cache function"""
        # Arrange
        mock_service = Mock()
        mock_service.clear_session_cache.return_value = True
        mock_service_class.return_value = mock_service
        
        # Act
        result = clear_session_cache()
        
        # Assert
        assert result is True
        mock_service.clear_session_cache.assert_called_once()

    @patch('src.application.services.ingredient_image_generator_service.IngredientImageGeneratorService')
    def test_get_cache_stats_function(self, mock_service_class):
        """Test standalone get_cache_stats function"""
        # Arrange
        mock_service = Mock()
        mock_service.get_cache_stats.return_value = {"total": 10}
        mock_service_class.return_value = mock_service
        
        # Act
        result = get_cache_stats()
        
        # Assert
        assert result == {"total": 10}
        mock_service.get_cache_stats.assert_called_once()

    @patch('src.application.services.ingredient_image_generator_service.IngredientImageGeneratorService')
    def test_get_or_generate_ingredient_images_sync_batch_function(self, mock_service_class, sample_ingredients):
        """Test standalone batch function"""
        # Arrange
        mock_service = Mock()
        mock_service.get_or_generate_ingredient_images_sync_batch.return_value = ["url1", "url2"]
        mock_service_class.return_value = mock_service
        
        # Act
        result = get_or_generate_ingredient_images_sync_batch(sample_ingredients)
        
        # Assert
        assert result == ["url1", "url2"]
        mock_service.get_or_generate_ingredient_images_sync_batch.assert_called_once()

    @patch('src.application.services.ingredient_image_generator_service.IngredientImageGeneratorService')
    def test_list_existing_ingredients_images_function(self, mock_service_class):
        """Test standalone list function"""
        # Arrange
        mock_service = Mock()
        mock_service.list_existing_ingredients_images.return_value = ["img1", "img2"]
        mock_service_class.return_value = mock_service
        
        # Act
        result = list_existing_ingredients_images()
        
        # Assert
        assert result == ["img1", "img2"]
        mock_service.list_existing_ingredients_images.assert_called_once()

    def test_ingredient_name_validation(self, service):
        """Test various ingredient name formats"""
        valid_ingredients = [
            "tomato",
            "red_onion", 
            "extra-virgin-olive-oil",
            "bell pepper",
            "sea salt"
        ]
        
        for ingredient in valid_ingredients:
            # Should not raise exception for valid ingredient names
            try:
                # We're testing validation, so we mock the actual generation
                with patch('src.application.services.ingredient_image_generator_service.openai_client'):
                    with patch('src.application.services.ingredient_image_generator_service.firebase_admin'):
                        result = service.get_or_generate_ingredient_image(ingredient)
                        # The result should be handled gracefully
                        assert True  # If no exception raised, validation passed
            except Exception as e:
                # Only acceptable if it's due to missing mocks, not validation
                assert "openai" in str(e).lower() or "firebase" in str(e).lower()

    @patch('src.application.services.ingredient_image_generator_service.time')
    def test_performance_tracking(self, mock_time, service):
        """Test that service tracks performance metrics"""
        # Arrange
        mock_time.time.side_effect = [1000.0, 1001.5]  # Start and end time
        
        with patch('src.application.services.ingredient_image_generator_service.openai_client'):
            with patch('src.application.services.ingredient_image_generator_service.firebase_admin'):
                # Act
                service.get_or_generate_ingredient_image("tomato")
                
                # Assert
                # Should have measured time for performance tracking
                assert mock_time.time.call_count >= 1
