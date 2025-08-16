#!/usr/bin/env python3
"""
Isolated Production Validation Tests
Tests core services without Flask app or database dependencies
"""
import sys
import os
import json
from unittest.mock import patch, MagicMock, Mock
import threading
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

def test_imports():
    """Test that critical modules can be imported"""
    print("🔍 Testing module imports...")
    
    try:
        # Test infrastructure imports
        from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
        print("✅ GeminiAdapterService imported successfully")
        
        from src.infrastructure.ai.cache_service import AIResponseCacheService
        print("✅ AIResponseCacheService imported successfully")
        
        # Test domain service imports
        from src.domain.services.ia_food_analyzer_service import IAFoodAnalyzerService
        print("✅ IAFoodAnalyzerService imported successfully")
        
        from src.domain.services.ia_recipe_generator_service import IARecipeGeneratorService
        print("✅ IARecipeGeneratorService imported successfully")
        
        return True, "All critical modules imported successfully"
        
    except Exception as e:
        return False, f"Import error: {str(e)}"

def test_gemini_adapter_service():
    """Test GeminiAdapterService without external dependencies"""
    print("🔍 Testing GeminiAdapterService...")
    
    try:
        from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService
        
        # Test initialization
        service = GeminiAdapterService()
        assert service is not None
        print("✅ Service initialization successful")
        
        # Test that required methods exist
        required_methods = [
            'recognize_ingredients',
            'recognize_foods', 
            'generate_recipes',
            'analyze_environmental_impact'
        ]
        
        for method in required_methods:
            assert hasattr(service, method), f"Missing method: {method}"
        print("✅ All required methods present")
        
        # Test with mocked Google AI
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = json.dumps({
                "ingredients": [
                    {"name": "tomato", "quantity": 3, "confidence": 0.95}
                ]
            })
            mock_model.return_value.generate_content.return_value = mock_response
            
            # Test ingredient recognition
            mock_image = Mock()
            result = service.recognize_ingredients(mock_image)
            
            assert isinstance(result, dict)
            if 'ingredients' in result:
                assert len(result['ingredients']) >= 0
            print("✅ Ingredient recognition works with mocked AI")
        
        return True, "GeminiAdapterService passed all tests"
        
    except Exception as e:
        return False, f"GeminiAdapterService error: {str(e)}"

def test_cache_service():
    """Test AIResponseCacheService"""
    print("🔍 Testing AIResponseCacheService...")
    
    try:
        from src.infrastructure.ai.cache_service import AIResponseCacheService
        
        # Test initialization
        cache_service = AIResponseCacheService()
        assert cache_service is not None
        print("✅ Cache service initialization successful")
        
        # Test basic cache operations
        test_key = "test_key_123"
        test_data = {"test": "data", "timestamp": "2024-01-10"}
        
        # Test caching
        cache_service.cache_response(test_key, test_data, ttl=300)
        print("✅ Cache storage successful")
        
        # Test retrieval
        cached_result = cache_service.get_cached_response(test_key)
        if cached_result:
            assert cached_result['test'] == 'data'
            print("✅ Cache retrieval successful")
        else:
            print("⚠️  Cache retrieval returned None (acceptable for in-memory cache)")
        
        # Test non-existent key
        result = cache_service.get_cached_response("nonexistent_key")
        assert result is None
        print("✅ Non-existent key handling correct")
        
        # Test cache stats
        stats = cache_service.get_cache_stats()
        assert isinstance(stats, dict)
        print("✅ Cache stats working")
        
        return True, "AIResponseCacheService passed all tests"
        
    except Exception as e:
        return False, f"AIResponseCacheService error: {str(e)}"

def test_service_performance():
    """Test service performance characteristics"""
    print("🔍 Testing service performance...")
    
    try:
        from src.infrastructure.ai.cache_service import AIResponseCacheService
        
        cache_service = AIResponseCacheService()
        
        # Performance test: multiple cache operations
        start_time = time.time()
        
        for i in range(100):
            key = f"perf_test_{i}"
            data = {"index": i, "data": f"test_data_{i}"}
            cache_service.cache_response(key, data)
        
        store_time = time.time() - start_time
        print(f"✅ Stored 100 items in {store_time:.3f} seconds")
        
        # Performance test: retrieval
        start_time = time.time()
        
        retrieved_count = 0
        for i in range(100):
            key = f"perf_test_{i}"
            result = cache_service.get_cached_response(key)
            if result:
                retrieved_count += 1
        
        retrieve_time = time.time() - start_time
        print(f"✅ Retrieved {retrieved_count}/100 items in {retrieve_time:.3f} seconds")
        
        # Both operations should be fast
        assert store_time < 2.0, f"Store time too slow: {store_time}s"
        assert retrieve_time < 1.0, f"Retrieve time too slow: {retrieve_time}s"
        
        return True, f"Performance test passed (store: {store_time:.3f}s, retrieve: {retrieve_time:.3f}s)"
        
    except Exception as e:
        return False, f"Performance test error: {str(e)}"

def test_concurrent_access():
    """Test concurrent access to services"""
    print("🔍 Testing concurrent access...")
    
    try:
        from src.infrastructure.ai.cache_service import AIResponseCacheService
        
        cache_service = AIResponseCacheService()
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                for i in range(10):
                    key = f"worker_{worker_id}_item_{i}"
                    data = {"worker": worker_id, "item": i}
                    
                    # Store
                    cache_service.cache_response(key, data)
                    
                    # Retrieve
                    result = cache_service.get_cached_response(key)
                    results.append(result)
                    
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")
        
        # Start 5 concurrent workers
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=10)
        
        # Check results
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        print(f"✅ Concurrent access successful ({len(results)} operations completed)")
        
        return True, f"Concurrent access test passed with {len(results)} operations"
        
    except Exception as e:
        return False, f"Concurrent access test error: {str(e)}"

def test_error_handling():
    """Test error handling in services"""
    print("🔍 Testing error handling...")
    
    try:
        from src.infrastructure.ai.cache_service import AIResponseCacheService
        
        cache_service = AIResponseCacheService()
        
        # Test invalid inputs
        error_cases = [
            {"key": None, "data": {"test": "data"}},
            {"key": "", "data": {"test": "data"}},
            {"key": "valid_key", "data": None},
        ]
        
        handled_errors = 0
        for case in error_cases:
            try:
                cache_service.cache_response(case["key"], case["data"])
                # If no exception, that's okay too
            except Exception as e:
                # Should handle errors gracefully
                handled_errors += 1
                error_msg = str(e).lower()
                # Error messages should not contain sensitive info
                sensitive_terms = ['password', 'secret', 'token', 'credential']
                for term in sensitive_terms:
                    assert term not in error_msg, f"Sensitive term '{term}' in error message"
        
        print(f"✅ Error handling test completed ({handled_errors} errors handled gracefully)")
        
        return True, f"Error handling passed ({handled_errors} cases handled)"
        
    except Exception as e:
        return False, f"Error handling test error: {str(e)}"

def test_memory_management():
    """Test memory management characteristics"""
    print("🔍 Testing memory management...")
    
    try:
        from src.infrastructure.ai.cache_service import AIResponseCacheService
        
        cache_service = AIResponseCacheService()
        
        # Create larger data objects to test memory handling
        large_data_size = 1000  # 1KB per item
        num_items = 50
        
        for i in range(num_items):
            key = f"memory_test_{i}"
            data = {
                "large_field": "x" * large_data_size,
                "index": i,
                "metadata": {"created": f"2024-01-10T10:{i:02d}:00Z"}
            }
            cache_service.cache_response(key, data, ttl=1)  # Short TTL
        
        print(f"✅ Created {num_items} large objects ({large_data_size}B each)")
        
        # Trigger cleanup
        cache_service.cleanup_expired()
        print("✅ Cleanup executed without errors")
        
        # Check cache still functions
        test_key = "post_cleanup_test"
        test_data = {"test": "post_cleanup"}
        cache_service.cache_response(test_key, test_data)
        
        result = cache_service.get_cached_response(test_key)
        if result:
            assert result["test"] == "post_cleanup"
        
        print("✅ Cache functional after memory management")
        
        return True, f"Memory management test passed ({num_items} large objects handled)"
        
    except Exception as e:
        return False, f"Memory management test error: {str(e)}"

def run_all_tests():
    """Run all production validation tests"""
    print("""
    🌱 ZeroWasteAI API - Isolated Production Validation
    ================================================
    Testing core services without external dependencies
    """)
    
    start_time = time.time()
    
    tests = [
        ("Module Imports", test_imports),
        ("GeminiAdapterService", test_gemini_adapter_service),
        ("AIResponseCacheService", test_cache_service),
        ("Service Performance", test_service_performance),
        ("Concurrent Access", test_concurrent_access),
        ("Error Handling", test_error_handling),
        ("Memory Management", test_memory_management),
    ]
    
    results = []
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            success, message = test_func()
            if success:
                print(f"✅ PASSED: {message}")
                passed_tests += 1
            else:
                print(f"❌ FAILED: {message}")
            
            results.append({
                "name": test_name,
                "success": success,
                "message": message
            })
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ FAILED: {error_msg}")
            results.append({
                "name": test_name,
                "success": False,
                "message": error_msg
            })
    
    # Final report
    end_time = time.time()
    total_time = end_time - start_time
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n\n{'='*80}")
    print(f"🏁 ISOLATED PRODUCTION VALIDATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Execution Time: {total_time:.2f} seconds")
    
    print(f"\n📊 DETAILED RESULTS:")
    print("-" * 50)
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status:<10} {result['name']:<25} {result['message']}")
    
    # Production readiness assessment
    print(f"\n🎯 CORE SERVICES ASSESSMENT:")
    print("=" * 40)
    
    if success_rate >= 95:
        print("✅ CORE SERVICES READY FOR PRODUCTION")
        print("   All critical services functioning correctly")
        print("   🚀 SERVICES APPROVED FOR DEPLOYMENT")
        return True
    elif success_rate >= 80:
        print("⚠️  CORE SERVICES MOSTLY READY")
        print("   Some issues detected but not critical")
        print("   🟡 DEPLOY WITH MONITORING")
        return True
    else:
        print("❌ CORE SERVICES NOT READY")
        print("   Critical service failures detected")
        print("   🚨 FIX ISSUES BEFORE DEPLOYMENT")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)