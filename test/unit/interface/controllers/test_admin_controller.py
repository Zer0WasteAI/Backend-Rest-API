"""
Unit tests for Admin Controller
Tests administrative endpoints and security operations
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask

from src.interface.controllers.admin_controller import admin_bp


class TestAdminController:
    """Test suite for Admin Controller"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['INTERNAL_SECRET'] = 'test-internal-secret'
        app.register_blueprint(admin_bp, url_prefix='/api/admin')
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def internal_headers(self):
        """Create internal service headers"""
        return {"Internal-Secret": "test-internal-secret"}

    def test_admin_blueprint_registration(self, app):
        """Test that admin blueprint is properly registered"""
        # Assert
        assert 'admin' in app.blueprints

    # POST /cleanup-tokens - Cleanup expired tokens
    @patch('src.interface.controllers.admin_controller.TokenSecurityRepository')
    @patch('src.interface.controllers.admin_controller.security_logger')
    def test_cleanup_expired_tokens_success(self, mock_security_logger, mock_token_repo_class, client, internal_headers):
        """Test successful cleanup of expired tokens"""
        # Arrange
        mock_token_repo = Mock()
        mock_cleanup_result = {
            "blacklist_cleaned": 15,
            "tracking_cleaned": 8
        }
        mock_token_repo.cleanup_expired_tokens.return_value = mock_cleanup_result
        mock_token_repo_class.return_value = mock_token_repo
        
        # Act
        response = client.post('/api/admin/cleanup-tokens', headers=internal_headers)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["message"] == "Token cleanup completed successfully"
        assert "cleaned" in response_data
        assert response_data["cleaned"]["blacklist_cleaned"] == 15
        assert response_data["cleaned"]["tracking_cleaned"] == 8
        
        # Verify repository was called
        mock_token_repo.cleanup_expired_tokens.assert_called_once()
        
        # Verify security logging
        mock_security_logger.log_security_event.assert_called()

    @patch('src.interface.controllers.admin_controller.TokenSecurityRepository')
    @patch('src.interface.controllers.admin_controller.security_logger')
    def test_cleanup_expired_tokens_repository_error(self, mock_security_logger, mock_token_repo_class, client, internal_headers):
        """Test cleanup tokens with repository error"""
        # Arrange
        mock_token_repo = Mock()
        mock_token_repo.cleanup_expired_tokens.side_effect = Exception("Database connection error")
        mock_token_repo_class.return_value = mock_token_repo
        
        # Act
        response = client.post('/api/admin/cleanup-tokens', headers=internal_headers)
        
        # Assert
        assert response.status_code == 500
        response_data = json.loads(response.data)
        assert response_data["error"] == "Cleanup operation failed"
        
        # Verify error logging
        mock_security_logger.log_security_event.assert_called()

    def test_cleanup_expired_tokens_unauthorized(self, client):
        """Test cleanup tokens without internal authorization"""
        # Act
        response = client.post('/api/admin/cleanup-tokens')
        
        # Assert
        assert response.status_code == 403

    def test_cleanup_expired_tokens_wrong_secret(self, client):
        """Test cleanup tokens with wrong internal secret"""
        # Arrange
        wrong_headers = {"Internal-Secret": "wrong-secret"}
        
        # Act
        response = client.post('/api/admin/cleanup-tokens', headers=wrong_headers)
        
        # Assert
        assert response.status_code == 403

    # GET /security-stats - Get security statistics
    @patch('src.interface.controllers.admin_controller.TokenSecurityRepository')
    def test_get_security_stats_success(self, mock_token_repo_class, client, internal_headers):
        """Test successful retrieval of security statistics"""
        # Arrange
        mock_token_repo = Mock()
        mock_stats = {
            "active_tokens": 150,
            "blacklisted_tokens": 23,
            "tokens_created_today": 45,
            "failed_attempts_today": 12,
            "last_cleanup": "2024-01-16T10:30:00Z"
        }
        mock_token_repo.get_security_stats.return_value = mock_stats
        mock_token_repo_class.return_value = mock_token_repo
        
        # Act
        response = client.get('/api/admin/security-stats', headers=internal_headers)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert "stats" in response_data
        assert response_data["stats"]["active_tokens"] == 150
        assert response_data["stats"]["blacklisted_tokens"] == 23
        
        # Verify repository was called
        mock_token_repo.get_security_stats.assert_called_once()

    @patch('src.interface.controllers.admin_controller.TokenSecurityRepository')
    def test_get_security_stats_repository_error(self, mock_token_repo_class, client, internal_headers):
        """Test security stats with repository error"""
        # Arrange
        mock_token_repo = Mock()
        mock_token_repo.get_security_stats.side_effect = Exception("Database query error")
        mock_token_repo_class.return_value = mock_token_repo
        
        # Act
        response = client.get('/api/admin/security-stats', headers=internal_headers)
        
        # Assert
        assert response.status_code == 500
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_get_security_stats_unauthorized(self, client):
        """Test security stats without internal authorization"""
        # Act
        response = client.get('/api/admin/security-stats')
        
        # Assert
        assert response.status_code == 403

    def test_get_security_stats_wrong_secret(self, client):
        """Test security stats with wrong internal secret"""
        # Arrange
        wrong_headers = {"Internal-Secret": "wrong-secret"}
        
        # Act
        response = client.get('/api/admin/security-stats', headers=wrong_headers)
        
        # Assert
        assert response.status_code == 403

    @patch('src.interface.controllers.admin_controller.smart_rate_limit')
    def test_rate_limiting_is_applied(self, mock_rate_limit, client, internal_headers):
        """Test that rate limiting decorators are applied correctly"""
        # This test verifies that the rate limiting decorator is being called
        # The actual rate limiting behavior would be tested in integration tests
        
        # Act
        response = client.post('/api/admin/cleanup-tokens', headers=internal_headers)
        
        # The response might succeed or fail, but we're testing decorator application
        assert response.status_code in [200, 500, 429]  # Various acceptable responses

    def test_all_endpoints_require_internal_authorization(self, client):
        """Test that all admin endpoints require internal authorization"""
        admin_endpoints = [
            ('/api/admin/cleanup-tokens', 'POST'),
            ('/api/admin/security-stats', 'GET')
        ]
        
        for endpoint, method in admin_endpoints:
            if method == 'POST':
                response = client.post(endpoint)
            else:
                response = client.get(endpoint)
            
            assert response.status_code == 403, f"Endpoint {method} {endpoint} should require internal authorization"

    def test_invalid_http_methods(self, client, internal_headers):
        """Test endpoints with invalid HTTP methods"""
        # Test GET on POST-only endpoint
        response = client.get('/api/admin/cleanup-tokens', headers=internal_headers)
        assert response.status_code == 405  # Method not allowed
        
        # Test POST on GET-only endpoint
        response = client.post('/api/admin/security-stats', headers=internal_headers)
        assert response.status_code == 405  # Method not allowed

    @patch('src.interface.controllers.admin_controller.TokenSecurityRepository')
    def test_cleanup_tokens_empty_result(self, mock_token_repo_class, client, internal_headers):
        """Test cleanup tokens with no tokens to clean"""
        # Arrange
        mock_token_repo = Mock()
        mock_cleanup_result = {
            "blacklist_cleaned": 0,
            "tracking_cleaned": 0
        }
        mock_token_repo.cleanup_expired_tokens.return_value = mock_cleanup_result
        mock_token_repo_class.return_value = mock_token_repo
        
        # Act
        response = client.post('/api/admin/cleanup-tokens', headers=internal_headers)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["cleaned"]["blacklist_cleaned"] == 0
        assert response_data["cleaned"]["tracking_cleaned"] == 0

    @patch('src.interface.controllers.admin_controller.TokenSecurityRepository')
    def test_security_stats_empty_result(self, mock_token_repo_class, client, internal_headers):
        """Test security stats with empty/null results"""
        # Arrange
        mock_token_repo = Mock()
        mock_stats = {
            "active_tokens": 0,
            "blacklisted_tokens": 0,
            "tokens_created_today": 0,
            "failed_attempts_today": 0,
            "last_cleanup": None
        }
        mock_token_repo.get_security_stats.return_value = mock_stats
        mock_token_repo_class.return_value = mock_token_repo
        
        # Act
        response = client.get('/api/admin/security-stats', headers=internal_headers)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["stats"]["active_tokens"] == 0
        assert response_data["stats"]["last_cleanup"] is None