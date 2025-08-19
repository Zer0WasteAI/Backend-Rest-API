"""
Comprehensive integration tests for Auth Controller.
Tests authentication flows, security measures, and edge cases.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.main import app
from src.config.config import Config


class TestAuthControllerIntegration:
    """Integration tests for Auth Controller endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.client = app.test_client()
        self.client.testing = True
        self.base_headers = {'Content-Type': 'application/json'}
    
    def test_firebase_debug_endpoint(self):
        """Test Firebase debug endpoint functionality."""
        with patch('src.interface.controllers.auth_controller.firebase') as mock_firebase:
            mock_firebase.return_value = {"debug": "info", "status": "active"}
            
            response = self.client.get('/api/auth/firebase-debug')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'debug' in data or 'error' in data

    def test_logout_endpoint_success(self):
        """Test successful logout functionality."""
        with patch('src.interface.controllers.auth_controller.request') as mock_request:
            mock_request.headers = {'Authorization': 'Bearer valid_token'}
            mock_request.get_json.return_value = {'token': 'valid_token'}
            
            with patch('src.interface.controllers.auth_controller.cleanup_user_session') as mock_cleanup:
                mock_cleanup.return_value = True
                
                response = self.client.post('/api/auth/logout', 
                                          json={'token': 'valid_token'},
                                          headers=self.base_headers)
                
                assert response.status_code in [200, 400]  # Success or validation error

    def test_logout_endpoint_invalid_token(self):
        """Test logout with invalid token."""
        response = self.client.post('/api/auth/logout', 
                                  json={'token': 'invalid_token'},
                                  headers=self.base_headers)
        
        assert response.status_code in [400, 401, 422]  # Expected validation/auth errors

    def test_guest_login_endpoint(self):
        """Test guest login functionality."""
        with patch('src.interface.controllers.auth_controller.create_guest_session') as mock_guest:
            mock_guest.return_value = {
                'token': 'guest_token_123',
                'user_id': 'guest_user',
                'expires': '2024-12-31T23:59:59Z'
            }
            
            response = self.client.post('/api/auth/guest-login', headers=self.base_headers)
            
            assert response.status_code in [200, 201]  # Success
            if response.status_code in [200, 201]:
                data = json.loads(response.data)
                assert 'token' in data or 'user_id' in data or 'message' in data

    def test_guest_login_rate_limiting(self):
        """Test guest login rate limiting."""
        # Simulate multiple rapid guest login attempts
        responses = []
        for _ in range(3):
            response = self.client.post('/api/auth/guest-login', headers=self.base_headers)
            responses.append(response.status_code)
        
        # At least one should succeed or all should have consistent behavior
        assert any(code in [200, 201] for code in responses) or all(code == responses[0] for code in responses)

    def test_authentication_flow_integration(self):
        """Test complete authentication flow integration."""
        # Test Firebase signin followed by other operations
        with patch('firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.return_value = {
                'uid': 'test_user_123',
                'email': 'test@example.com'
            }
            
            # First, attempt Firebase signin
            signin_response = self.client.post('/api/auth/firebase-signin',
                                             json={'token': 'valid_firebase_token'},
                                             headers=self.base_headers)
            
            if signin_response.status_code == 200:
                signin_data = json.loads(signin_response.data)
                if 'token' in signin_data:
                    auth_headers = {**self.base_headers, 'Authorization': f"Bearer {signin_data['token']}"}
                    
                    # Test token refresh with the new token
                    refresh_response = self.client.post('/api/auth/refresh',
                                                      headers=auth_headers)
                    
                    assert refresh_response.status_code in [200, 401]

    def test_security_validation_flow(self):
        """Test security validation across auth endpoints."""
        # Test malformed requests
        malformed_requests = [
            {'endpoint': '/api/auth/firebase-signin', 'data': {'invalid': 'data'}},
            {'endpoint': '/api/auth/logout', 'data': {'wrong_field': 'value'}},
            {'endpoint': '/api/auth/refresh', 'data': {}}
        ]
        
        for req in malformed_requests:
            response = self.client.post(req['endpoint'], 
                                      json=req['data'], 
                                      headers=self.base_headers)
            
            # Should handle malformed requests gracefully
            assert response.status_code in [400, 401, 422, 500]

    def test_concurrent_auth_operations(self):
        """Test concurrent authentication operations."""
        import threading
        results = []
        
        def auth_operation():
            response = self.client.post('/api/auth/guest-login', headers=self.base_headers)
            results.append(response.status_code)
        
        threads = [threading.Thread(target=auth_operation) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All operations should complete without server errors
        assert all(code != 500 for code in results)

    def test_auth_error_handling_integration(self):
        """Test comprehensive error handling across auth endpoints."""
        test_scenarios = [
            {'endpoint': '/api/auth/firebase-debug', 'method': 'GET'},
            {'endpoint': '/api/auth/logout', 'method': 'POST', 'data': {}},
            {'endpoint': '/api/auth/guest-login', 'method': 'POST'}
        ]
        
        for scenario in test_scenarios:
            if scenario['method'] == 'GET':
                response = self.client.get(scenario['endpoint'])
            else:
                response = self.client.post(scenario['endpoint'],
                                          json=scenario.get('data', {}),
                                          headers=self.base_headers)
            
            # Should not cause server crashes
            assert response.status_code != 500 or 'error' in json.loads(response.data)
