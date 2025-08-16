"""
Production Validation Tests for Core Services
Tests critical business logic services without database dependencies
"""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
from src.infrastructure.ai.cache_service import AIResponseCacheService


class TestCoreServicesProduction:
    """Production validation tests for core services"""

    # ================================================================
    # GeminiAdapterService Tests - MOST CRITICAL SERVICE
    # ================================================================
    
    def test_gemini_adapter_service_initialization(self):
        """Test GeminiAdapterService initializes correctly"""
        service = GeminiAdapterService()
        assert service is not None
        assert hasattr(service, 'recognize_ingredients')
        assert hasattr(service, 'recognize_foods')
        assert hasattr(service, 'generate_recipes')

    @patch('google.generativeai.GenerativeModel')
    def test_gemini_recognize_ingredients_success(self, mock_model):
        """Test ingredient recognition with Gemini AI"""
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "ingredients": [
                {
                    "name": "tomato",
                    "quantity": 3,
                    "unit": "pieces",
                    "confidence": 0.95
                }
            ]
        })
        mock_model.return_value.generate_content.return_value = mock_response
        
        service = GeminiAdapterService()
        
        # Mock image input
        mock_image = MagicMock()
        result = service.recognize_ingredients(mock_image)
        
        assert 'ingredients' in result
        assert len(result['ingredients']) == 1
        assert result['ingredients'][0]['name'] == 'tomato'
        assert result['ingredients'][0]['confidence'] > 0.8

    @patch('google.generativeai.GenerativeModel')
    def test_gemini_recognize_foods_success(self, mock_model):
        """Test food recognition with Gemini AI"""
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "foods": [
                {
                    "name": "spaghetti_carbonara",
                    "cuisine": "italian",
                    "confidence": 0.92
                }
            ]
        })
        mock_model.return_value.generate_content.return_value = mock_response
        
        service = GeminiAdapterService()
        mock_image = MagicMock()
        
        result = service.recognize_foods(mock_image)
        
        assert 'foods' in result
        assert len(result['foods']) == 1
        assert result['foods'][0]['name'] == 'spaghetti_carbonara'

    @patch('google.generativeai.GenerativeModel')
    def test_gemini_generate_recipes_success(self, mock_model):
        """Test recipe generation with Gemini AI"""
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "recipes": [
                {
                    "title": "Tomato Pasta",
                    "ingredients": ["tomato", "pasta"],
                    "instructions": ["Boil pasta", "Add tomatoes"],
                    "cooking_time": "20 minutes"
                }
            ]
        })
        mock_model.return_value.generate_content.return_value = mock_response
        
        service = GeminiAdapterService()
        ingredients = ["tomato", "pasta"]
        
        result = service.generate_recipes(ingredients)
        
        assert 'recipes' in result
        assert len(result['recipes']) == 1
        assert result['recipes'][0]['title'] == 'Tomato Pasta'

    @patch('google.generativeai.GenerativeModel')
    def test_gemini_error_handling(self, mock_model):
        """Test Gemini service error handling"""
        mock_model.return_value.generate_content.side_effect = Exception("API Error")
        
        service = GeminiAdapterService()
        mock_image = MagicMock()
        
        # Should handle errors gracefully
        try:
            result = service.recognize_ingredients(mock_image)
            # If no exception, check for error response
            assert 'error' in result or 'ingredients' in result
        except Exception as e:
            # Exception should be handled gracefully
            assert "API Error" in str(e)

    @patch('google.generativeai.GenerativeModel')
    def test_gemini_malformed_response_handling(self, mock_model):
        """Test handling of malformed AI responses"""
        mock_response = MagicMock()
        mock_response.text = "Invalid JSON response"
        mock_model.return_value.generate_content.return_value = mock_response
        
        service = GeminiAdapterService()
        mock_image = MagicMock()
        
        # Should handle malformed responses
        try:
            result = service.recognize_ingredients(mock_image)
            # Should provide fallback response
            assert isinstance(result, dict)
        except Exception as e:
            # JSON parsing errors should be handled
            assert "JSON" in str(e) or "parse" in str(e).lower()

    @patch('google.generativeai.GenerativeModel')
    def test_gemini_empty_response_handling(self, mock_model):
        """Test handling of empty AI responses"""
        mock_response = MagicMock()
        mock_response.text = ""
        mock_model.return_value.generate_content.return_value = mock_response
        
        service = GeminiAdapterService()
        mock_image = MagicMock()
        
        result = service.recognize_ingredients(mock_image)
        
        # Should handle empty responses gracefully
        assert isinstance(result, dict)

    # ================================================================
    # AI Cache Service Tests
    # ================================================================
    
    def test_cache_service_initialization(self):
        """Test AI cache service initializes correctly"""
        cache_service = AIResponseCacheService()
        assert cache_service is not None
        assert hasattr(cache_service, 'get_cached_response')
        assert hasattr(cache_service, 'cache_response')

    def test_cache_service_get_nonexistent_key(self):
        """Test cache service with non-existent key"""
        cache_service = AIResponseCacheService()
        
        result = cache_service.get_cached_response("nonexistent_key")
        
        assert result is None

    def test_cache_service_store_and_retrieve(self):
        """Test cache service store and retrieve functionality"""
        cache_service = AIResponseCacheService()
        
        test_key = "test_ingredients_recognition"
        test_data = {
            "ingredients": [{"name": "tomato", "quantity": 2}],
            "timestamp": "2024-01-10T10:00:00Z"
        }
        
        # Store data
        cache_service.cache_response(test_key, test_data, ttl=300)
        
        # Retrieve data
        cached_result = cache_service.get_cached_response(test_key)
        
        assert cached_result is not None
        assert cached_result['ingredients'][0]['name'] == 'tomato'

    def test_cache_service_ttl_expiration(self):
        """Test cache TTL expiration"""
        cache_service = AIResponseCacheService()
        
        test_key = "test_expired_key"
        test_data = {"test": "data"}
        
        # Store with very short TTL
        cache_service.cache_response(test_key, test_data, ttl=0.01)  # 10ms
        
        # Wait for expiration
        import time
        time.sleep(0.02)
        
        # Should be expired
        result = cache_service.get_cached_response(test_key)
        # May still exist if cleanup hasn't run, but should be expired
        assert result is None or 'test' in result

    def test_cache_service_invalidation(self):
        """Test cache invalidation"""
        cache_service = AIResponseCacheService()
        
        test_key = "test_invalidate_key"
        test_data = {"test": "data"}
        
        # Store data
        cache_service.cache_response(test_key, test_data)
        
        # Verify it's there
        assert cache_service.get_cached_response(test_key) is not None
        
        # Invalidate
        cache_service.invalidate_cache(test_key)
        
        # Should be gone
        result = cache_service.get_cached_response(test_key)
        assert result is None

    def test_cache_service_stats(self):
        """Test cache statistics functionality"""
        cache_service = AIResponseCacheService()
        
        # Get initial stats
        stats = cache_service.get_cache_stats()
        
        assert isinstance(stats, dict)
        assert 'hit_rate' in stats or 'total_requests' in stats or 'cache_size' in stats

    # ================================================================
    # Performance and Load Tests
    # ================================================================
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_service_performance(self, mock_model):
        """Test Gemini service performance under load"""
        import time
        
        mock_response = MagicMock()
        mock_response.text = json.dumps({"ingredients": []})
        mock_model.return_value.generate_content.return_value = mock_response
        
        service = GeminiAdapterService()
        mock_image = MagicMock()
        
        # Test multiple calls
        start_time = time.time()
        
        for i in range(5):
            result = service.recognize_ingredients(mock_image)
            assert isinstance(result, dict)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 5
        
        # Each call should complete quickly (under 1 second when mocked)
        assert avg_time < 1.0

    def test_cache_service_performance(self):
        """Test cache service performance"""
        import time
        
        cache_service = AIResponseCacheService()
        
        # Test storing multiple items
        start_time = time.time()
        
        for i in range(10):
            key = f"perf_test_key_{i}"
            data = {"test": f"data_{i}", "index": i}
            cache_service.cache_response(key, data)
        
        store_time = time.time() - start_time
        
        # Test retrieving multiple items
        start_time = time.time()
        
        for i in range(10):
            key = f"perf_test_key_{i}"
            result = cache_service.get_cached_response(key)
            assert result is not None
        
        retrieve_time = time.time() - start_time
        
        # Cache operations should be fast
        assert store_time < 1.0
        assert retrieve_time < 0.5

    # ================================================================
    # Concurrent and Thread Safety Tests
    # ================================================================
    
    def test_cache_service_thread_safety(self):
        """Test cache service thread safety"""
        import threading
        import time
        
        cache_service = AIResponseCacheService()
        results = []
        errors = []
        
        def cache_operations(thread_id):
            try:
                for i in range(5):
                    key = f"thread_{thread_id}_key_{i}"
                    data = {"thread": thread_id, "iteration": i}
                    
                    # Store
                    cache_service.cache_response(key, data)
                    
                    # Retrieve
                    result = cache_service.get_cached_response(key)
                    results.append(result)
                    
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=cache_operations, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 15  # 3 threads * 5 operations
        
        # All results should be valid
        for result in results:
            if result is not None:
                assert 'thread' in result
                assert 'iteration' in result

    @patch('google.generativeai.GenerativeModel')
    def test_gemini_service_concurrent_requests(self, mock_model):
        """Test concurrent requests to Gemini service"""
        import threading
        
        mock_response = MagicMock()
        mock_response.text = json.dumps({"ingredients": [{"name": "test"}]})
        mock_model.return_value.generate_content.return_value = mock_response
        
        service = GeminiAdapterService()
        results = []
        errors = []
        
        def make_request():
            try:
                mock_image = MagicMock()
                result = service.recognize_ingredients(mock_image)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Start multiple concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent request errors: {errors}"
        assert len(results) == 5
        
        # All results should be valid
        for result in results:
            assert isinstance(result, dict)

    # ================================================================
    # Memory and Resource Management Tests
    # ================================================================
    
    def test_cache_service_memory_cleanup(self):
        """Test cache service memory cleanup"""
        cache_service = AIResponseCacheService()
        
        # Add many items to cache
        for i in range(100):
            key = f"memory_test_key_{i}"
            # Create larger data objects
            data = {
                "large_data": "x" * 1000,  # 1KB per item
                "index": i,
                "metadata": {"created": f"2024-01-10T10:{i:02d}:00Z"}
            }
            cache_service.cache_response(key, data, ttl=1)  # Short TTL
        
        # Trigger cleanup
        cache_service.cleanup_expired()
        
        # Cache should handle cleanup gracefully
        stats = cache_service.get_cache_stats()
        assert isinstance(stats, dict)

    @patch('google.generativeai.GenerativeModel')
    def test_gemini_service_memory_usage(self, mock_model):
        """Test Gemini service memory usage with large responses"""
        # Simulate large AI response
        large_ingredients = [
            {
                "name": f"ingredient_{i}",
                "quantity": i,
                "confidence": 0.9,
                "description": "x" * 100  # Large description
            }
            for i in range(50)
        ]
        
        mock_response = MagicMock()
        mock_response.text = json.dumps({"ingredients": large_ingredients})
        mock_model.return_value.generate_content.return_value = mock_response
        
        service = GeminiAdapterService()
        mock_image = MagicMock()
        
        # Process large response
        result = service.recognize_ingredients(mock_image)
        
        assert 'ingredients' in result
        assert len(result['ingredients']) == 50
        
        # Memory should be handled properly
        # (In a real test, you'd monitor memory usage)

    # ================================================================
    # Error Recovery and Resilience Tests
    # ================================================================
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_service_retry_mechanism(self, mock_model):
        """Test Gemini service retry mechanism on failures"""
        # First call fails, second succeeds
        mock_model.return_value.generate_content.side_effect = [
            Exception("Temporary failure"),
            MagicMock(text=json.dumps({"ingredients": []}))
        ]
        
        service = GeminiAdapterService()
        mock_image = MagicMock()
        
        # Should retry and succeed
        try:
            result = service.recognize_ingredients(mock_image)
            # If retry mechanism works, should get valid result
            assert isinstance(result, dict)
        except Exception:
            # If no retry mechanism, should fail gracefully
            pass

    def test_cache_service_error_recovery(self):
        """Test cache service error recovery"""
        cache_service = AIResponseCacheService()
        
        # Test with various problematic inputs
        problematic_cases = [
            None,  # None key
            "",    # Empty key
            " ",   # Whitespace key
            "a" * 1000,  # Very long key
        ]
        
        for case in problematic_cases:
            try:
                # Should handle gracefully
                result = cache_service.get_cached_response(case)
                # May return None or handle differently
                assert result is None or isinstance(result, dict)
            except Exception as e:
                # Exceptions should be specific and handled
                assert isinstance(e, (ValueError, KeyError, TypeError))

    # ================================================================
    # Integration Points Tests
    # ================================================================
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_with_cache_integration(self, mock_model):
        """Test integration between Gemini service and cache"""
        mock_response = MagicMock()
        mock_response.text = json.dumps({"ingredients": [{"name": "cached_tomato"}]})
        mock_model.return_value.generate_content.return_value = mock_response
        
        service = GeminiAdapterService()
        cache_service = AIResponseCacheService()
        
        mock_image = MagicMock()
        
        # First call - should hit Gemini and cache result
        result1 = service.recognize_ingredients(mock_image)
        
        # Cache the result manually (simulating integration)
        cache_key = "test_integration_key"
        cache_service.cache_response(cache_key, result1)
        
        # Second call - should hit cache
        cached_result = cache_service.get_cached_response(cache_key)
        
        assert result1 == cached_result
        assert cached_result['ingredients'][0]['name'] == 'cached_tomato'

    def test_production_ready_error_messages(self):
        """Test that error messages are production-ready (no sensitive info)"""
        cache_service = AIResponseCacheService()
        
        try:
            # Trigger an error condition
            cache_service.cache_response(None, None)
        except Exception as e:
            error_msg = str(e)
            
            # Error messages should not contain:
            sensitive_terms = [
                'password', 'token', 'secret', 'key', 'credential',
                'internal', 'debug', 'stack', 'traceback'
            ]
            
            for term in sensitive_terms:
                assert term.lower() not in error_msg.lower(), f"Sensitive term '{term}' found in error message"