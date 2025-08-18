"""
Unit tests for Infrastructure Services
Tests AI adapters, storage services, and security services
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


class TestInfrastructureServices:
    """Test suite for Infrastructure Services"""

    # Firebase Storage Adapter Tests
    @patch('src.infrastructure.firebase.firebase_storage_adapter.bucket')
    def test_firebase_storage_upload_success(self, mock_bucket):
        """Test successful file upload to Firebase Storage"""
        # Arrange
        from src.infrastructure.firebase.firebase_storage_adapter import FirebaseStorageAdapter
        
        mock_blob = Mock()
        mock_blob.public_url = "https://storage.googleapis.com/test-bucket/test-file.jpg"
        mock_bucket.blob.return_value = mock_blob
        
        storage_adapter = FirebaseStorageAdapter()
        
        # Act
        result = storage_adapter.upload_file("test-file.jpg", b"test-content", "image/jpeg")
        
        # Assert
        assert "public_url" in result
        assert result["public_url"] == "https://storage.googleapis.com/test-bucket/test-file.jpg"
        mock_blob.upload_from_string.assert_called_once()

    @patch('src.infrastructure.firebase.firebase_storage_adapter.bucket')
    def test_firebase_storage_upload_failure(self, mock_bucket):
        """Test Firebase Storage upload failure handling"""
        # Arrange
        from src.infrastructure.firebase.firebase_storage_adapter import FirebaseStorageAdapter
        
        mock_bucket.blob.side_effect = Exception("Storage error")
        storage_adapter = FirebaseStorageAdapter()
        
        # Act & Assert
        with pytest.raises(Exception):
            storage_adapter.upload_file("test-file.jpg", b"test-content", "image/jpeg")

    @patch('src.infrastructure.firebase.firebase_storage_adapter.bucket')
    def test_firebase_storage_delete_success(self, mock_bucket):
        """Test successful file deletion from Firebase Storage"""
        # Arrange
        from src.infrastructure.firebase.firebase_storage_adapter import FirebaseStorageAdapter
        
        mock_blob = Mock()
        mock_bucket.blob.return_value = mock_blob
        
        storage_adapter = FirebaseStorageAdapter()
        
        # Act
        result = storage_adapter.delete_file("test-file.jpg")
        
        # Assert
        assert result is True
        mock_blob.delete.assert_called_once()

    # AI Adapter Service Tests
    @patch('src.infrastructure.ai.gemini_adapter_service.genai')
    def test_gemini_adapter_recognize_ingredients(self, mock_genai):
        """Test Gemini AI ingredient recognition"""
        # Arrange
        from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '{"ingredients": [{"name": "Tomato", "confidence": 0.95}]}'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        ai_service = GeminiAdapterService()
        
        # Act
        result = ai_service.recognize_ingredients(["test-image.jpg"])
        
        # Assert
        assert "ingredients" in result
        assert len(result["ingredients"]) == 1
        assert result["ingredients"][0]["name"] == "Tomato"
        mock_model.generate_content.assert_called()

    @patch('src.infrastructure.ai.gemini_adapter_service.genai')
    def test_gemini_adapter_generate_recipe(self, mock_genai):
        """Test Gemini AI recipe generation"""
        # Arrange
        from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '{"title": "Tomato Soup", "ingredients": ["Tomato"], "steps": ["Cook tomatoes"]}'
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        ai_service = GeminiAdapterService()
        
        # Act
        result = ai_service.generate_recipe({"ingredients": ["Tomato"]})
        
        # Assert
        assert "title" in result
        assert result["title"] == "Tomato Soup"
        mock_model.generate_content.assert_called()

    def test_gemini_adapter_invalid_json_response(self):
        """Test handling of invalid JSON response from Gemini"""
        # Arrange
        with patch('src.infrastructure.ai.gemini_adapter_service.genai') as mock_genai:
            mock_model = Mock()
            mock_response = Mock()
            mock_response.text = "Invalid JSON response"
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model
            
            from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
            ai_service = GeminiAdapterService()
            
            # Act & Assert
            with pytest.raises(Exception):
                ai_service.recognize_ingredients(["test.jpg"])

    # JWT Service Tests
    def test_jwt_service_create_token(self):
        """Test JWT token creation"""
        # Arrange
        from src.infrastructure.auth.jwt_service import JWTService
        
        jwt_service = JWTService()
        user_data = {"uid": "user_123", "email": "test@example.com"}
        
        # Act
        token = jwt_service.create_access_token(user_data)
        
        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically longer

    def test_jwt_service_verify_token(self):
        """Test JWT token verification"""
        # Arrange
        from src.infrastructure.auth.jwt_service import JWTService
        
        jwt_service = JWTService()
        user_data = {"uid": "user_123", "email": "test@example.com"}
        token = jwt_service.create_access_token(user_data)
        
        # Act
        decoded_data = jwt_service.decode_token(token)
        
        # Assert
        assert decoded_data["uid"] == "user_123"
        assert decoded_data["email"] == "test@example.com"

    def test_jwt_service_invalid_token(self):
        """Test JWT service with invalid token"""
        # Arrange
        from src.infrastructure.auth.jwt_service import JWTService
        
        jwt_service = JWTService()
        invalid_token = "invalid.token.here"
        
        # Act & Assert
        with pytest.raises(Exception):
            jwt_service.decode_token(invalid_token)

    def test_jwt_service_expired_token(self):
        """Test JWT service with expired token"""
        # Arrange
        from src.infrastructure.auth.jwt_service import JWTService
        
        jwt_service = JWTService()
        user_data = {"uid": "user_123", "email": "test@example.com"}
        
        # Create token with very short expiry
        with patch('src.infrastructure.auth.jwt_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.utcnow() - timedelta(days=1)
            token = jwt_service.create_access_token(user_data)
        
        # Act & Assert
        with pytest.raises(Exception):
            jwt_service.decode_token(token)

    # Security Service Tests
    @patch('src.infrastructure.security.rate_limiter.redis_client')
    def test_rate_limiter_allow_request(self, mock_redis):
        """Test rate limiter allows requests within limits"""
        # Arrange
        from src.infrastructure.security.rate_limiter import RateLimiter
        
        mock_redis.get.return_value = b'5'  # 5 requests made
        mock_redis.incr.return_value = 6
        mock_redis.expire.return_value = True
        
        rate_limiter = RateLimiter(limit=10, window=60)
        
        # Act
        result = rate_limiter.is_allowed("user_123")
        
        # Assert
        assert result is True
        mock_redis.incr.assert_called()

    @patch('src.infrastructure.security.rate_limiter.redis_client')
    def test_rate_limiter_block_request(self, mock_redis):
        """Test rate limiter blocks requests exceeding limits"""
        # Arrange
        from src.infrastructure.security.rate_limiter import RateLimiter
        
        mock_redis.get.return_value = b'10'  # 10 requests made (at limit)
        
        rate_limiter = RateLimiter(limit=10, window=60)
        
        # Act
        result = rate_limiter.is_allowed("user_123")
        
        # Assert
        assert result is False

    # Mise en Place Service Tests
    def test_mise_en_place_service_organization(self):
        """Test mise en place service ingredient organization"""
        # Arrange
        from src.infrastructure.services.mise_en_place_service import MiseEnPlaceService
        
        service = MiseEnPlaceService()
        ingredients = [
            {"name": "Tomato", "category": "vegetable"},
            {"name": "Onion", "category": "vegetable"},
            {"name": "Salt", "category": "seasoning"}
        ]
        
        # Act
        organized = service.organize_ingredients(ingredients)
        
        # Assert
        assert "vegetable" in organized
        assert "seasoning" in organized
        assert len(organized["vegetable"]) == 2

    def test_mise_en_place_service_preparation_steps(self):
        """Test mise en place service preparation step generation"""
        # Arrange
        from src.infrastructure.services.mise_en_place_service import MiseEnPlaceService
        
        service = MiseEnPlaceService()
        recipe_data = {
            "ingredients": ["Tomato", "Onion"],
            "cooking_method": "sauté"
        }
        
        # Act
        steps = service.generate_preparation_steps(recipe_data)
        
        # Assert
        assert isinstance(steps, list)
        assert len(steps) > 0

    # Idempotency Service Tests
    def test_idempotency_service_key_generation(self):
        """Test idempotency service key generation"""
        # Arrange
        from src.infrastructure.services.idempotency_service import IdempotencyService
        
        service = IdempotencyService()
        request_data = {"user_id": "123", "action": "create_recipe"}
        
        # Act
        key = service.generate_key(request_data)
        
        # Assert
        assert isinstance(key, str)
        assert len(key) > 10

    def test_idempotency_service_duplicate_detection(self):
        """Test idempotency service duplicate request detection"""
        # Arrange
        from src.infrastructure.services.idempotency_service import IdempotencyService
        
        service = IdempotencyService()
        request_data = {"user_id": "123", "action": "create_recipe"}
        
        # Act
        first_check = service.is_duplicate_request(request_data)
        service.mark_request_processed(request_data)
        second_check = service.is_duplicate_request(request_data)
        
        # Assert
        assert first_check is False
        assert second_check is True

    # AI Cache Service Tests
    @patch('src.infrastructure.ai.cache_service.redis_client')
    def test_ai_cache_service_cache_result(self, mock_redis):
        """Test AI cache service result caching"""
        # Arrange
        from src.infrastructure.ai.cache_service import CacheService
        
        mock_redis.set.return_value = True
        service = CacheService()
        
        # Act
        result = service.cache_ai_result("test_key", {"result": "success"}, ttl=300)
        
        # Assert
        assert result is True
        mock_redis.set.assert_called()

    @patch('src.infrastructure.ai.cache_service.redis_client')
    def test_ai_cache_service_get_cached(self, mock_redis):
        """Test AI cache service cached result retrieval"""
        # Arrange
        from src.infrastructure.ai.cache_service import CacheService
        
        mock_redis.get.return_value = b'{"result": "cached_success"}'
        service = CacheService()
        
        # Act
        result = service.get_cached_result("test_key")
        
        # Assert
        assert result["result"] == "cached_success"
        mock_redis.get.assert_called_with("test_key")

    # Performance Monitor Tests
    def test_performance_monitor_timing(self):
        """Test performance monitor execution timing"""
        # Arrange
        from src.infrastructure.ai.performance_monitor import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Act
        with monitor.measure_execution("test_operation"):
            import time
            time.sleep(0.1)  # Simulate operation
        
        metrics = monitor.get_metrics("test_operation")
        
        # Assert
        assert metrics["execution_time"] >= 0.1
        assert metrics["call_count"] == 1

    def test_performance_monitor_memory_tracking(self):
        """Test performance monitor memory usage tracking"""
        # Arrange
        from src.infrastructure.ai.performance_monitor import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # Act
        initial_memory = monitor.get_current_memory_usage()
        
        # Create some data to use memory
        test_data = [i for i in range(10000)]
        current_memory = monitor.get_current_memory_usage()
        
        # Assert
        assert current_memory >= initial_memory
        assert isinstance(current_memory, (int, float))
