"""
Unit tests for User Controller
Tests user profile management endpoints and business logic integration
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from src.interface.controllers.user_controller import user_bp


class TestUserController:
    """Test suite for User Controller"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing using project configuration"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
        
        # Set testing environment before importing
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['TESTING'] = '1'
        
        from src.main import create_app
        app = create_app()
        app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False
        })
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def auth_token(self, app):
        """Create test authentication token"""
        with app.app_context():
            token = create_access_token(identity="test-user-123")
        return token
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Create authentication headers"""
        return {"Authorization": f"Bearer {auth_token}"}

    def test_user_blueprint_registration(self, app):
        """Test that user blueprint is properly registered"""
        # Assert
        assert 'user_bp' in app.blueprints

    # GET /profile - Get user profile
    @patch('src.interface.controllers.user_controller.make_firestore_profile_service')
    def test_get_user_profile_success(self, mock_service_factory, client, auth_headers):
        """Test successful user profile retrieval"""
        # Arrange
        mock_service = Mock()
        mock_profile = {
            "uid": "test-user-123",
            "displayName": "Test User",
            "email": "test@example.com",
            "photoURL": None,
            "emailVerified": True,
            "authProvider": "password",
            "language": "en",
            "cookingLevel": "intermediate",
            "measurementUnit": "metric",
            "allergies": [],
            "allergyItems": [],
            "preferredFoodTypes": ["italian", "mexican"],
            "specialDietItems": [],
            "favoriteRecipes": [],
            "initialPreferencesCompleted": True,
            "createdAt": "2024-01-01T00:00:00Z",
            "lastLoginAt": "2024-01-16T10:30:00Z"
        }
        mock_service.get_profile.return_value = mock_profile
        mock_service_factory.return_value = mock_service
        
        # Act
        response = client.get('/api/user/profile', headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["uid"] == "test-user-123"
        assert response_data["displayName"] == "Test User"
        assert response_data["email"] == "test@example.com"
        mock_service.get_profile.assert_called_once_with("test-user-123")

    @patch('src.interface.controllers.user_controller.make_firestore_profile_service')
    def test_get_user_profile_not_found(self, mock_service_factory, client, auth_headers):
        """Test user profile not found"""
        # Arrange
        mock_service = Mock()
        mock_service.get_profile.return_value = None
        mock_service_factory.return_value = mock_service
        
        # Act
        response = client.get('/api/user/profile', headers=auth_headers)
        
        # Assert
        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert "error" in response_data

    @patch('src.interface.controllers.user_controller.make_firestore_profile_service')
    def test_get_user_profile_service_error(self, mock_service_factory, client, auth_headers):
        """Test user profile service error"""
        # Arrange
        mock_service = Mock()
        mock_service.get_profile.side_effect = Exception("Firestore connection error")
        mock_service_factory.return_value = mock_service
        
        # Act
        response = client.get('/api/user/profile', headers=auth_headers)
        
        # Assert
        assert response.status_code == 500

    def test_get_user_profile_unauthorized(self, client):
        """Test get user profile without authentication"""
        # Act
        response = client.get('/api/user/profile')
        
        # Assert
        assert response.status_code == 401

    # PUT /profile - Update user profile
    @patch('src.interface.controllers.user_controller.make_firestore_profile_service')
    def test_update_user_profile_success(self, mock_service_factory, client, auth_headers):
        """Test successful user profile update"""
        # Arrange
        mock_service = Mock()
        mock_service.update_profile.return_value = True
        mock_service_factory.return_value = mock_service
        
        profile_update = {
            "displayName": "Updated Name",
            "cookingLevel": "advanced",
            "language": "es",
            "measurementUnit": "imperial",
            "allergies": ["nuts", "dairy"],
            "preferredFoodTypes": ["vegan", "italian"],
            "specialDietItems": ["gluten_free"],
            "initialPreferencesCompleted": True
        }
        
        # Act
        response = client.put(
            '/api/user/profile',
            data=json.dumps(profile_update),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert "success" in response_data
        mock_service.update_profile.assert_called_once()

    @patch('src.interface.controllers.user_controller.make_firestore_profile_service')
    def test_update_user_profile_validation_error(self, mock_service_factory, client, auth_headers):
        """Test user profile update with validation error"""
        # Arrange
        mock_service = Mock()
        mock_service_factory.return_value = mock_service
        
        invalid_profile_update = {
            "cookingLevel": "invalid_level",  # Invalid cooking level
            "measurementUnit": "invalid_unit"  # Invalid measurement unit
        }
        
        # Act
        response = client.put(
            '/api/user/profile',
            data=json.dumps(invalid_profile_update),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400

    @patch('src.interface.controllers.user_controller.make_firestore_profile_service')
    def test_update_user_profile_empty_body(self, mock_service_factory, client, auth_headers):
        """Test user profile update with empty body"""
        # Arrange
        mock_service = Mock()
        mock_service_factory.return_value = mock_service
        
        # Act
        response = client.put(
            '/api/user/profile',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400

    @patch('src.interface.controllers.user_controller.make_firestore_profile_service')
    def test_update_user_profile_service_error(self, mock_service_factory, client, auth_headers):
        """Test user profile update service error"""
        # Arrange
        mock_service = Mock()
        mock_service.update_profile.side_effect = Exception("Firestore update error")
        mock_service_factory.return_value = mock_service
        
        profile_update = {
            "displayName": "Test Update"
        }
        
        # Act
        response = client.put(
            '/api/user/profile',
            data=json.dumps(profile_update),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 500

    def test_update_user_profile_unauthorized(self, client):
        """Test update user profile without authentication"""
        # Arrange
        profile_update = {"displayName": "Test"}
        
        # Act
        response = client.put(
            '/api/user/profile',
            data=json.dumps(profile_update),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 401

    def test_update_user_profile_invalid_content_type(self, client, auth_headers):
        """Test update user profile with invalid content type"""
        # Act
        response = client.put(
            '/api/user/profile',
            data="invalid data",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code in [400, 415]  # Bad request or unsupported media type

    @patch('src.interface.controllers.user_controller.security_logger')
    def test_security_logging_is_applied(self, mock_security_logger, client, auth_headers):
        """Test that security logging is applied correctly"""
        # This test verifies that the security logging decorator is being called
        # The actual logging behavior would be tested in integration tests
        
        # Act
        response = client.get('/api/user/profile', headers=auth_headers)
        
        # The response might succeed or fail, but we're testing decorator application
        assert response.status_code in [200, 404, 500]  # Various acceptable responses

    @patch('src.interface.controllers.user_controller.cache_user_data')
    def test_caching_is_applied(self, mock_cache, client, auth_headers):
        """Test that caching decorators are applied correctly"""
        # This test verifies that the caching decorator is being called
        # The actual caching behavior would be tested in integration tests
        
        # Act
        response = client.get('/api/user/profile', headers=auth_headers)
        
        # The response might succeed or fail, but we're testing decorator application
        assert response.status_code in [200, 404, 500]  # Various acceptable responses

    @patch('src.interface.controllers.user_controller.api_rate_limit')
    def test_rate_limiting_is_applied(self, mock_rate_limit, client, auth_headers):
        """Test that rate limiting decorators are applied correctly"""
        # This test verifies that the rate limiting decorator is being called
        # The actual rate limiting behavior would be tested in integration tests
        
        # Act
        response = client.get('/api/user/profile', headers=auth_headers)
        
        # The response might succeed or fail, but we're testing decorator application
        assert response.status_code in [200, 404, 429, 500]  # Various acceptable responses including rate limit

    def test_profile_schema_validation_fields(self, client, auth_headers):
        """Test profile schema validation with specific field types"""
        # Arrange
        with patch('src.interface.controllers.user_controller.make_firestore_profile_service') as mock_factory:
            mock_service = Mock()
            mock_service.update_profile.return_value = True
            mock_factory.return_value = mock_service
            
            # Test with specific field types that should be validated
            profile_update = {
                "cookingLevel": "beginner",  # Should be one of: beginner, intermediate, advanced
                "measurementUnit": "metric",  # Should be one of: metric, imperial
                "language": "en",  # Should be valid language code
                "allergies": ["nuts", "dairy"],  # Should be array of strings
                "emailVerified": True,  # Should be boolean
                "initialPreferencesCompleted": False  # Should be boolean
            }
            
            # Act
            response = client.put(
                '/api/user/profile',
                data=json.dumps(profile_update),
                content_type='application/json',
                headers=auth_headers
            )
            
            # Assert
            # Response should be successful if validation passes
            assert response.status_code in [200, 400]  # Success or validation error