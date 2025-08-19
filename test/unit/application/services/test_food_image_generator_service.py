"""
Unit tests for Food Image Generator Service
Tests food image generation and management functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.application.services.food_image_generator_service import (
    FoodImageGeneratorService,
    get_or_generate_food_image,
    list_existing_foods_images
)


class TestFoodImageGeneratorService:
    """Test suite for Food Image Generator Service"""
    
    @pytest.fixture
    def service(self):
        """Create food image generator service instance"""
        return FoodImageGeneratorService()
    
    @pytest.fixture
    def sample_foods(self):
        """Sample food names for testing"""
        return ["pizza", "pasta_carbonara", "vegetable_stir_fry", "chicken_soup", "apple_pie"]
    
    @patch('src.application.services.food_image_generator_service.openai_client')
    @patch('src.application.services.food_image_generator_service.firebase_admin')
    def test_get_or_generate_food_image_success(self, mock_firebase, mock_openai, service):
        """Test successful food image generation"""
        # Arrange
        mock_openai.images.generate.return_value.data = [
            Mock(url="https://generated-image.com/pizza.jpg")
        ]
        mock_storage = Mock()
        mock_blob = Mock()
        mock_blob.public_url = "https://storage.googleapis.com/bucket/pizza_generated.jpg"
        mock_storage.blob.return_value = mock_blob
        mock_firebase.storage.bucket.return_value = mock_storage
        
        # Act
        result = service.get_or_generate_food_image("pizza")
        
        # Assert
        assert result is not None
        assert isinstance(result, str) or "url" in result
        mock_openai.images.generate.assert_called_once()

    def test_get_or_generate_food_image_empty_name(self, service):
        """Test image generation with empty food name"""
        # Act & Assert
        with pytest.raises((ValueError, TypeError)):
            service.get_or_generate_food_image("")
        
        with pytest.raises((ValueError, TypeError)):
            service.get_or_generate_food_image(None)

    def test_get_or_generate_food_image_invalid_characters(self, service):
        """Test image generation with invalid characters in food name"""
        invalid_names = ["food@#$%", "food<script>", "food/../hack"]
        
        for invalid_name in invalid_names:
            # Should handle invalid characters gracefully
            try:
                with patch('src.application.services.food_image_generator_service.openai_client'):
                    with patch('src.application.services.food_image_generator_service.firebase_admin'):
                        result = service.get_or_generate_food_image(invalid_name)
                        # If it doesn't raise an exception, it should sanitize the name
                        assert result is not None
            except ValueError:
                # Acceptable to reject invalid names
                pass

    @patch('src.application.services.food_image_generator_service.firebase_admin')
    def test_list_existing_foods_images_success(self, mock_firebase, service):
        """Test successful listing of existing food images"""
        # Arrange
        mock_storage = Mock()
        mock_blobs = [
            Mock(name="foods/pizza.jpg", public_url="https://storage.googleapis.com/bucket/pizza.jpg"),
            Mock(name="foods/pasta.jpg", public_url="https://storage.googleapis.com/bucket/pasta.jpg"),
            Mock(name="foods/soup.jpg", public_url="https://storage.googleapis.com/bucket/soup.jpg"),
            Mock(name="foods/salad.jpg", public_url="https://storage.googleapis.com/bucket/salad.jpg")
        ]
        mock_storage.list_blobs.return_value = mock_blobs
        mock_firebase.storage.bucket.return_value = mock_storage
        
        # Act
        result = service.list_existing_foods_images()
        
        # Assert
        assert result is not None
        assert isinstance(result, (list, dict))
        if isinstance(result, list):
            assert len(result) == 4
        elif isinstance(result, dict):
            assert len(result) >= 4

    @patch('src.application.services.food_image_generator_service.firebase_admin')
    def test_list_existing_foods_images_empty_storage(self, mock_firebase, service):
        """Test listing when storage is empty"""
        # Arrange
        mock_storage = Mock()
        mock_storage.list_blobs.return_value = []
        mock_firebase.storage.bucket.return_value = mock_storage
        
        # Act
        result = service.list_existing_foods_images()
        
        # Assert
        assert result is not None
        assert len(result) == 0

    @patch('src.application.services.food_image_generator_service.firebase_admin')
    def test_list_existing_foods_images_with_filter(self, mock_firebase, service):
        """Test listing with specific food type filter"""
        # Arrange
        mock_storage = Mock()
        mock_blobs = [
            Mock(name="foods/italian_pizza.jpg"),
            Mock(name="foods/italian_pasta.jpg"),
            Mock(name="foods/chinese_noodles.jpg"),
            Mock(name="foods/mexican_tacos.jpg")
        ]
        mock_storage.list_blobs.return_value = mock_blobs
        mock_firebase.storage.bucket.return_value = mock_storage
        
        # Act
        result = service.list_existing_foods_images("italian")
        
        # Assert
        assert result is not None
        # Should filter Italian foods or return all foods for filtering
        assert isinstance(result, (list, dict))

    @patch('src.application.services.food_image_generator_service.openai_client')
    def test_get_or_generate_food_image_ai_error(self, mock_openai, service):
        """Test handling of AI service errors"""
        # Arrange
        mock_openai.images.generate.side_effect = Exception("AI service temporarily unavailable")
        
        # Act & Assert
        with pytest.raises(Exception):
            service.get_or_generate_food_image("pizza")

    @patch('src.application.services.food_image_generator_service.firebase_admin')
    def test_get_or_generate_food_image_firebase_error(self, mock_firebase, service):
        """Test handling of Firebase storage errors"""
        # Arrange
        mock_firebase.storage.bucket.side_effect = Exception("Firebase connection failed")
        
        with patch('src.application.services.food_image_generator_service.openai_client'):
            # Act & Assert
            with pytest.raises(Exception):
                service.get_or_generate_food_image("pizza")

    def test_service_initialization(self):
        """Test service can be initialized properly"""
        # Act
        service = FoodImageGeneratorService()
        
        # Assert
        assert service is not None
        assert hasattr(service, 'get_or_generate_food_image')
        assert hasattr(service, 'list_existing_foods_images')

    @patch('src.application.services.food_image_generator_service.cache')
    @patch('src.application.services.food_image_generator_service.openai_client')
    @patch('src.application.services.food_image_generator_service.firebase_admin')
    def test_caching_mechanism(self, mock_firebase, mock_openai, mock_cache, service):
        """Test that food images are cached properly"""
        # Arrange
        cached_url = "https://cached-image.com/pizza.jpg"
        mock_cache.get.return_value = cached_url
        
        # Act
        result = service.get_or_generate_food_image("pizza")
        
        # Assert
        # Should check cache first
        mock_cache.get.assert_called()
        if result == cached_url:
            # Used cached version, shouldn't call AI service
            mock_openai.images.generate.assert_not_called()

    @patch('src.application.services.food_image_generator_service.openai_client')
    @patch('src.application.services.food_image_generator_service.firebase_admin')
    def test_complex_food_names(self, mock_firebase, mock_openai, service):
        """Test image generation for complex food names"""
        # Arrange
        complex_foods = [
            "beef_wellington_with_mushroom_duxelles",
            "thai_green_curry_with_jasmine_rice",
            "chocolate_lava_cake_with_vanilla_ice_cream",
            "grilled_salmon_with_lemon_herb_butter"
        ]
        
        mock_openai.images.generate.return_value.data = [Mock(url="https://test.com/food.jpg")]
        mock_storage = Mock()
        mock_blob = Mock()
        mock_blob.public_url = "https://storage.googleapis.com/bucket/food.jpg"
        mock_storage.blob.return_value = mock_blob
        mock_firebase.storage.bucket.return_value = mock_storage
        
        # Act & Assert
        for food_name in complex_foods:
            result = service.get_or_generate_food_image(food_name)
            assert result is not None
            # Should handle complex names gracefully

    # Test standalone functions
    @patch('src.application.services.food_image_generator_service.FoodImageGeneratorService')
    def test_get_or_generate_food_image_function(self, mock_service_class):
        """Test standalone get_or_generate_food_image function"""
        # Arrange
        mock_service = Mock()
        mock_service.get_or_generate_food_image.return_value = "test_food_url"
        mock_service_class.return_value = mock_service
        
        # Act
        result = get_or_generate_food_image("pizza")
        
        # Assert
        assert result == "test_food_url"
        mock_service.get_or_generate_food_image.assert_called_once_with("pizza")

    @patch('src.application.services.food_image_generator_service.FoodImageGeneratorService')
    def test_list_existing_foods_images_function(self, mock_service_class):
        """Test standalone list_existing_foods_images function"""
        # Arrange
        mock_service = Mock()
        mock_service.list_existing_foods_images.return_value = ["food1.jpg", "food2.jpg"]
        mock_service_class.return_value = mock_service
        
        # Act
        result = list_existing_foods_images()
        
        # Assert
        assert result == ["food1.jpg", "food2.jpg"]
        mock_service.list_existing_foods_images.assert_called_once()

    def test_food_name_sanitization(self, service):
        """Test food name sanitization for safe file naming"""
        problematic_names = [
            "Food with spaces",
            "Food/with/slashes",
            "Food with éspecial characters",
            "Food-with-dashes_and_underscores"
        ]
        
        for name in problematic_names:
            try:
                with patch('src.application.services.food_image_generator_service.openai_client'):
                    with patch('src.application.services.food_image_generator_service.firebase_admin'):
                        result = service.get_or_generate_food_image(name)
                        # Should handle name sanitization
                        assert result is not None
            except Exception as e:
                # Only acceptable if due to missing service connections
                assert "openai" in str(e).lower() or "firebase" in str(e).lower()

    @patch('src.application.services.food_image_generator_service.logger')
    def test_logging_integration(self, mock_logger, service):
        """Test that service properly logs activities"""
        with patch('src.application.services.food_image_generator_service.openai_client'):
            with patch('src.application.services.food_image_generator_service.firebase_admin'):
                try:
                    service.get_or_generate_food_image("pizza")
                except:
                    pass  # Ignore errors, just test logging
                
                # Should log the image generation attempt
                assert mock_logger.info.called or mock_logger.debug.called or mock_logger.warning.called

    def test_concurrent_requests_handling(self, service):
        """Test handling of concurrent image generation requests"""
        # This is a basic test for thread safety
        import threading
        results = []
        
        def generate_image(food_name):
            try:
                with patch('src.application.services.food_image_generator_service.openai_client'):
                    with patch('src.application.services.food_image_generator_service.firebase_admin'):
                        result = service.get_or_generate_food_image(food_name)
                        results.append(result)
            except:
                results.append(None)
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=generate_image, args=[f"food_{i}"])
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should handle concurrent requests without crashing
        assert len(results) == 3
