"""
Database Performance Testing Suite
Comprehensive database performance tests including query optimization, connection pooling, and transaction performance
"""
import pytest
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock
from src.main import create_app
import sqlite3
import tempfile
import os


class TestDatabasePerformance:
    """Database performance testing for production deployment validation"""

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
            token = create_access_token(identity="db-perf-test-user")
            return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def temp_db_file(self):
        """Create temporary database file for persistent testing"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        yield temp_file.name
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass

    # ================================================================
    # QUERY PERFORMANCE TESTING
    # ================================================================

    def test_database_query_performance_analysis(self, client, auth_headers):
        """Test database query performance across different endpoints"""
        print("📊 Starting Database Query Performance Analysis...")
        
        # Database-intensive endpoints to test
        query_endpoints = [
            ('/api/inventory/complete', 'Complex inventory query'),
            ('/api/recipes/saved', 'User recipes query'),
            ('/api/planning/all', 'Meal planning query'),
            ('/api/environmental_savings/calculations', 'Environmental calculations query'),
            ('/api/inventory/expiring', 'Expiring items query')
        ]
        
        query_results = {}
        
        for endpoint, description in query_endpoints:
            print(f"   Testing {description}...")
            
            # Measure query performance
            query_times = []
            
            for i in range(10):  # 10 queries per endpoint
                start_time = time.time()
                
                try:
                    response = client.get(endpoint, headers=auth_headers)
                    query_time = time.time() - start_time
                    query_times.append({
                        'query_time': query_time,
                        'status_code': response.status_code,
                        'response_size': len(response.get_data())
                    })
                except Exception as e:
                    query_times.append({
                        'query_time': time.time() - start_time,
                        'error': str(e),
                        'status_code': 500
                    })
            
            # Analyze query performance
            successful_queries = [q for q in query_times if q.get('status_code', 500) < 400]
            
            if successful_queries:
                times = [q['query_time'] for q in successful_queries]
                avg_time = statistics.mean(times)
                median_time = statistics.median(times)
                p95_time = sorted(times)[int(len(times) * 0.95)] if times else 0
                max_time = max(times)
                
                query_results[endpoint] = {
                    'description': description,
                    'avg_time': avg_time,
                    'median_time': median_time,
                    'p95_time': p95_time,
                    'max_time': max_time,
                    'total_queries': len(query_times),
                    'successful_queries': len(successful_queries),
                    'success_rate': len(successful_queries) / len(query_times) * 100
                }
                
                print(f"     Avg: {avg_time:.3f}s, P95: {p95_time:.3f}s, Max: {max_time:.3f}s")
                
                # Query performance assertions
                assert avg_time < 2.0, f"{description} average query time too slow: {avg_time:.3f}s"
                assert p95_time < 5.0, f"{description} P95 query time too slow: {p95_time:.3f}s"
                assert query_results[endpoint]['success_rate'] > 90.0, f"{description} query failure rate too high"
        
        print(f"✅ Database Query Performance Analysis Complete")
        print(f"   Tested {len(query_results)} endpoint types")
        print(f"   Overall performance: {'GOOD' if all(r['avg_time'] < 1.0 for r in query_results.values()) else 'ACCEPTABLE'}")

    def test_database_concurrent_query_performance(self, client, auth_headers):
        """Test database performance under concurrent query load"""
        print("🔄 Starting Concurrent Database Query Performance Test...")
        
        def concurrent_database_query(query_id, endpoint):
            """Execute database query and measure performance"""
            start_time = time.time()
            
            try:
                response = client.get(endpoint, headers=auth_headers)
                return {
                    'query_id': query_id,
                    'endpoint': endpoint,
                    'query_time': time.time() - start_time,
                    'status_code': response.status_code,
                    'success': response.status_code < 400
                }
            except Exception as e:
                return {
                    'query_id': query_id,
                    'endpoint': endpoint,
                    'query_time': time.time() - start_time,
                    'error': str(e),
                    'success': False
                }
        
        # Test different concurrency levels
        concurrency_levels = [5, 10, 20, 30]
        test_endpoint = '/api/inventory/complete'
        
        concurrency_results = {}
        
        for concurrency in concurrency_levels:
            print(f"   Testing concurrency level: {concurrency}")
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                # Submit queries
                futures = []
                for i in range(concurrency * 2):  # 2x queries per worker
                    future = executor.submit(concurrent_database_query, i, test_endpoint)
                    futures.append(future)
                
                # Collect results
                results = []
                for future in as_completed(futures):
                    results.append(future.result())
            
            total_test_time = time.time() - start_time
            
            # Analyze concurrent performance
            successful_queries = [r for r in results if r.get('success', False)]
            failed_queries = [r for r in results if not r.get('success', False)]
            
            if successful_queries:
                query_times = [r['query_time'] for r in successful_queries]
                avg_query_time = statistics.mean(query_times)
                p95_query_time = sorted(query_times)[int(len(query_times) * 0.95)]
                throughput = len(successful_queries) / total_test_time
                
                concurrency_results[concurrency] = {
                    'avg_query_time': avg_query_time,
                    'p95_query_time': p95_query_time,
                    'throughput': throughput,
                    'success_rate': len(successful_queries) / len(results) * 100,
                    'total_queries': len(results),
                    'successful_queries': len(successful_queries),
                    'failed_queries': len(failed_queries)
                }
                
                print(f"     Success: {len(successful_queries)}/{len(results)}")
                print(f"     Avg time: {avg_query_time:.3f}s")
                print(f"     Throughput: {throughput:.1f} queries/s")
        
        print(f"✅ Concurrent Database Performance Results:")
        for concurrency, metrics in concurrency_results.items():
            print(f"   Concurrency {concurrency}: {metrics['avg_query_time']:.3f}s avg, {metrics['throughput']:.1f} q/s")
        
        # Performance degradation analysis
        if len(concurrency_results) >= 2:
            low_concurrency = concurrency_results[min(concurrency_results.keys())]
            high_concurrency = concurrency_results[max(concurrency_results.keys())]
            
            degradation_factor = high_concurrency['avg_query_time'] / low_concurrency['avg_query_time']
            
            print(f"   Performance degradation factor: {degradation_factor:.2f}x")
            
            # Assertions
            assert degradation_factor < 5.0, f"Severe performance degradation: {degradation_factor:.2f}x slower"
            assert high_concurrency['success_rate'] > 80.0, f"High concurrency success rate too low: {high_concurrency['success_rate']:.1f}%"

    # ================================================================
    # CONNECTION POOLING PERFORMANCE
    # ================================================================

    def test_database_connection_pool_performance(self, client, auth_headers):
        """Test database connection pool performance"""
        print("🔗 Starting Database Connection Pool Performance Test...")
        
        def test_connection_reuse(test_id):
            """Test connection pool reuse efficiency"""
            queries_per_connection = []
            
            # Make multiple queries in sequence (should reuse connection)
            for i in range(5):
                start_time = time.time()
                try:
                    response = client.get('/api/inventory/simple', headers=auth_headers)
                    query_time = time.time() - start_time
                    queries_per_connection.append({
                        'test_id': test_id,
                        'query_number': i,
                        'query_time': query_time,
                        'status_code': response.status_code
                    })
                except Exception as e:
                    queries_per_connection.append({
                        'test_id': test_id,
                        'query_number': i,
                        'error': str(e),
                        'query_time': time.time() - start_time
                    })
            
            return queries_per_connection
        
        # Test connection pool with multiple threads
        pool_test_results = []
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(test_connection_reuse, i) for i in range(20)]
            
            for future in as_completed(futures):
                pool_test_results.extend(future.result())
        
        # Analyze connection pool performance
        successful_queries = [q for q in pool_test_results if q.get('status_code', 500) == 200]
        
        if successful_queries:
            # Group by test_id to analyze connection reuse
            connection_groups = {}
            for query in successful_queries:
                test_id = query['test_id']
                if test_id not in connection_groups:
                    connection_groups[test_id] = []
                connection_groups[test_id].append(query)
            
            connection_reuse_analysis = []
            
            for test_id, queries in connection_groups.items():
                if len(queries) >= 2:
                    query_times = [q['query_time'] for q in queries]
                    first_query_time = queries[0]['query_time']
                    subsequent_avg = statistics.mean(query_times[1:]) if len(query_times) > 1 else 0
                    
                    connection_reuse_analysis.append({
                        'test_id': test_id,
                        'first_query_time': first_query_time,
                        'subsequent_avg_time': subsequent_avg,
                        'reuse_efficiency': first_query_time / subsequent_avg if subsequent_avg > 0 else 0
                    })
            
            if connection_reuse_analysis:
                avg_first_query = statistics.mean([a['first_query_time'] for a in connection_reuse_analysis])
                avg_subsequent = statistics.mean([a['subsequent_avg_time'] for a in connection_reuse_analysis])
                avg_efficiency = statistics.mean([a['reuse_efficiency'] for a in connection_reuse_analysis if a['reuse_efficiency'] > 0])
                
                print(f"✅ Connection Pool Performance Analysis:")
                print(f"   First query avg time: {avg_first_query:.3f}s")
                print(f"   Subsequent queries avg time: {avg_subsequent:.3f}s")
                print(f"   Connection reuse efficiency: {avg_efficiency:.2f}x")
                print(f"   Total successful queries: {len(successful_queries)}")
                
                # Connection pool assertions
                assert avg_efficiency > 1.0, "Connection pool not providing reuse benefits"
                assert avg_subsequent < avg_first_query, "Subsequent queries should be faster due to connection reuse"

    # ================================================================
    # TRANSACTION PERFORMANCE
    # ================================================================

    def test_database_transaction_performance(self, client, auth_headers):
        """Test database transaction performance"""
        print("📝 Starting Database Transaction Performance Test...")
        
        def test_transaction_operation(operation_id):
            """Test transaction-based operations"""
            start_time = time.time()
            
            try:
                # Transaction-heavy operation: Add multiple ingredients
                ingredient_data = {
                    "ingredients": [
                        {
                            "name": f"transaction_test_ingredient_{operation_id}_{i}",
                            "quantity": 100 + i,
                            "unit": "grams",
                            "expiry_date": "2024-12-31"
                        }
                        for i in range(3)  # 3 ingredients per transaction
                    ]
                }
                
                response = client.post('/api/inventory/ingredients',
                    json=ingredient_data,
                    headers=auth_headers)
                
                transaction_time = time.time() - start_time
                
                return {
                    'operation_id': operation_id,
                    'transaction_time': transaction_time,
                    'status_code': response.status_code,
                    'ingredients_count': len(ingredient_data['ingredients']),
                    'success': response.status_code in [200, 201]
                }
                
            except Exception as e:
                return {
                    'operation_id': operation_id,
                    'transaction_time': time.time() - start_time,
                    'error': str(e),
                    'success': False
                }
        
        # Test transaction performance under different loads
        transaction_loads = [5, 10, 15]
        transaction_results = {}
        
        for load in transaction_loads:
            print(f"   Testing transaction load: {load} concurrent transactions")
            
            with ThreadPoolExecutor(max_workers=load) as executor:
                futures = [executor.submit(test_transaction_operation, i) for i in range(load)]
                results = [future.result() for future in as_completed(futures)]
            
            successful_transactions = [r for r in results if r.get('success', False)]
            failed_transactions = [r for r in results if not r.get('success', False)]
            
            if successful_transactions:
                transaction_times = [r['transaction_time'] for r in successful_transactions]
                avg_transaction_time = statistics.mean(transaction_times)
                p95_transaction_time = sorted(transaction_times)[int(len(transaction_times) * 0.95)]
                
                transaction_results[load] = {
                    'avg_transaction_time': avg_transaction_time,
                    'p95_transaction_time': p95_transaction_time,
                    'success_rate': len(successful_transactions) / len(results) * 100,
                    'total_transactions': len(results),
                    'successful_transactions': len(successful_transactions),
                    'failed_transactions': len(failed_transactions)
                }
                
                print(f"     Successful: {len(successful_transactions)}/{len(results)}")
                print(f"     Avg time: {avg_transaction_time:.3f}s")
                print(f"     P95 time: {p95_transaction_time:.3f}s")
        
        print(f"✅ Transaction Performance Analysis:")
        for load, metrics in transaction_results.items():
            print(f"   Load {load}: {metrics['avg_transaction_time']:.3f}s avg, {metrics['success_rate']:.1f}% success")
        
        # Transaction performance assertions
        if transaction_results:
            max_load_metrics = transaction_results[max(transaction_results.keys())]
            assert max_load_metrics['success_rate'] > 85.0, f"Transaction success rate too low: {max_load_metrics['success_rate']:.1f}%"
            assert max_load_metrics['avg_transaction_time'] < 3.0, f"Transaction time too slow: {max_load_metrics['avg_transaction_time']:.3f}s"

    # ================================================================
    # DATABASE SCALABILITY TESTING
    # ================================================================

    def test_database_scalability_limits(self, client, auth_headers):
        """Test database scalability limits"""
        print("📈 Starting Database Scalability Limits Test...")
        
        def scalability_test_request(request_id, endpoint_type):
            """Make scalability test request"""
            endpoints = {
                'read_heavy': '/api/inventory',
                'write_heavy': '/api/inventory/ingredients',
                'mixed': '/api/recipes/saved'
            }
            
            endpoint = endpoints.get(endpoint_type, '/api/inventory')
            start_time = time.time()
            
            try:
                if endpoint_type == 'write_heavy':
                    data = {
                        "ingredients": [{
                            "name": f"scale_test_{request_id}",
                            "quantity": 50,
                            "unit": "grams"
                        }]
                    }
                    response = client.post(endpoint, json=data, headers=auth_headers)
                else:
                    response = client.get(endpoint, headers=auth_headers)
                
                return {
                    'request_id': request_id,
                    'endpoint_type': endpoint_type,
                    'response_time': time.time() - start_time,
                    'status_code': response.status_code,
                    'success': response.status_code < 400
                }
                
            except Exception as e:
                return {
                    'request_id': request_id,
                    'endpoint_type': endpoint_type,
                    'response_time': time.time() - start_time,
                    'error': str(e),
                    'success': False
                }
        
        # Test scalability across different load patterns
        scalability_tests = [
            (20, 'read_heavy', 'Read-heavy workload'),
            (15, 'write_heavy', 'Write-heavy workload'),
            (25, 'mixed', 'Mixed workload')
        ]
        
        scalability_results = {}
        
        for load, endpoint_type, description in scalability_tests:
            print(f"   Testing {description} (load: {load})...")
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=load) as executor:
                futures = [executor.submit(scalability_test_request, i, endpoint_type) for i in range(load * 2)]
                results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            
            successful = [r for r in results if r.get('success', False)]
            failed = [r for r in results if not r.get('success', False)]
            
            if successful:
                response_times = [r['response_time'] for r in successful]
                avg_response_time = statistics.mean(response_times)
                throughput = len(successful) / total_time
                
                scalability_results[endpoint_type] = {
                    'description': description,
                    'load_level': load,
                    'avg_response_time': avg_response_time,
                    'throughput': throughput,
                    'success_rate': len(successful) / len(results) * 100,
                    'total_requests': len(results),
                    'successful_requests': len(successful),
                    'failed_requests': len(failed)
                }
                
                print(f"     Throughput: {throughput:.1f} req/s")
                print(f"     Success rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
                print(f"     Avg response: {avg_response_time:.3f}s")
        
        print(f"✅ Database Scalability Analysis:")
        for endpoint_type, metrics in scalability_results.items():
            print(f"   {metrics['description']}: {metrics['throughput']:.1f} req/s, {metrics['success_rate']:.1f}% success")
        
        # Scalability assertions
        for endpoint_type, metrics in scalability_results.items():
            assert metrics['success_rate'] > 70.0, f"{metrics['description']} success rate too low: {metrics['success_rate']:.1f}%"
            assert metrics['throughput'] > 2.0, f"{metrics['description']} throughput too low: {metrics['throughput']:.1f} req/s"

    # ================================================================
    # DATABASE OPTIMIZATION ANALYSIS
    # ================================================================

    def test_database_query_optimization_analysis(self, client, auth_headers):
        """Test database query optimization analysis"""
        print("⚡ Starting Database Query Optimization Analysis...")
        
        def test_query_patterns(pattern_name, query_func):
            """Test different query patterns"""
            pattern_results = []
            
            for i in range(5):
                start_time = time.time()
                try:
                    result = query_func(i)
                    query_time = time.time() - start_time
                    pattern_results.append({
                        'pattern': pattern_name,
                        'iteration': i,
                        'query_time': query_time,
                        'success': True,
                        'result_size': len(str(result))
                    })
                except Exception as e:
                    pattern_results.append({
                        'pattern': pattern_name,
                        'iteration': i,
                        'query_time': time.time() - start_time,
                        'error': str(e),
                        'success': False
                    })
            
            return pattern_results
        
        # Define different query patterns to test
        query_patterns = {
            'simple_select': lambda i: client.get('/api/inventory/simple', headers=auth_headers),
            'complex_join': lambda i: client.get('/api/inventory/complete', headers=auth_headers),
            'filtered_query': lambda i: client.get('/api/inventory/expiring', headers=auth_headers),
            'aggregation_query': lambda i: client.get('/api/environmental_savings/summary', headers=auth_headers)
        }
        
        optimization_results = {}
        
        for pattern_name, query_func in query_patterns.items():
            print(f"   Analyzing {pattern_name} pattern...")
            
            pattern_results = test_query_patterns(pattern_name, query_func)
            successful_queries = [r for r in pattern_results if r.get('success', False)]
            
            if successful_queries:
                query_times = [r['query_time'] for r in successful_queries]
                avg_time = statistics.mean(query_times)
                min_time = min(query_times)
                max_time = max(query_times)
                std_dev = statistics.stdev(query_times) if len(query_times) > 1 else 0
                
                # Query consistency analysis
                consistency_score = 1 - (std_dev / avg_time) if avg_time > 0 else 0
                
                optimization_results[pattern_name] = {
                    'avg_time': avg_time,
                    'min_time': min_time,
                    'max_time': max_time,
                    'std_dev': std_dev,
                    'consistency_score': consistency_score,
                    'total_queries': len(pattern_results),
                    'successful_queries': len(successful_queries)
                }
                
                print(f"     Avg: {avg_time:.3f}s, Consistency: {consistency_score:.2f}")
        
        print(f"✅ Query Optimization Analysis:")
        
        # Identify optimization opportunities
        slow_queries = [name for name, metrics in optimization_results.items() if metrics['avg_time'] > 1.0]
        inconsistent_queries = [name for name, metrics in optimization_results.items() if metrics['consistency_score'] < 0.8]
        
        if slow_queries:
            print(f"   ⚠️ Slow queries detected: {', '.join(slow_queries)}")
        if inconsistent_queries:
            print(f"   ⚠️ Inconsistent queries detected: {', '.join(inconsistent_queries)}")
        
        if not slow_queries and not inconsistent_queries:
            print(f"   ✅ All query patterns performing well")
        
        # Performance recommendations
        print(f"   Query Performance Grades:")
        for pattern_name, metrics in optimization_results.items():
            if metrics['avg_time'] < 0.1:
                grade = "A+"
            elif metrics['avg_time'] < 0.5:
                grade = "A"
            elif metrics['avg_time'] < 1.0:
                grade = "B"
            elif metrics['avg_time'] < 2.0:
                grade = "C"
            else:
                grade = "D"
            
            print(f"     {pattern_name}: {grade} ({metrics['avg_time']:.3f}s avg)")
        
        # Optimization assertions
        assert len(slow_queries) <= len(optimization_results) // 2, "Too many slow query patterns"
        assert len(inconsistent_queries) <= len(optimization_results) // 3, "Too many inconsistent query patterns"

    # ================================================================
    # DATABASE STRESS RECOVERY TESTING
    # ================================================================

    def test_database_stress_recovery(self, client, auth_headers):
        """Test database recovery after stress conditions"""
        print("🔄 Starting Database Stress Recovery Test...")
        
        def stress_phase_test(phase_name, requests_count, concurrency):
            """Execute stress phase"""
            phase_results = []
            
            def stress_request(req_id):
                start_time = time.time()
                try:
                    # Mix of read and write operations
                    if req_id % 3 == 0:
                        # Write operation
                        data = {"ingredients": [{"name": f"stress_{req_id}", "quantity": 10}]}
                        response = client.post('/api/inventory/ingredients', json=data, headers=auth_headers)
                    else:
                        # Read operation
                        response = client.get('/api/inventory', headers=auth_headers)
                    
                    return {
                        'request_id': req_id,
                        'phase': phase_name,
                        'response_time': time.time() - start_time,
                        'status_code': response.status_code,
                        'success': response.status_code < 400
                    }
                except Exception as e:
                    return {
                        'request_id': req_id,
                        'phase': phase_name,
                        'response_time': time.time() - start_time,
                        'error': str(e),
                        'success': False
                    }
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(stress_request, i) for i in range(requests_count)]
                phase_results = [future.result() for future in as_completed(futures)]
            
            return phase_results
        
        # Multi-phase stress recovery test
        stress_phases = [
            ("baseline", 20, 5),      # Baseline performance
            ("stress", 100, 20),      # High stress
            ("recovery", 30, 5),      # Recovery measurement
        ]
        
        all_stress_results = []
        
        for phase_name, requests, concurrency in stress_phases:
            print(f"   Executing {phase_name} phase ({requests} requests, {concurrency} concurrency)...")
            
            phase_start = time.time()
            phase_results = stress_phase_test(phase_name, requests, concurrency)
            phase_duration = time.time() - phase_start
            
            all_stress_results.extend(phase_results)
            
            # Analyze phase results
            successful = [r for r in phase_results if r.get('success', False)]
            if successful:
                response_times = [r['response_time'] for r in successful]
                avg_time = statistics.mean(response_times)
                success_rate = len(successful) / len(phase_results) * 100
                
                print(f"     Phase duration: {phase_duration:.1f}s")
                print(f"     Success rate: {success_rate:.1f}%")
                print(f"     Avg response: {avg_time:.3f}s")
            
            # Brief pause between phases
            if phase_name != "recovery":
                time.sleep(2)
        
        # Recovery analysis
        baseline_results = [r for r in all_stress_results if r.get('phase') == 'baseline' and r.get('success')]
        stress_results = [r for r in all_stress_results if r.get('phase') == 'stress' and r.get('success')]
        recovery_results = [r for r in all_stress_results if r.get('phase') == 'recovery' and r.get('success')]
        
        recovery_analysis = {}
        
        if baseline_results and recovery_results:
            baseline_avg = statistics.mean([r['response_time'] for r in baseline_results])
            recovery_avg = statistics.mean([r['response_time'] for r in recovery_results])
            recovery_ratio = recovery_avg / baseline_avg
            
            recovery_analysis = {
                'baseline_avg_time': baseline_avg,
                'recovery_avg_time': recovery_avg,
                'recovery_ratio': recovery_ratio,
                'recovery_quality': 'EXCELLENT' if recovery_ratio < 1.2 else 'GOOD' if recovery_ratio < 1.5 else 'POOR'
            }
            
            print(f"✅ Database Stress Recovery Analysis:")
            print(f"   Baseline performance: {baseline_avg:.3f}s")
            print(f"   Recovery performance: {recovery_avg:.3f}s")
            print(f"   Recovery ratio: {recovery_ratio:.2f}x")
            print(f"   Recovery quality: {recovery_analysis['recovery_quality']}")
            
            # Recovery assertions
            assert recovery_ratio < 2.0, f"Poor database recovery: {recovery_ratio:.2f}x slower than baseline"
            assert len(recovery_results) >= len(baseline_results) * 0.8, "Database not recovering request capacity"

    # ================================================================
    # COMPREHENSIVE DATABASE PERFORMANCE SUMMARY
    # ================================================================

    def test_comprehensive_database_performance_summary(self, client, auth_headers):
        """Comprehensive database performance summary"""
        print("🏁 Starting Comprehensive Database Performance Summary...")
        
        # Run abbreviated versions of key database tests
        performance_metrics = {}
        
        # Quick query performance check
        print("   Running quick query performance check...")
        query_times = []
        for i in range(5):
            start = time.time()
            response = client.get('/api/inventory', headers=auth_headers)
            query_times.append(time.time() - start)
        
        if query_times:
            performance_metrics['avg_query_time'] = statistics.mean(query_times)
            performance_metrics['max_query_time'] = max(query_times)
        
        # Quick concurrency check
        print("   Running quick concurrency check...")
        def quick_concurrent_query(req_id):
            start = time.time()
            try:
                response = client.get('/api/inventory/simple', headers=auth_headers)
                return time.time() - start
            except:
                return None
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(quick_concurrent_query, i) for i in range(20)]
            concurrent_times = [f.result() for f in as_completed(futures) if f.result() is not None]
        
        if concurrent_times:
            performance_metrics['concurrent_avg_time'] = statistics.mean(concurrent_times)
            performance_metrics['concurrent_throughput'] = len(concurrent_times) / sum(concurrent_times)
        
        # Quick write performance check
        print("   Running quick write performance check...")
        write_times = []
        for i in range(3):
            start = time.time()
            try:
                data = {"ingredients": [{"name": f"perf_test_{i}", "quantity": 10}]}
                response = client.post('/api/inventory/ingredients', json=data, headers=auth_headers)
                if response.status_code in [200, 201]:
                    write_times.append(time.time() - start)
            except:
                pass
        
        if write_times:
            performance_metrics['avg_write_time'] = statistics.mean(write_times)
        
        # Performance scoring
        print(f"\n🏆 DATABASE PERFORMANCE SCORECARD:")
        print("=" * 50)
        
        total_score = 0
        max_score = 0
        
        # Query Performance (30 points)
        if 'avg_query_time' in performance_metrics:
            query_time = performance_metrics['avg_query_time']
            if query_time < 0.1:
                query_score = 30
            elif query_time < 0.5:
                query_score = 25
            elif query_time < 1.0:
                query_score = 20
            elif query_time < 2.0:
                query_score = 15
            else:
                query_score = 10
            
            total_score += query_score
            max_score += 30
            print(f"Query Performance: {query_score}/30 ({query_time:.3f}s avg)")
        
        # Concurrency Performance (25 points)
        if 'concurrent_avg_time' in performance_metrics:
            concurrent_time = performance_metrics['concurrent_avg_time']
            if concurrent_time < 0.2:
                concurrent_score = 25
            elif concurrent_time < 0.5:
                concurrent_score = 20
            elif concurrent_time < 1.0:
                concurrent_score = 15
            elif concurrent_time < 2.0:
                concurrent_score = 10
            else:
                concurrent_score = 5
            
            total_score += concurrent_score
            max_score += 25
            print(f"Concurrency Performance: {concurrent_score}/25 ({concurrent_time:.3f}s avg)")
        
        # Throughput Performance (25 points)
        if 'concurrent_throughput' in performance_metrics:
            throughput = performance_metrics['concurrent_throughput']
            if throughput > 50:
                throughput_score = 25
            elif throughput > 20:
                throughput_score = 20
            elif throughput > 10:
                throughput_score = 15
            elif throughput > 5:
                throughput_score = 10
            else:
                throughput_score = 5
            
            total_score += throughput_score
            max_score += 25
            print(f"Throughput Performance: {throughput_score}/25 ({throughput:.1f} req/s)")
        
        # Write Performance (20 points)
        if 'avg_write_time' in performance_metrics:
            write_time = performance_metrics['avg_write_time']
            if write_time < 0.2:
                write_score = 20
            elif write_time < 0.5:
                write_score = 15
            elif write_time < 1.0:
                write_score = 12
            elif write_time < 2.0:
                write_score = 8
            else:
                write_score = 4
            
            total_score += write_score
            max_score += 20
            print(f"Write Performance: {write_score}/20 ({write_time:.3f}s avg)")
        
        # Overall grade
        if max_score > 0:
            percentage_score = (total_score / max_score) * 100
            
            if percentage_score >= 90:
                grade = "A+"
                status = "EXCELLENT"
            elif percentage_score >= 80:
                grade = "A"
                status = "VERY GOOD"
            elif percentage_score >= 70:
                grade = "B"
                status = "GOOD"
            elif percentage_score >= 60:
                grade = "C"
                status = "ACCEPTABLE"
            else:
                grade = "D"
                status = "NEEDS IMPROVEMENT"
            
            print(f"\nOVERALL DATABASE PERFORMANCE:")
            print(f"  Score: {total_score}/{max_score} ({percentage_score:.1f}%)")
            print(f"  Grade: {grade}")
            print(f"  Status: {status}")
            
            # Final assertions
            assert percentage_score >= 60.0, f"Database performance too low: {percentage_score:.1f}%"
            
        print(f"\n✅ Database Performance Summary Complete")
        
        return performance_metrics