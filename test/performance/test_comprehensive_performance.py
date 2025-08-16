"""
Comprehensive Performance Testing Suite - 100% Coverage
Stress testing, memory profiling, and load testing for production readiness
"""
import pytest
import time
import threading
import psutil
import os
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock
from src.main import create_app
import json


class TestComprehensivePerformance:
    """100% Performance testing coverage including stress, memory, and load tests"""

    @pytest.fixture(scope="class")
    def app(self):
        app = create_app()
        app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "JWT_ACCESS_TOKEN_EXPIRES": False,
        })
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def auth_headers(self, app):
        with app.app_context():
            from flask_jwt_extended import create_access_token
            token = create_access_token(identity="stress-test-user")
            return {"Authorization": f"Bearer {token}"}

    # ================================================================
    # STRESS TESTING - High Concurrency Load
    # ================================================================

    def test_stress_authentication_1000_concurrent_users(self, client):
        """Test authentication with 1000+ concurrent requests"""
        print("🔥 Starting 1000 concurrent authentication stress test...")
        
        with patch('firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.return_value = {
                'uid': lambda i=0: f'stress-user-{i % 100}',
                'email': lambda i=0: f'stress-user-{i % 100}@example.com'
            }
            
            results = []
            errors = []
            start_time = time.time()
            
            def auth_request(user_id):
                try:
                    mock_verify.return_value = {
                        'uid': f'stress-user-{user_id}',
                        'email': f'stress-user-{user_id}@example.com'
                    }
                    
                    response = client.post('/api/auth/firebase-signin',
                        json={'firebase_id_token': f'stress-token-{user_id}'})
                    
                    return {
                        'user_id': user_id,
                        'status_code': response.status_code,
                        'response_time': time.time()
                    }
                except Exception as e:
                    errors.append(f"User {user_id}: {str(e)}")
                    return None
            
            # Execute 1000 concurrent requests
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(auth_request, i) for i in range(1000)]
                
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        results.append(result)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Analyze results
            successful_requests = len([r for r in results if r['status_code'] in [200, 201]])
            failed_requests = len([r for r in results if r['status_code'] >= 400])
            
            print(f"✅ Stress Test Results:")
            print(f"   Total requests: 1000")
            print(f"   Successful: {successful_requests}")
            print(f"   Failed: {failed_requests}")
            print(f"   Errors: {len(errors)}")
            print(f"   Total time: {total_time:.2f}s")
            print(f"   Requests/second: {1000/total_time:.2f}")
            
            # Performance assertions
            assert total_time < 30.0, f"Stress test took too long: {total_time}s"
            assert len(errors) < 50, f"Too many errors: {len(errors)}"
            assert successful_requests > 800, f"Too many failed requests: {failed_requests}"

    def test_stress_inventory_operations_heavy_load(self, client, auth_headers):
        """Test inventory operations under heavy concurrent load"""
        print("🔥 Starting heavy inventory operations stress test...")
        
        with patch('src.application.use_cases.inventory.get_inventory_content_use_case.GetInventoryContentUseCase.execute') as mock_inventory:
            # Mock heavy inventory response
            mock_inventory.return_value = {
                "ingredients": [
                    {"name": f"ingredient_{i}", "quantity": i, "details": "x" * 100}
                    for i in range(500)  # 500 ingredients
                ],
                "foods": [
                    {"name": f"food_{i}", "quantity": i, "details": "x" * 100}
                    for i in range(500)  # 500 foods
                ]
            }
            
            results = []
            start_time = time.time()
            
            def inventory_request(request_id):
                try:
                    response_start = time.time()
                    response = client.get('/api/inventory/complete', headers=auth_headers)
                    response_time = time.time() - response_start
                    
                    return {
                        'request_id': request_id,
                        'status_code': response.status_code,
                        'response_time': response_time,
                        'response_size': len(response.get_data())
                    }
                except Exception as e:
                    return {'request_id': request_id, 'error': str(e)}
            
            # 100 concurrent heavy requests
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(inventory_request, i) for i in range(100)]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Analyze performance
            successful = [r for r in results if r.get('status_code') == 200]
            avg_response_time = sum(r['response_time'] for r in successful) / len(successful) if successful else 0
            max_response_time = max(r['response_time'] for r in successful) if successful else 0
            
            print(f"✅ Heavy Load Test Results:")
            print(f"   Successful requests: {len(successful)}/100")
            print(f"   Average response time: {avg_response_time:.3f}s")
            print(f"   Max response time: {max_response_time:.3f}s")
            print(f"   Total time: {total_time:.2f}s")
            
            assert len(successful) >= 95, "Too many failed requests under load"
            assert avg_response_time < 2.0, f"Average response time too slow: {avg_response_time}s"
            assert max_response_time < 5.0, f"Max response time too slow: {max_response_time}s"

    # ================================================================
    # MEMORY PROFILING AND LEAK DETECTION
    # ================================================================

    def test_memory_usage_under_sustained_load(self, client, auth_headers):
        """Test memory usage during sustained operations"""
        print("🧠 Starting memory usage profiling test...")
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_samples = [initial_memory]
        
        with patch('src.application.use_cases.inventory.get_inventory_content_use_case.GetInventoryContentUseCase.execute') as mock_execute:
            # Simulate large data responses
            mock_execute.return_value = {
                "large_data": ["x" * 1000 for _ in range(100)],  # 100KB per request
                "metadata": {"request_id": "memory_test"}
            }
            
            # Make 200 requests and monitor memory
            for i in range(200):
                response = client.get('/api/inventory', headers=auth_headers)
                
                # Sample memory every 10 requests
                if i % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_samples.append(current_memory)
                    
                    # Force garbage collection to test for leaks
                    if i % 50 == 0:
                        gc.collect()
                        after_gc_memory = process.memory_info().rss / 1024 / 1024
                        memory_samples.append(after_gc_memory)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        max_memory = max(memory_samples)
        
        print(f"✅ Memory Profiling Results:")
        print(f"   Initial memory: {initial_memory:.2f} MB")
        print(f"   Final memory: {final_memory:.2f} MB")
        print(f"   Memory growth: {memory_growth:.2f} MB")
        print(f"   Peak memory: {max_memory:.2f} MB")
        print(f"   Memory samples: {len(memory_samples)}")
        
        # Memory assertions
        assert memory_growth < 50.0, f"Memory leak detected: {memory_growth:.2f} MB growth"
        assert max_memory < initial_memory + 100.0, f"Excessive memory usage: {max_memory:.2f} MB"

    def test_memory_cleanup_after_large_operations(self, client, auth_headers):
        """Test memory cleanup after processing large datasets"""
        print("🧹 Starting memory cleanup validation test...")
        
        process = psutil.Process(os.getpid())
        
        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024
        
        with patch('src.application.use_cases.recipes.generate_recipes_use_case.GenerateRecipesUseCase.execute') as mock_generate:
            # Simulate very large recipe generation
            mock_generate.return_value = {
                "recipes": [
                    {
                        "title": f"Recipe {i}",
                        "ingredients": [f"ingredient_{j}" for j in range(20)],
                        "instructions": [f"Step {k}: " + "x" * 200 for k in range(15)],
                        "large_description": "x" * 2000  # 2KB per recipe
                    }
                    for i in range(100)  # 100 recipes * 2KB = ~200KB per response
                ]
            }
            
            # Process 50 large requests
            for i in range(50):
                response = client.post('/api/recipes/generate-from-inventory',
                    json={"max_recipes": 100},
                    headers=auth_headers)
        
        # Force cleanup and measure
        gc.collect()
        after_cleanup_memory = process.memory_info().rss / 1024 / 1024
        memory_retained = after_cleanup_memory - baseline_memory
        
        print(f"✅ Memory Cleanup Results:")
        print(f"   Baseline memory: {baseline_memory:.2f} MB")
        print(f"   After cleanup: {after_cleanup_memory:.2f} MB")
        print(f"   Memory retained: {memory_retained:.2f} MB")
        
        assert memory_retained < 30.0, f"Poor memory cleanup: {memory_retained:.2f} MB retained"

    # ================================================================
    # DATABASE PERFORMANCE TESTING
    # ================================================================

    def test_database_query_performance_under_load(self, client, auth_headers):
        """Test database performance with concurrent queries"""
        print("🗄️ Starting database performance test...")
        
        query_times = []
        errors = []
        
        def database_intensive_operation(operation_id):
            try:
                start_time = time.time()
                
                # Simulate database-heavy operations
                endpoints = [
                    '/api/inventory/complete',
                    '/api/recipes/saved',
                    '/api/planning/all',
                    '/api/environmental_savings/calculations'
                ]
                
                endpoint = endpoints[operation_id % len(endpoints)]
                response = client.get(endpoint, headers=auth_headers)
                
                query_time = time.time() - start_time
                
                return {
                    'operation_id': operation_id,
                    'endpoint': endpoint,
                    'query_time': query_time,
                    'status_code': response.status_code
                }
                
            except Exception as e:
                errors.append(f"Operation {operation_id}: {str(e)}")
                return None
        
        # 200 concurrent database operations
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(database_intensive_operation, i) for i in range(200)]
            results = [future.result() for future in as_completed(futures) if future.result()]
        
        # Analyze database performance
        query_times = [r['query_time'] for r in results]
        avg_query_time = sum(query_times) / len(query_times) if query_times else 0
        max_query_time = max(query_times) if query_times else 0
        p95_query_time = sorted(query_times)[int(len(query_times) * 0.95)] if query_times else 0
        
        print(f"✅ Database Performance Results:")
        print(f"   Total queries: {len(results)}")
        print(f"   Errors: {len(errors)}")
        print(f"   Average query time: {avg_query_time:.3f}s")
        print(f"   Max query time: {max_query_time:.3f}s")
        print(f"   95th percentile: {p95_query_time:.3f}s")
        
        assert len(errors) < 10, f"Too many database errors: {len(errors)}"
        assert avg_query_time < 1.0, f"Database queries too slow: {avg_query_time:.3f}s"
        assert p95_query_time < 2.0, f"95th percentile too slow: {p95_query_time:.3f}s"

    # ================================================================
    # CACHE PERFORMANCE OPTIMIZATION
    # ================================================================

    def test_cache_performance_under_high_throughput(self, client, auth_headers):
        """Test cache performance with high request throughput"""
        print("⚡ Starting cache performance optimization test...")
        
        cache_hits = 0
        cache_misses = 0
        response_times = []
        
        # Pre-warm cache with some requests
        for i in range(5):
            client.get('/api/inventory', headers=auth_headers)
        
        def cache_test_request(request_id):
            start_time = time.time()
            response = client.get('/api/inventory', headers=auth_headers)
            response_time = time.time() - start_time
            
            # Check if response was cached (faster response = likely cached)
            is_cached = response_time < 0.1  # Cached responses should be < 100ms
            
            return {
                'request_id': request_id,
                'response_time': response_time,
                'is_cached': is_cached,
                'status_code': response.status_code
            }
        
        # 500 requests to test cache efficiency
        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(cache_test_request, i) for i in range(500)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze cache performance
        response_times = [r['response_time'] for r in results]
        cache_hits = len([r for r in results if r['is_cached']])
        cache_misses = len(results) - cache_hits
        cache_hit_rate = cache_hits / len(results) * 100
        
        avg_response_time = sum(response_times) / len(response_times)
        cached_avg = sum(r['response_time'] for r in results if r['is_cached']) / cache_hits if cache_hits > 0 else 0
        
        print(f"✅ Cache Performance Results:")
        print(f"   Total requests: {len(results)}")
        print(f"   Cache hits: {cache_hits}")
        print(f"   Cache misses: {cache_misses}")
        print(f"   Cache hit rate: {cache_hit_rate:.1f}%")
        print(f"   Average response time: {avg_response_time:.3f}s")
        print(f"   Cached response time: {cached_avg:.3f}s")
        
        assert cache_hit_rate > 70.0, f"Cache hit rate too low: {cache_hit_rate:.1f}%"
        assert cached_avg < 0.1, f"Cached responses too slow: {cached_avg:.3f}s"

    # ================================================================
    # BATCH PROCESSING PERFORMANCE
    # ================================================================

    def test_batch_processing_scalability(self, client, auth_headers):
        """Test batch processing with increasingly large datasets"""
        print("📦 Starting batch processing scalability test...")
        
        batch_sizes = [10, 50, 100, 250, 500]
        results = {}
        
        for batch_size in batch_sizes:
            print(f"   Testing batch size: {batch_size}")
            
            with patch('src.application.use_cases.recognition.recognize_batch_use_case.RecognizeBatchUseCase.execute') as mock_batch:
                mock_batch.return_value = {
                    "results": [{"image_name": f"img_{i}.jpg", "ingredients": []} for i in range(batch_size)],
                    "total_images": batch_size,
                    "processing_time": f"{batch_size * 0.1:.1f}s"
                }
                
                # Create mock batch data
                batch_data = {
                    'images': [(f'image_{i}.jpg', b'fake_image_data') for i in range(batch_size)]
                }
                
                start_time = time.time()
                response = client.post('/api/recognition/batch',
                    data=batch_data,
                    headers=auth_headers,
                    content_type='multipart/form-data')
                processing_time = time.time() - start_time
                
                results[batch_size] = {
                    'processing_time': processing_time,
                    'status_code': response.status_code,
                    'throughput': batch_size / processing_time if processing_time > 0 else 0
                }
        
        print(f"✅ Batch Processing Results:")
        for size, result in results.items():
            print(f"   Batch {size}: {result['processing_time']:.3f}s, {result['throughput']:.1f} items/s")
        
        # Verify scalability - larger batches should have better throughput
        small_batch_throughput = results[10]['throughput']
        large_batch_throughput = results[500]['throughput']
        
        assert all(r['status_code'] == 200 for r in results.values()), "Batch processing failures"
        assert large_batch_throughput > small_batch_throughput * 2, "Poor batch processing scalability"

    # ================================================================
    # DEGRADATION TESTING
    # ================================================================

    def test_graceful_degradation_under_extreme_load(self, client, auth_headers):
        """Test system behavior under extreme load conditions"""
        print("🔥 Starting graceful degradation test...")
        
        # Gradually increase load and monitor response
        load_levels = [50, 100, 200, 400, 800]
        degradation_results = {}
        
        for load_level in load_levels:
            print(f"   Testing load level: {load_level} concurrent requests")
            
            results = []
            start_time = time.time()
            
            def load_request(req_id):
                try:
                    response = client.get('/api/inventory', headers=auth_headers)
                    return {
                        'status_code': response.status_code,
                        'response_time': time.time()
                    }
                except Exception as e:
                    return {'error': str(e)}
            
            # Execute concurrent requests
            with ThreadPoolExecutor(max_workers=min(load_level, 100)) as executor:
                futures = [executor.submit(load_request, i) for i in range(load_level)]
                results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            successful = len([r for r in results if r.get('status_code') == 200])
            errors = len([r for r in results if 'error' in r])
            success_rate = successful / load_level * 100
            
            degradation_results[load_level] = {
                'success_rate': success_rate,
                'total_time': total_time,
                'errors': errors,
                'throughput': load_level / total_time
            }
        
        print(f"✅ Degradation Test Results:")
        for load, result in degradation_results.items():
            print(f"   Load {load}: {result['success_rate']:.1f}% success, {result['throughput']:.1f} req/s")
        
        # Verify graceful degradation
        low_load_success = degradation_results[50]['success_rate']
        high_load_success = degradation_results[800]['success_rate']
        
        assert low_load_success > 95.0, "Poor performance at low load"
        assert high_load_success > 70.0, "System fails under high load (not graceful)"
        
    def test_system_recovery_after_load_spike(self, client, auth_headers):
        """Test system recovery after extreme load spike"""
        print("🔄 Starting system recovery test...")
        
        # Phase 1: Normal load
        normal_results = []
        for _ in range(20):
            start_time = time.time()
            response = client.get('/api/inventory', headers=auth_headers)
            response_time = time.time() - start_time
            normal_results.append(response_time)
        
        baseline_avg = sum(normal_results) / len(normal_results)
        
        # Phase 2: Load spike
        print("   Applying load spike...")
        spike_results = []
        
        def spike_request(req_id):
            try:
                start_time = time.time()
                response = client.get('/api/inventory', headers=auth_headers)
                return time.time() - start_time
            except:
                return None
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(spike_request, i) for i in range(500)]
            spike_results = [f.result() for f in as_completed(futures) if f.result()]
        
        # Phase 3: Recovery measurement
        time.sleep(2)  # Allow system to recover
        
        recovery_results = []
        for _ in range(20):
            start_time = time.time()
            response = client.get('/api/inventory', headers=auth_headers)
            response_time = time.time() - start_time
            recovery_results.append(response_time)
        
        recovery_avg = sum(recovery_results) / len(recovery_results)
        recovery_ratio = recovery_avg / baseline_avg
        
        print(f"✅ Recovery Test Results:")
        print(f"   Baseline average: {baseline_avg:.3f}s")
        print(f"   Recovery average: {recovery_avg:.3f}s")
        print(f"   Recovery ratio: {recovery_ratio:.2f}x")
        print(f"   Spike requests processed: {len(spike_results)}")
        
        assert recovery_ratio < 2.0, f"Poor recovery: {recovery_ratio:.2f}x slower than baseline"
        assert len(spike_results) > 400, "System failed during load spike"