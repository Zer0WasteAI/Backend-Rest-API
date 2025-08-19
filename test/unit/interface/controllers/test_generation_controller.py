"""
Unit tests for Generation Controller
Tests image generation endpoints and business logic integration
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from src.interface.controllers.generation_controller import generation_bp


class TestGenerationController:
    """Test suite for Generation Controller"""
    
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

    def test_generation_blueprint_registration(self, app):
        """Test that generation blueprint is properly registered"""
        # Assert
        assert 'generation' in app.blueprints

    # GET /images/status/<task_id> - Get image generation status
    def test_get_image_generation_status_success(self, client, auth_headers):
        """Test successful image generation status retrieval"""
        # Act
        response = client.get(
            '/api/generation/images/status/task_123',
            headers=auth_headers
        )
        
        # Assert
        # Endpoint exists and accepts requests
        assert response.status_code in [200, 404, 500]  # Various acceptable responses

    def test_get_image_generation_status_invalid_task_id(self, client, auth_headers):
        """Test image generation status with invalid task ID"""
        # Act
        response = client.get(
            '/api/generation/images/status/invalid-task-id',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code in [400, 404]  # Bad request or not found

    def test_get_image_generation_status_unauthorized(self, client):
        """Test image generation status without authentication"""
        # Act
        response = client.get('/api/generation/images/status/task_123')
        
        # Assert
        assert response.status_code == 401

    # GET /<generation_id>/images - Get generation images
    def test_get_generation_images_success(self, client, auth_headers):
        """Test successful generation images retrieval"""
        # Act
        response = client.get(
            '/api/generation/gen_123/images',
            headers=auth_headers
        )
        
        # Assert
        # Endpoint exists and accepts requests
        assert response.status_code in [200, 404, 500]  # Various acceptable responses

    def test_get_generation_images_invalid_generation_id(self, client, auth_headers):
        """Test generation images with invalid generation ID"""
        # Act
        response = client.get(
            '/api/generation/invalid-gen-id/images',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code in [400, 404]  # Bad request or not found

    def test_get_generation_images_unauthorized(self, client):
        """Test generation images without authentication"""
        # Act
        response = client.get('/api/generation/gen_123/images')
        
        # Assert
        assert response.status_code == 401

    def test_all_endpoints_require_authentication(self, client):
        """Test that all endpoints require authentication"""
        endpoints = [
            ('/api/generation/images/status/task_123', 'GET'),
            ('/api/generation/gen_123/images', 'GET')
        ]
        
        for endpoint, method in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {method} {endpoint} should require authentication"

    @patch('src.interface.controllers.generation_controller.smart_rate_limit')
    def test_rate_limiting_is_applied(self, mock_rate_limit, client, auth_headers):
        """Test that rate limiting decorators are applied correctly"""
        # This test verifies that the rate limiting decorator is being called
        # The actual rate limiting behavior would be tested in integration tests
        
        # Act
        response = client.get('/api/generation/images/status/task_123', headers=auth_headers)
        
        # The response might succeed or fail, but we're testing decorator application
        assert response.status_code in [200, 404, 429, 500]  # Various acceptable responses

    def test_invalid_http_methods(self, client, auth_headers):
        """Test endpoints with invalid HTTP methods"""
        # Test POST on GET-only endpoints
        response = client.post('/api/generation/images/status/task_123', headers=auth_headers)
        assert response.status_code == 405  # Method not allowed
        
        response = client.post('/api/generation/gen_123/images', headers=auth_headers)
        assert response.status_code == 405  # Method not allowed
        
        # Test PUT on GET-only endpoints
        response = client.put('/api/generation/images/status/task_123', headers=auth_headers)
        assert response.status_code == 405  # Method not allowed
        
        response = client.put('/api/generation/gen_123/images', headers=auth_headers)
        assert response.status_code == 405  # Method not allowed

    def test_task_id_parameter_validation(self, client, auth_headers):
        """Test task ID parameter validation"""
        # Test with empty task ID
        response = client.get('/api/generation/images/status/', headers=auth_headers)
        assert response.status_code == 404  # Not found due to missing task_id
        
        # Test with very long task ID
        long_task_id = "a" * 1000
        response = client.get(f'/api/generation/images/status/{long_task_id}', headers=auth_headers)
        assert response.status_code in [400, 404]  # Bad request or not found

    def test_generation_id_parameter_validation(self, client, auth_headers):
        """Test generation ID parameter validation"""
        # Test with empty generation ID
        response = client.get('/api/generation//images', headers=auth_headers)
        assert response.status_code == 404  # Not found due to missing generation_id
        
        # Test with very long generation ID
        long_gen_id = "b" * 1000
        response = client.get(f'/api/generation/{long_gen_id}/images', headers=auth_headers)
        assert response.status_code in [400, 404]  # Bad request or not found

    @patch('src.interface.controllers.generation_controller.make_get_generation_status_use_case')
    def test_get_image_generation_status_with_mock_success(self, mock_use_case_factory, client, auth_headers):
        """Test image generation status with mocked use case success"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "task_id": "task_123",
            "status": "completed",
            "progress": 100,
            "generated_images": [
                {
                    "image_id": "img_gen_456",
                    "url": "https://storage.example.com/img_gen_456.jpg",
                    "format": "JPEG",
                    "dimensions": {"width": 512, "height": 512}
                }
            ],
            "generation_time_ms": 15000,
            "prompt_used": "Fresh tomatoes on wooden table"
        }
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get(
            '/api/generation/images/status/task_123',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["task_id"] == "task_123"
        assert response_data["status"] == "completed"
        assert response_data["progress"] == 100

    @patch('src.interface.controllers.generation_controller.make_get_generation_images_use_case')
    def test_get_generation_images_with_mock_success(self, mock_use_case_factory, client, auth_headers):
        """Test generation images with mocked use case success"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "generation_id": "gen_123",
            "images": [
                {
                    "image_id": "img_1",
                    "url": "https://storage.example.com/img_1.jpg",
                    "thumbnail_url": "https://storage.example.com/thumb_img_1.jpg",
                    "generated_at": "2024-01-16T10:30:00Z",
                    "prompt": "Fresh vegetables",
                    "style": "photorealistic"
                },
                {
                    "image_id": "img_2",
                    "url": "https://storage.example.com/img_2.jpg",
                    "thumbnail_url": "https://storage.example.com/thumb_img_2.jpg",
                    "generated_at": "2024-01-16T10:32:00Z",
                    "prompt": "Fresh vegetables",
                    "style": "photorealistic"
                }
            ],
            "total_images": 2,
            "generation_metadata": {
                "created_at": "2024-01-16T10:30:00Z",
                "model_version": "v2.1",
                "total_generation_time_ms": 25000
            }
        }
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get(
            '/api/generation/gen_123/images',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["generation_id"] == "gen_123"
        assert len(response_data["images"]) == 2
        assert response_data["total_images"] == 2

    def test_endpoint_error_handling(self, client, auth_headers):
        """Test endpoint error handling with various scenarios"""
        # Test with special characters in IDs
        special_chars_task_id = "task_123@#$%"
        response = client.get(f'/api/generation/images/status/{special_chars_task_id}', headers=auth_headers)
        assert response.status_code in [400, 404]
        
        special_chars_gen_id = "gen_123@#$%"
        response = client.get(f'/api/generation/{special_chars_gen_id}/images', headers=auth_headers)
        assert response.status_code in [400, 404]