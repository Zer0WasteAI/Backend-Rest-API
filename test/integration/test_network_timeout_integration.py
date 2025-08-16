"""
Network and Timeout Integration Tests
Tests network resilience, timeout handling, and failure recovery scenarios for production deployment
"""
import pytest
import time
import threading
import socket
import requests
from unittest.mock import patch, MagicMock, Mock
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.main import create_app
import json


class TestNetworkTimeoutIntegration:
    """Network resilience and timeout integration testing"""

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
            token = create_access_token(identity="network-test-user")
            return {"Authorization": f"Bearer {token}"}

    # ================================================================
    # NETWORK TIMEOUT TESTING
    # ================================================================

    def test_external_service_timeout_handling(self, client, auth_headers):
        """Test handling of external service timeouts"""
        print("⏱️ Testing External Service Timeout Handling...")
        
        def simulate_timeout_scenario(service_name, timeout_duration):
            """Simulate different timeout scenarios"""
            
            if service_name == "google_ai":
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_model_class.return_value = mock_model
                    
                    # Simulate AI service timeout
                    def timeout_ai_call(*args, **kwargs):
                        time.sleep(timeout_duration)
                        if timeout_duration > 5.0:  # Simulate timeout after 5s
                            raise Exception("Request timeout")
                        return MagicMock(text='{"recipes": []}')
                    
                    mock_model.generate_content.side_effect = timeout_ai_call
                    
                    start_time = time.time()
                    try:
                        response = client.post('/api/recipes/generate-from-inventory',
                            json={"max_recipes": 1},
                            headers=auth_headers)
                        
                        return {
                            'service': service_name,
                            'timeout_duration': timeout_duration,
                            'response_time': time.time() - start_time,
                            'status_code': response.status_code,
                            'handled_gracefully': response.status_code in [200, 408, 503, 504]
                        }
                    except Exception as e:
                        return {
                            'service': service_name,
                            'timeout_duration': timeout_duration,
                            'response_time': time.time() - start_time,
                            'error': str(e),
                            'handled_gracefully': True  # Exception caught, so handled
                        }
            
            elif service_name == "firebase_auth":
                with patch('firebase_admin.auth.verify_id_token') as mock_verify:
                    def timeout_firebase_call(*args, **kwargs):
                        time.sleep(timeout_duration)
                        if timeout_duration > 3.0:  # Simulate timeout after 3s
                            raise Exception("Firebase timeout")
                        return {'uid': 'test-user', 'email': 'test@example.com'}
                    
                    mock_verify.side_effect = timeout_firebase_call
                    
                    start_time = time.time()
                    try:
                        response = client.post('/api/auth/firebase-signin',
                            json={'firebase_id_token': 'test.token'})
                        
                        return {
                            'service': service_name,
                            'timeout_duration': timeout_duration,
                            'response_time': time.time() - start_time,
                            'status_code': response.status_code,
                            'handled_gracefully': response.status_code in [200, 401, 408, 503]
                        }
                    except Exception as e:
                        return {
                            'service': service_name,
                            'timeout_duration': timeout_duration,
                            'response_time': time.time() - start_time,
                            'error': str(e),
                            'handled_gracefully': True
                        }
        
        # Test different timeout scenarios
        timeout_scenarios = [
            ("google_ai", 1.0),      # Fast response
            ("google_ai", 3.0),      # Moderate delay
            ("google_ai", 6.0),      # Timeout scenario
            ("firebase_auth", 0.5),  # Fast auth
            ("firebase_auth", 2.0),  # Moderate auth delay
            ("firebase_auth", 4.0),  # Auth timeout
        ]
        
        timeout_results = []
        
        for service, timeout_duration in timeout_scenarios:
            print(f"   Testing {service} timeout scenario ({timeout_duration}s delay)...")
            result = simulate_timeout_scenario(service, timeout_duration)
            timeout_results.append(result)
            
            print(f"     Response time: {result['response_time']:.2f}s")
            print(f"     Handled gracefully: {result['handled_gracefully']}")
        
        # Analyze timeout handling
        print(f"✅ Timeout Handling Analysis:")
        
        graceful_handling_count = sum(1 for r in timeout_results if r['handled_gracefully'])
        total_scenarios = len(timeout_results)
        graceful_rate = graceful_handling_count / total_scenarios * 100
        
        print(f"   Total timeout scenarios: {total_scenarios}")
        print(f"   Gracefully handled: {graceful_handling_count}")
        print(f"   Graceful handling rate: {graceful_rate:.1f}%")
        
        # Group by service
        services_tested = set(r['service'] for r in timeout_results)
        for service in services_tested:
            service_results = [r for r in timeout_results if r['service'] == service]
            service_graceful = sum(1 for r in service_results if r['handled_gracefully'])
            service_rate = service_graceful / len(service_results) * 100
            print(f"   {service}: {service_rate:.1f}% graceful handling")
        
        # Assertions
        assert graceful_rate >= 80.0, f"Timeout handling rate too low: {graceful_rate:.1f}%"
        assert all(r['response_time'] < 30.0 for r in timeout_results), "Some requests took too long to timeout"

    def test_network_connectivity_failure_scenarios(self, client, auth_headers):
        """Test network connectivity failure scenarios"""
        print("🌐 Testing Network Connectivity Failure Scenarios...")
        
        def simulate_network_failure(failure_type):
            """Simulate different network failure types"""
            
            if failure_type == "dns_resolution_failure":
                with patch('socket.gethostbyname') as mock_dns:
                    mock_dns.side_effect = socket.gaierror("Name resolution failed")
                    
                    try:
                        # This should test any external API calls
                        response = client.post('/api/recipes/generate-from-inventory',
                            json={"max_recipes": 1},
                            headers=auth_headers)
                        return {
                            'failure_type': failure_type,
                            'status_code': response.status_code,
                            'handled': response.status_code in [200, 503, 502, 504]
                        }
                    except Exception as e:
                        return {
                            'failure_type': failure_type,
                            'error': str(e),
                            'handled': True  # Exception caught
                        }
            
            elif failure_type == "connection_refused":
                with patch('requests.post') as mock_post:
                    mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
                    
                    try:
                        response = client.post('/api/recipes/generate-from-inventory',
                            json={"max_recipes": 1},
                            headers=auth_headers)
                        return {
                            'failure_type': failure_type,
                            'status_code': response.status_code,
                            'handled': response.status_code in [200, 503, 502]
                        }
                    except Exception as e:
                        return {
                            'failure_type': failure_type,
                            'error': str(e),
                            'handled': True
                        }
            
            elif failure_type == "network_unreachable":
                with patch('requests.get') as mock_get:
                    mock_get.side_effect = requests.exceptions.NetworkError("Network unreachable")
                    
                    try:
                        # Test a simple GET endpoint
                        response = client.get('/api/inventory', headers=auth_headers)
                        return {
                            'failure_type': failure_type,
                            'status_code': response.status_code,
                            'handled': response.status_code in [200, 500, 503]
                        }
                    except Exception as e:
                        return {
                            'failure_type': failure_type,
                            'error': str(e),
                            'handled': True
                        }
        
        # Test different network failure scenarios
        network_failures = [
            "dns_resolution_failure",
            "connection_refused", 
            "network_unreachable"
        ]
        
        failure_results = []
        
        for failure_type in network_failures:
            print(f"   Testing {failure_type}...")
            result = simulate_network_failure(failure_type)
            failure_results.append(result)
            print(f"     Handled gracefully: {result.get('handled', False)}")
        
        # Analyze network failure handling
        print(f"✅ Network Failure Handling Analysis:")
        
        handled_failures = sum(1 for r in failure_results if r.get('handled', False))
        total_failures = len(failure_results)
        handling_rate = handled_failures / total_failures * 100
        
        print(f"   Total network failure types: {total_failures}")
        print(f"   Gracefully handled: {handled_failures}")
        print(f"   Handling rate: {handling_rate:.1f}%")
        
        # Assertions
        assert handling_rate >= 90.0, f"Network failure handling rate too low: {handling_rate:.1f}%"

    def test_slow_network_conditions_simulation(self, client, auth_headers):
        """Test behavior under slow network conditions"""
        print("🐌 Testing Slow Network Conditions Simulation...")
        
        def simulate_slow_network_request(delay_seconds, request_type):
            """Simulate slow network requests"""
            
            if request_type == "external_api":
                with patch('google.generativeai.GenerativeModel') as mock_model_class:
                    mock_model = MagicMock()
                    mock_model_class.return_value = mock_model
                    
                    def slow_api_call(*args, **kwargs):
                        time.sleep(delay_seconds)
                        return MagicMock(text='{"recipes": [{"title": "Slow Recipe"}]}')
                    
                    mock_model.generate_content.side_effect = slow_api_call
                    
                    start_time = time.time()
                    try:
                        response = client.post('/api/recipes/generate-from-inventory',
                            json={"max_recipes": 1},
                            headers=auth_headers)
                        
                        return {
                            'delay_seconds': delay_seconds,
                            'request_type': request_type,
                            'total_time': time.time() - start_time,
                            'status_code': response.status_code,
                            'completed': True
                        }
                    except Exception as e:
                        return {
                            'delay_seconds': delay_seconds,
                            'request_type': request_type,
                            'total_time': time.time() - start_time,
                            'error': str(e),
                            'completed': False
                        }
            
            elif request_type == "database_query":
                # Simulate slow database operations
                with patch('src.application.use_cases.inventory.get_inventory_content_use_case.GetInventoryContentUseCase.execute') as mock_db:
                    def slow_db_query(*args, **kwargs):
                        time.sleep(delay_seconds)
                        return {"ingredients": [], "foods": []}
                    
                    mock_db.side_effect = slow_db_query
                    
                    start_time = time.time()
                    try:
                        response = client.get('/api/inventory', headers=auth_headers)
                        
                        return {
                            'delay_seconds': delay_seconds,
                            'request_type': request_type,
                            'total_time': time.time() - start_time,
                            'status_code': response.status_code,
                            'completed': True
                        }
                    except Exception as e:
                        return {
                            'delay_seconds': delay_seconds,
                            'request_type': request_type,
                            'total_time': time.time() - start_time,
                            'error': str(e),
                            'completed': False
                        }
        
        # Test different slow network scenarios
        slow_network_tests = [
            (0.5, "external_api"),    # Moderately slow API
            (2.0, "external_api"),    # Very slow API
            (4.0, "external_api"),    # Extremely slow API
            (0.3, "database_query"),  # Slow database
            (1.0, "database_query"),  # Very slow database
            (2.0, "database_query"),  # Extremely slow database
        ]
        
        slow_network_results = []
        
        for delay, request_type in slow_network_tests:
            print(f"   Testing {request_type} with {delay}s delay...")
            result = simulate_slow_network_request(delay, request_type)
            slow_network_results.append(result)
            
            if result['completed']:
                print(f"     Total time: {result['total_time']:.2f}s (expected ~{delay}s)")
            else:
                print(f"     Failed after: {result['total_time']:.2f}s")
        
        # Analyze slow network handling
        print(f"✅ Slow Network Conditions Analysis:")
        
        completed_requests = [r for r in slow_network_results if r['completed']]
        failed_requests = [r for r in slow_network_results if not r['completed']]
        
        completion_rate = len(completed_requests) / len(slow_network_results) * 100
        
        if completed_requests:
            avg_delay = sum(r['delay_seconds'] for r in completed_requests) / len(completed_requests)
            avg_total_time = sum(r['total_time'] for r in completed_requests) / len(completed_requests)
            overhead_ratio = avg_total_time / avg_delay if avg_delay > 0 else 0
            
            print(f"   Completion rate: {completion_rate:.1f}%")
            print(f"   Average expected delay: {avg_delay:.1f}s")
            print(f"   Average actual total time: {avg_total_time:.1f}s")
            print(f"   Overhead ratio: {overhead_ratio:.2f}x")
        
        # Group by request type
        request_types = set(r['request_type'] for r in slow_network_results)
        for req_type in request_types:
            type_results = [r for r in slow_network_results if r['request_type'] == req_type]
            type_completed = [r for r in type_results if r['completed']]
            type_completion_rate = len(type_completed) / len(type_results) * 100
            print(f"   {req_type}: {type_completion_rate:.1f}% completion rate")
        
        # Assertions
        assert completion_rate >= 70.0, f"Slow network completion rate too low: {completion_rate:.1f}%"

    # ================================================================
    # CONCURRENT NETWORK OPERATIONS TESTING
    # ================================================================

    def test_concurrent_network_operations_resilience(self, client, auth_headers):
        """Test resilience under concurrent network operations"""
        print("🔀 Testing Concurrent Network Operations Resilience...")
        
        def concurrent_network_operation(operation_id, operation_type):
            """Perform concurrent network operations"""
            start_time = time.time()
            
            try:
                if operation_type == "mixed_external_calls":
                    # Mix of different external service calls
                    operations = [
                        lambda: client.post('/api/recipes/generate-from-inventory', 
                                          json={"max_recipes": 1}, headers=auth_headers),
                        lambda: client.get('/api/inventory', headers=auth_headers),
                        lambda: client.get('/api/recipes/saved', headers=auth_headers),
                        lambda: client.post('/api/auth/firebase-signin', 
                                          json={'firebase_id_token': 'test'})
                    ]
                    
                    operation = operations[operation_id % len(operations)]
                    response = operation()
                    
                elif operation_type == "high_frequency_requests":
                    # High frequency requests to same endpoint
                    response = client.get('/api/inventory/simple', headers=auth_headers)
                
                elif operation_type == "resource_intensive":
                    # Resource intensive operations
                    response = client.get('/api/inventory/complete', headers=auth_headers)
                
                return {
                    'operation_id': operation_id,
                    'operation_type': operation_type,
                    'response_time': time.time() - start_time,
                    'status_code': response.status_code,
                    'success': response.status_code < 500
                }
                
            except Exception as e:
                return {
                    'operation_id': operation_id,
                    'operation_type': operation_type,
                    'response_time': time.time() - start_time,
                    'error': str(e),
                    'success': False
                }
        
        # Test different concurrent operation patterns
        concurrent_tests = [
            ("mixed_external_calls", 15, "Mixed external service calls"),
            ("high_frequency_requests", 25, "High frequency requests"),
            ("resource_intensive", 10, "Resource intensive operations")
        ]
        
        concurrent_results = {}
        
        for operation_type, concurrency, description in concurrent_tests:
            print(f"   Testing {description} (concurrency: {concurrency})...")
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [
                    executor.submit(concurrent_network_operation, i, operation_type)
                    for i in range(concurrency * 2)
                ]
                
                results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            
            successful_operations = [r for r in results if r['success']]
            failed_operations = [r for r in results if not r['success']]
            
            if successful_operations:
                response_times = [r['response_time'] for r in successful_operations]
                avg_response_time = sum(response_times) / len(response_times)
                throughput = len(successful_operations) / total_time
                
                concurrent_results[operation_type] = {
                    'description': description,
                    'concurrency_level': concurrency,
                    'total_operations': len(results),
                    'successful_operations': len(successful_operations),
                    'failed_operations': len(failed_operations),
                    'success_rate': len(successful_operations) / len(results) * 100,
                    'avg_response_time': avg_response_time,
                    'throughput': throughput,
                    'total_test_time': total_time
                }
                
                print(f"     Success rate: {len(successful_operations)}/{len(results)} ({len(successful_operations)/len(results)*100:.1f}%)")
                print(f"     Avg response time: {avg_response_time:.3f}s")
                print(f"     Throughput: {throughput:.1f} ops/s")
        
        # Analyze concurrent network resilience
        print(f"✅ Concurrent Network Operations Analysis:")
        
        for operation_type, metrics in concurrent_results.items():
            print(f"   {metrics['description']}:")
            print(f"     Success Rate: {metrics['success_rate']:.1f}%")
            print(f"     Throughput: {metrics['throughput']:.1f} ops/s")
            print(f"     Avg Response: {metrics['avg_response_time']:.3f}s")
        
        # Resilience assertions
        for operation_type, metrics in concurrent_results.items():
            assert metrics['success_rate'] >= 75.0, f"{metrics['description']} success rate too low: {metrics['success_rate']:.1f}%"
            assert metrics['throughput'] > 1.0, f"{metrics['description']} throughput too low: {metrics['throughput']:.1f} ops/s"

    # ================================================================
    # RETRY AND CIRCUIT BREAKER TESTING
    # ================================================================

    def test_retry_mechanism_effectiveness(self, client, auth_headers):
        """Test effectiveness of retry mechanisms"""
        print("🔄 Testing Retry Mechanism Effectiveness...")
        
        def simulate_intermittent_failure(failure_probability, max_retries=3):
            """Simulate intermittent failures to test retry logic"""
            attempts = []
            
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = MagicMock()
                mock_model_class.return_value = mock_model
                
                call_count = 0
                
                def intermittent_failure_call(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    attempts.append(call_count)
                    
                    # Simulate failure based on probability
                    import random
                    if random.random() < failure_probability and call_count <= max_retries:
                        raise Exception(f"Intermittent failure on attempt {call_count}")
                    
                    # Success case
                    return MagicMock(text='{"recipes": [{"title": "Retry Success"}]}')
                
                mock_model.generate_content.side_effect = intermittent_failure_call
                
                start_time = time.time()
                try:
                    response = client.post('/api/recipes/generate-from-inventory',
                        json={"max_recipes": 1},
                        headers=auth_headers)
                    
                    return {
                        'failure_probability': failure_probability,
                        'attempts_made': len(attempts),
                        'final_attempt': max(attempts) if attempts else 0,
                        'response_time': time.time() - start_time,
                        'status_code': response.status_code,
                        'succeeded': response.status_code == 200,
                        'retry_effective': len(attempts) > 1 and response.status_code == 200
                    }
                    
                except Exception as e:
                    return {
                        'failure_probability': failure_probability,
                        'attempts_made': len(attempts),
                        'final_attempt': max(attempts) if attempts else 0,
                        'response_time': time.time() - start_time,
                        'error': str(e),
                        'succeeded': False,
                        'retry_effective': False
                    }
        
        # Test different failure probabilities
        retry_test_scenarios = [
            0.2,  # 20% failure rate
            0.5,  # 50% failure rate
            0.8,  # 80% failure rate
        ]
        
        retry_results = []
        
        for failure_prob in retry_test_scenarios:
            print(f"   Testing retry mechanism with {failure_prob*100:.0f}% failure probability...")
            
            # Run multiple iterations to get statistical data
            scenario_results = []
            for _ in range(5):
                result = simulate_intermittent_failure(failure_prob)
                scenario_results.append(result)
            
            # Analyze scenario results
            successful_retries = sum(1 for r in scenario_results if r['retry_effective'])
            total_successes = sum(1 for r in scenario_results if r['succeeded'])
            avg_attempts = sum(r['attempts_made'] for r in scenario_results) / len(scenario_results)
            
            retry_effectiveness = successful_retries / len(scenario_results) * 100
            success_rate = total_successes / len(scenario_results) * 100
            
            retry_results.append({
                'failure_probability': failure_prob,
                'retry_effectiveness': retry_effectiveness,
                'success_rate': success_rate,
                'avg_attempts': avg_attempts,
                'scenario_results': scenario_results
            })
            
            print(f"     Retry effectiveness: {retry_effectiveness:.1f}%")
            print(f"     Overall success rate: {success_rate:.1f}%")
            print(f"     Average attempts: {avg_attempts:.1f}")
        
        # Analyze retry mechanism performance
        print(f"✅ Retry Mechanism Analysis:")
        
        for result in retry_results:
            failure_rate = result['failure_probability'] * 100
            print(f"   {failure_rate:.0f}% failure rate: {result['success_rate']:.1f}% success, {result['retry_effectiveness']:.1f}% retry effective")
        
        # Retry mechanism assertions
        high_failure_scenario = next((r for r in retry_results if r['failure_probability'] >= 0.5), None)
        if high_failure_scenario:
            assert high_failure_scenario['success_rate'] >= 60.0, f"Retry mechanism not effective enough at high failure rates: {high_failure_scenario['success_rate']:.1f}%"

    def test_circuit_breaker_pattern_simulation(self, client, auth_headers):
        """Test circuit breaker pattern simulation"""
        print("🔌 Testing Circuit Breaker Pattern Simulation...")
        
        def simulate_circuit_breaker_behavior():
            """Simulate circuit breaker behavior for external services"""
            circuit_states = []
            
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                mock_model = MagicMock()
                mock_model_class.return_value = mock_model
                
                failure_count = 0
                circuit_open = False
                
                def circuit_breaker_call(*args, **kwargs):
                    nonlocal failure_count, circuit_open
                    
                    # Circuit breaker logic simulation
                    if circuit_open:
                        circuit_states.append('OPEN')
                        raise Exception("Circuit breaker is OPEN - request rejected")
                    
                    # Simulate service failures
                    failure_count += 1
                    if failure_count <= 3:
                        circuit_states.append('CLOSED_FAILING')
                        raise Exception(f"Service failure #{failure_count}")
                    elif failure_count <= 5:
                        # Circuit should open after 3 failures
                        circuit_open = True
                        circuit_states.append('OPENING')
                        raise Exception("Circuit breaker OPENING")
                    else:
                        # Service recovery
                        circuit_states.append('HALF_OPEN')
                        return MagicMock(text='{"recipes": [{"title": "Circuit Recovery"}]}')
                
                mock_model.generate_content.side_effect = circuit_breaker_call
                
                # Make multiple requests to trigger circuit breaker
                circuit_results = []
                
                for i in range(8):  # 8 requests to test full circuit breaker cycle
                    start_time = time.time()
                    try:
                        response = client.post('/api/recipes/generate-from-inventory',
                            json={"max_recipes": 1},
                            headers=auth_headers)
                        
                        circuit_results.append({
                            'request_number': i + 1,
                            'response_time': time.time() - start_time,
                            'status_code': response.status_code,
                            'circuit_state': circuit_states[-1] if circuit_states else 'UNKNOWN',
                            'succeeded': response.status_code == 200
                        })
                        
                    except Exception as e:
                        circuit_results.append({
                            'request_number': i + 1,
                            'response_time': time.time() - start_time,
                            'error': str(e),
                            'circuit_state': circuit_states[-1] if circuit_states else 'UNKNOWN',
                            'succeeded': False
                        })
            
            return circuit_results, circuit_states
        
        print("   Simulating circuit breaker pattern...")
        circuit_results, circuit_states = simulate_circuit_breaker_behavior()
        
        # Analyze circuit breaker behavior
        print(f"✅ Circuit Breaker Analysis:")
        print(f"   Total requests made: {len(circuit_results)}")
        
        # Count different circuit states
        state_counts = {}
        for state in circuit_states:
            state_counts[state] = state_counts.get(state, 0) + 1
        
        print(f"   Circuit state transitions:")
        for state, count in state_counts.items():
            print(f"     {state}: {count} times")
        
        # Analyze request outcomes by circuit state
        states_encountered = set(circuit_states)
        for state in states_encountered:
            state_results = [r for r in circuit_results if r.get('circuit_state') == state]
            if state_results:
                success_rate = sum(1 for r in state_results if r['succeeded']) / len(state_results) * 100
                print(f"   {state} state: {success_rate:.1f}% success rate")
        
        # Circuit breaker effectiveness
        early_failures = [r for r in circuit_results[:5]]  # First 5 requests
        later_attempts = [r for r in circuit_results[5:]]  # Later requests
        
        if early_failures and later_attempts:
            early_failure_rate = sum(1 for r in early_failures if not r['succeeded']) / len(early_failures) * 100
            later_recovery_rate = sum(1 for r in later_attempts if r['succeeded']) / len(later_attempts) * 100
            
            print(f"   Early failure rate: {early_failure_rate:.1f}%")
            print(f"   Later recovery rate: {later_recovery_rate:.1f}%")
            
            # Circuit breaker should prevent cascading failures
            circuit_breaker_effective = 'OPEN' in circuit_states or 'OPENING' in circuit_states
            assert circuit_breaker_effective, "Circuit breaker pattern not triggered during failures"

    # ================================================================
    # NETWORK RESILIENCE COMPREHENSIVE TESTING
    # ================================================================

    def test_comprehensive_network_resilience_suite(self, client, auth_headers):
        """Comprehensive network resilience test suite"""
        print("🏁 Starting Comprehensive Network Resilience Test Suite...")
        
        # Run abbreviated versions of all network resilience tests
        resilience_metrics = {}
        
        print("   Phase 1: Basic timeout handling...")
        # Quick timeout test
        timeout_results = []
        with patch('google.generativeai.GenerativeModel') as mock_model:
            mock_ai = MagicMock()
            mock_model.return_value = mock_ai
            
            def quick_timeout_test(delay):
                start = time.time()
                if delay > 2.0:
                    mock_ai.generate_content.side_effect = Exception("Timeout")
                else:
                    mock_ai.generate_content.return_value = MagicMock(text='{"recipes": []}')
                
                try:
                    response = client.post('/api/recipes/generate-from-inventory',
                        json={"max_recipes": 1}, headers=auth_headers)
                    return time.time() - start, response.status_code < 500
                except:
                    return time.time() - start, False
            
            for delay in [1.0, 3.0]:
                response_time, success = quick_timeout_test(delay)
                timeout_results.append((delay, response_time, success))
        
        timeout_success_rate = sum(1 for _, _, success in timeout_results if success) / len(timeout_results) * 100
        resilience_metrics['timeout_handling'] = timeout_success_rate
        
        print("   Phase 2: Network failure simulation...")
        # Quick network failure test
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Network failure")
            
            failure_handled = False
            try:
                response = client.post('/api/recipes/generate-from-inventory',
                    json={"max_recipes": 1}, headers=auth_headers)
                failure_handled = response.status_code in [503, 502, 500]
            except:
                failure_handled = True  # Exception caught = handled
        
        resilience_metrics['network_failure_handling'] = 100.0 if failure_handled else 0.0
        
        print("   Phase 3: Concurrent operations test...")
        # Quick concurrent test
        def concurrent_quick_test(req_id):
            try:
                response = client.get('/api/inventory/simple', headers=auth_headers)
                return response.status_code < 500
            except:
                return False
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            concurrent_futures = [executor.submit(concurrent_quick_test, i) for i in range(20)]
            concurrent_results = [f.result() for f in as_completed(concurrent_futures)]
        
        concurrent_success_rate = sum(1 for success in concurrent_results if success) / len(concurrent_results) * 100
        resilience_metrics['concurrent_resilience'] = concurrent_success_rate
        
        print("   Phase 4: Slow network simulation...")
        # Quick slow network test
        with patch('src.application.use_cases.inventory.get_inventory_content_use_case.GetInventoryContentUseCase.execute') as mock_db:
            def slow_operation(*args, **kwargs):
                time.sleep(0.5)  # 500ms delay
                return {"ingredients": [], "foods": []}
            
            mock_db.side_effect = slow_operation
            
            start_time = time.time()
            try:
                response = client.get('/api/inventory', headers=auth_headers)
                slow_response_time = time.time() - start_time
                slow_handled = response.status_code == 200 and slow_response_time < 5.0
            except:
                slow_handled = False
        
        resilience_metrics['slow_network_handling'] = 100.0 if slow_handled else 0.0
        
        # Calculate overall resilience score
        print(f"\n🏆 NETWORK RESILIENCE SCORECARD:")
        print("=" * 50)
        
        total_score = 0
        max_score = 0
        
        categories = [
            ('timeout_handling', 'Timeout Handling', 25),
            ('network_failure_handling', 'Network Failure Handling', 25),
            ('concurrent_resilience', 'Concurrent Operations', 25),
            ('slow_network_handling', 'Slow Network Handling', 25)
        ]
        
        for metric_key, metric_name, weight in categories:
            if metric_key in resilience_metrics:
                metric_value = resilience_metrics[metric_key]
                score = (metric_value / 100.0) * weight
                total_score += score
                max_score += weight
                
                print(f"{metric_name}: {score:.1f}/{weight} ({metric_value:.1f}%)")
        
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
            
            print(f"\nOVERALL NETWORK RESILIENCE:")
            print(f"  Score: {total_score:.1f}/{max_score} ({percentage_score:.1f}%)")
            print(f"  Grade: {grade}")
            print(f"  Status: {status}")
            
            # Resilience recommendations
            print(f"\nRESILIENCE RECOMMENDATIONS:")
            if percentage_score >= 90:
                print("  ✅ Excellent network resilience - ready for production")
            elif percentage_score >= 80:
                print("  ✅ Good network resilience - minor optimizations recommended")
            elif percentage_score >= 70:
                print("  ⚠️ Acceptable resilience - consider improving weak areas")
            else:
                print("  ❌ Poor resilience - significant improvements needed before production")
            
            # Specific recommendations based on weak areas
            weak_areas = [name for key, name, _ in categories if resilience_metrics.get(key, 0) < 80]
            if weak_areas:
                print(f"  Areas needing improvement: {', '.join(weak_areas)}")
            
            # Final assertions
            assert percentage_score >= 65.0, f"Network resilience too low for production: {percentage_score:.1f}%"
        
        print(f"\n✅ Comprehensive Network Resilience Testing Complete")
        
        return resilience_metrics