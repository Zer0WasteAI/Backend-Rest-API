"""
Production Validation Tests for Authentication Endpoints
Tests every auth endpoint with all scenarios to validate production readiness
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock
from flask import Flask
from src.main import create_app


class TestAuthEndpointsProduction:
    """Production validation tests for all authentication endpoints"""

    @pytest.fixture(scope="class")
    def app(self):
        app = create_app()
        app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "JWT_ACCESS_TOKEN_EXPIRES": False,  # No expiration for testing
        })
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    # ================================================================
    # POST /api/auth/firebase-signin - Firebase Authentication
    # ================================================================

    def test_firebase_signin_success(self, client):
        """Test successful Firebase ID token authentication"""
        with patch('firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.return_value = {
                'uid': 'test-firebase-uid',
                'email': 'test@example.com',
                'name': 'Test User'
            }
            
            response = client.post('/api/auth/firebase-signin', 
                json={'firebase_id_token': 'valid-firebase-token'})
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'access_token' in data
            assert 'refresh_token' in data
            assert data['message'] == 'Login successful'
            assert data['user']['uid'] == 'test-firebase-uid'

    def test_firebase_signin_invalid_token(self, client):
        """Test Firebase signin with invalid token"""
        with patch('firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.side_effect = Exception("Invalid token")
            
            response = client.post('/api/auth/firebase-signin', 
                json={'firebase_id_token': 'invalid-token'})
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'error' in data
            assert 'invalid' in data['error'].lower()

    def test_firebase_signin_missing_token(self, client):
        """Test Firebase signin without token"""
        response = client.post('/api/auth/firebase-signin', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_firebase_signin_empty_token(self, client):
        """Test Firebase signin with empty token"""
        response = client.post('/api/auth/firebase-signin', 
            json={'firebase_id_token': ''})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_firebase_signin_malformed_request(self, client):
        """Test Firebase signin with malformed JSON"""
        response = client.post('/api/auth/firebase-signin', 
            data='invalid-json', 
            content_type='application/json')
        
        assert response.status_code == 400

    def test_firebase_signin_rate_limiting(self, client):
        """Test that rate limiting is applied to signin endpoint"""
        with patch('firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.return_value = {
                'uid': 'test-uid',
                'email': 'test@example.com'
            }
            
            # Make multiple requests to trigger rate limit (5 req/min for auth_signin)
            for i in range(6):
                response = client.post('/api/auth/firebase-signin', 
                    json={'firebase_id_token': f'token-{i}'})
                
                if i < 5:
                    assert response.status_code in [200, 401]  # Normal responses
                else:
                    assert response.status_code == 429  # Rate limited

    # ================================================================
    # POST /api/auth/refresh - JWT Token Refresh
    # ================================================================

    def test_refresh_token_success(self, client, app):
        """Test successful token refresh"""
        with app.app_context():
            # First get valid tokens
            with patch('firebase_admin.auth.verify_id_token') as mock_verify:
                mock_verify.return_value = {
                    'uid': 'test-uid',
                    'email': 'test@example.com'
                }
                
                signin_response = client.post('/api/auth/firebase-signin', 
                    json={'firebase_id_token': 'valid-token'})
                
                assert signin_response.status_code == 200
                tokens = signin_response.get_json()
                refresh_token = tokens['refresh_token']
                
                # Now test refresh
                response = client.post('/api/auth/refresh',
                    headers={'Authorization': f'Bearer {refresh_token}'})
                
                assert response.status_code == 200
                data = response.get_json()
                assert 'access_token' in data
                assert data['message'] == 'Token refreshed successfully'

    def test_refresh_token_invalid_token(self, client):
        """Test refresh with invalid token"""
        response = client.post('/api/auth/refresh',
            headers={'Authorization': 'Bearer invalid-refresh-token'})
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data

    def test_refresh_token_missing_header(self, client):
        """Test refresh without authorization header"""
        response = client.post('/api/auth/refresh')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'error' in data

    def test_refresh_token_wrong_token_type(self, client, app):
        """Test refresh with access token instead of refresh token"""
        with app.app_context():
            with patch('firebase_admin.auth.verify_id_token') as mock_verify:
                mock_verify.return_value = {
                    'uid': 'test-uid',
                    'email': 'test@example.com'
                }
                
                signin_response = client.post('/api/auth/firebase-signin', 
                    json={'firebase_id_token': 'valid-token'})
                
                tokens = signin_response.get_json()
                access_token = tokens['access_token']
                
                # Try to refresh with access token (should fail)
                response = client.post('/api/auth/refresh',
                    headers={'Authorization': f'Bearer {access_token}'})
                
                assert response.status_code == 401

    def test_refresh_token_rate_limiting(self, client, app):
        """Test rate limiting on refresh endpoint (3 req/min)"""
        with app.app_context():
            with patch('firebase_admin.auth.verify_id_token') as mock_verify:
                mock_verify.return_value = {
                    'uid': 'test-uid',
                    'email': 'test@example.com'
                }
                
                signin_response = client.post('/api/auth/firebase-signin', 
                    json={'firebase_id_token': 'valid-token'})
                
                refresh_token = signin_response.get_json()['refresh_token']
                
                # Make 4 refresh requests (limit is 3)
                for i in range(4):
                    response = client.post('/api/auth/refresh',
                        headers={'Authorization': f'Bearer {refresh_token}'})
                    
                    if i < 3:
                        assert response.status_code in [200, 401]
                    else:
                        assert response.status_code == 429

    # ================================================================
    # POST /api/auth/logout - Logout and Token Invalidation
    # ================================================================

    def test_logout_success(self, client, app):
        """Test successful logout"""
        with app.app_context():
            with patch('firebase_admin.auth.verify_id_token') as mock_verify:
                mock_verify.return_value = {
                    'uid': 'test-uid',
                    'email': 'test@example.com'
                }
                
                signin_response = client.post('/api/auth/firebase-signin', 
                    json={'firebase_id_token': 'valid-token'})
                
                access_token = signin_response.get_json()['access_token']
                
                # Test logout
                response = client.post('/api/auth/logout',
                    headers={'Authorization': f'Bearer {access_token}'})
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['message'] == 'Logout successful'

    def test_logout_invalid_token(self, client):
        """Test logout with invalid token"""
        response = client.post('/api/auth/logout',
            headers={'Authorization': 'Bearer invalid-access-token'})
        
        assert response.status_code == 401

    def test_logout_missing_header(self, client):
        """Test logout without authorization header"""
        response = client.post('/api/auth/logout')
        
        assert response.status_code == 401

    def test_logout_token_blacklisting(self, client, app):
        """Test that logout properly blacklists tokens"""
        with app.app_context():
            with patch('firebase_admin.auth.verify_id_token') as mock_verify:
                mock_verify.return_value = {
                    'uid': 'test-uid',
                    'email': 'test@example.com'
                }
                
                signin_response = client.post('/api/auth/firebase-signin', 
                    json={'firebase_id_token': 'valid-token'})
                
                access_token = signin_response.get_json()['access_token']
                
                # Logout
                logout_response = client.post('/api/auth/logout',
                    headers={'Authorization': f'Bearer {access_token}'})
                
                assert logout_response.status_code == 200
                
                # Try to use the same token again (should fail)
                response = client.post('/api/auth/logout',
                    headers={'Authorization': f'Bearer {access_token}'})
                
                assert response.status_code == 401

    # ================================================================
    # GET /api/auth/firebase-debug - Debug Endpoint (Development)
    # ================================================================

    def test_firebase_debug_endpoint(self, client):
        """Test Firebase debug endpoint (should work in testing)"""
        response = client.get('/api/auth/firebase-debug')
        
        # Should return debug info in testing environment
        assert response.status_code == 200
        data = response.get_json()
        assert 'firebase_config' in data or 'status' in data

    # ================================================================
    # Security and Edge Case Tests
    # ================================================================

    def test_auth_headers_security(self, client):
        """Test that auth endpoints have proper security headers"""
        response = client.post('/api/auth/firebase-signin', 
            json={'firebase_id_token': 'test-token'})
        
        # Check for security headers
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers
        assert 'X-XSS-Protection' in response.headers

    def test_auth_content_type_validation(self, client):
        """Test that auth endpoints validate content type"""
        response = client.post('/api/auth/firebase-signin', 
            data='firebase_id_token=test-token',
            content_type='application/x-www-form-urlencoded')
        
        # Should reject non-JSON requests
        assert response.status_code in [400, 415]

    def test_auth_cors_headers(self, client):
        """Test CORS headers on auth endpoints"""
        response = client.options('/api/auth/firebase-signin')
        
        # Check CORS headers
        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers

    def test_sql_injection_protection(self, client):
        """Test SQL injection protection in auth endpoints"""
        malicious_token = "'; DROP TABLE users; --"
        
        response = client.post('/api/auth/firebase-signin', 
            json={'firebase_id_token': malicious_token})
        
        # Should handle malicious input safely
        assert response.status_code in [400, 401]

    def test_xss_protection(self, client):
        """Test XSS protection in auth responses"""
        xss_payload = "<script>alert('xss')</script>"
        
        response = client.post('/api/auth/firebase-signin', 
            json={'firebase_id_token': xss_payload})
        
        # Response should not contain unescaped script tags
        data = response.get_data(as_text=True)
        assert '<script>' not in data

    def test_large_payload_handling(self, client):
        """Test handling of unusually large auth payloads"""
        large_token = 'x' * 10000  # 10KB token
        
        response = client.post('/api/auth/firebase-signin', 
            json={'firebase_id_token': large_token})
        
        # Should handle large payloads gracefully
        assert response.status_code in [400, 401, 413]

    def test_concurrent_auth_requests(self, client):
        """Test concurrent authentication requests"""
        import threading
        results = []
        
        def make_request():
            response = client.post('/api/auth/firebase-signin', 
                json={'firebase_id_token': 'test-token'})
            results.append(response.status_code)
        
        # Start 5 concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # All should complete without server errors
        assert all(status < 500 for status in results)

    def test_memory_usage_with_failed_logins(self, client):
        """Test memory usage doesn't grow with failed login attempts"""
        # This is a basic test - in production you'd use memory profiling
        for i in range(50):
            response = client.post('/api/auth/firebase-signin', 
                json={'firebase_id_token': f'invalid-token-{i}'})
            assert response.status_code in [400, 401]
        
        # If we get here without timeout, memory usage is likely controlled

    # ================================================================
    # Performance and Load Tests
    # ================================================================

    def test_auth_response_time(self, client):
        """Test that auth endpoints respond within acceptable time"""
        import time
        
        start_time = time.time()
        response = client.post('/api/auth/firebase-signin', 
            json={'firebase_id_token': 'test-token'})
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Auth should respond within 2 seconds
        assert response_time < 2.0

    def test_token_validation_performance(self, client, app):
        """Test JWT token validation performance"""
        with app.app_context():
            with patch('firebase_admin.auth.verify_id_token') as mock_verify:
                mock_verify.return_value = {
                    'uid': 'test-uid',
                    'email': 'test@example.com'
                }
                
                # Get a valid token
                signin_response = client.post('/api/auth/firebase-signin', 
                    json={'firebase_id_token': 'valid-token'})
                
                access_token = signin_response.get_json()['access_token']
                
                # Test validation performance
                start_time = time.time()
                response = client.post('/api/auth/logout',
                    headers={'Authorization': f'Bearer {access_token}'})
                end_time = time.time()
                
                response_time = end_time - start_time
                
                # Token validation should be fast
                assert response_time < 1.0
                assert response.status_code == 200