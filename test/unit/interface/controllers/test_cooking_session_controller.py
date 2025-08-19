"""
Unit tests for Cooking Session Controller
Tests cooking session endpoints and business logic integration
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from src.interface.controllers.cooking_session_controller import cooking_session_bp


class TestCookingSessionController:
    """Test suite for Cooking Session Controller"""
    
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

    def test_cooking_session_blueprint_registration(self, app):
        """Test that cooking session blueprint is properly registered"""
        # Assert
        assert 'cooking_session' in app.blueprints

    # GET /recipes/<recipe_uid>/mise_en_place - Get mise en place
    @patch('src.interface.controllers.cooking_session_controller.make_get_mise_en_place_use_case')
    def test_get_mise_en_place_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful retrieval of mise en place"""
        # Arrange
        mock_use_case = Mock()
        mock_mise_en_place = Mock()
        mock_mise_en_place.to_dict.return_value = {
            "recipe_uid": "recipe_123",
            "servings": 2,
            "tools": ["olla", "sartén"],
            "prep_tasks": [],
            "measured_ingredients": []
        }
        mock_use_case.execute.return_value = mock_mise_en_place
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get(
            '/api/cooking_session/recipes/recipe_123/mise_en_place?servings=2',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once_with(
            recipe_uid="recipe_123",
            servings=2,
            user_uid="test-user-123"
        )

    @patch('src.interface.controllers.cooking_session_controller.make_get_mise_en_place_use_case')
    def test_get_mise_en_place_default_servings(self, mock_use_case_factory, client, auth_headers):
        """Test mise en place with default servings"""
        # Arrange
        mock_use_case = Mock()
        mock_mise_en_place = Mock()
        mock_mise_en_place.to_dict.return_value = {"servings": 2}
        mock_use_case.execute.return_value = mock_mise_en_place
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get(
            '/api/cooking_session/recipes/recipe_123/mise_en_place',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once_with(
            recipe_uid="recipe_123",
            servings=2,  # Default value
            user_uid="test-user-123"
        )

    def test_get_mise_en_place_invalid_servings(self, client, auth_headers):
        """Test mise en place with invalid servings"""
        # Act
        response = client.get(
            '/api/cooking_session/recipes/recipe_123/mise_en_place?servings=0',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400

    def test_get_mise_en_place_unauthorized(self, client):
        """Test mise en place without authentication"""
        # Act
        response = client.get('/api/cooking_session/recipes/recipe_123/mise_en_place')
        
        # Assert
        assert response.status_code == 401

    # POST /cooking_session/start - Start cooking session
    @patch('src.interface.controllers.cooking_session_controller.make_start_cooking_session_use_case')
    def test_start_cooking_session_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful cooking session start"""
        # Arrange
        mock_use_case = Mock()
        mock_session = Mock()
        mock_session.session_id = "cook_123"
        mock_use_case.execute.return_value = mock_session
        mock_use_case_factory.return_value = mock_use_case
        
        session_data = {
            "recipe_uid": "recipe_123",
            "servings": 2,
            "level": "intermediate",
            "started_at": "2024-01-16T10:30:00Z"
        }
        
        # Act
        response = client.post(
            '/api/cooking_session/cooking_session/start',
            data=json.dumps(session_data),
            content_type='application/json',
            headers={**auth_headers, "Idempotency-Key": "idem_123"}
        )
        
        # Assert
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data["session_id"] == "cook_123"
        assert response_data["status"] == "running"

    def test_start_cooking_session_missing_idempotency_key(self, client, auth_headers):
        """Test start cooking session without idempotency key"""
        # Arrange
        session_data = {
            "recipe_uid": "recipe_123",
            "servings": 2,
            "level": "intermediate",
            "started_at": "2024-01-16T10:30:00Z"
        }
        
        # Act
        response = client.post(
            '/api/cooking_session/cooking_session/start',
            data=json.dumps(session_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400

    def test_start_cooking_session_missing_required_fields(self, client, auth_headers):
        """Test start cooking session with missing required fields"""
        # Arrange
        session_data = {
            "recipe_uid": "recipe_123"
            # Missing servings, level, started_at
        }
        
        # Act
        response = client.post(
            '/api/cooking_session/cooking_session/start',
            data=json.dumps(session_data),
            content_type='application/json',
            headers={**auth_headers, "Idempotency-Key": "idem_123"}
        )
        
        # Assert
        assert response.status_code == 400

    def test_start_cooking_session_invalid_datetime(self, client, auth_headers):
        """Test start cooking session with invalid datetime format"""
        # Arrange
        session_data = {
            "recipe_uid": "recipe_123",
            "servings": 2,
            "level": "intermediate",
            "started_at": "invalid-datetime"
        }
        
        # Act
        response = client.post(
            '/api/cooking_session/cooking_session/start',
            data=json.dumps(session_data),
            content_type='application/json',
            headers={**auth_headers, "Idempotency-Key": "idem_123"}
        )
        
        # Assert
        assert response.status_code == 400

    # POST /cooking_session/complete_step - Complete cooking step
    @patch('src.interface.controllers.cooking_session_controller.make_complete_step_use_case')
    def test_complete_cooking_step_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful cooking step completion"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "ok": True,
            "inventory_updates": [
                {"lot_id": "batch_777", "new_qty": 120}
            ]
        }
        mock_use_case_factory.return_value = mock_use_case
        
        step_data = {
            "session_id": "cook_123",
            "step_id": "step_1",
            "timer_ms": 300000,
            "consumptions": [
                {
                    "ingredient_uid": "ing_onion",
                    "lot_id": "batch_777",
                    "qty": 100,
                    "unit": "g"
                }
            ]
        }
        
        # Act
        response = client.post(
            '/api/cooking_session/cooking_session/complete_step',
            data=json.dumps(step_data),
            content_type='application/json',
            headers={**auth_headers, "Idempotency-Key": "idem_step_123"}
        )
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["ok"] is True

    def test_complete_cooking_step_missing_required_fields(self, client, auth_headers):
        """Test complete cooking step with missing required fields"""
        # Arrange
        step_data = {
            "session_id": "cook_123"
            # Missing step_id
        }
        
        # Act
        response = client.post(
            '/api/cooking_session/cooking_session/complete_step',
            data=json.dumps(step_data),
            content_type='application/json',
            headers={**auth_headers, "Idempotency-Key": "idem_step_123"}
        )
        
        # Assert
        assert response.status_code == 400

    # POST /cooking_session/finish - Finish cooking session
    @patch('src.interface.controllers.cooking_session_controller.make_finish_cooking_session_use_case')
    def test_finish_cooking_session_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful cooking session finish"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "ok": True,
            "environmental_saving": {
                "co2e_kg": 0.38,
                "water_l": 95,
                "waste_kg": 0.12
            },
            "leftover_suggestion": {
                "portions": 2,
                "eat_by": "2025-08-18"
            }
        }
        mock_use_case_factory.return_value = mock_use_case
        
        finish_data = {
            "session_id": "cook_123",
            "notes": "Delicious meal!",
            "photo_url": "https://example.com/photo.jpg"
        }
        
        # Act
        response = client.post(
            '/api/cooking_session/cooking_session/finish',
            data=json.dumps(finish_data),
            content_type='application/json',
            headers={**auth_headers, "Idempotency-Key": "idem_finish_123"}
        )
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["ok"] is True
        assert "environmental_saving" in response_data

    def test_finish_cooking_session_missing_session_id(self, client, auth_headers):
        """Test finish cooking session without session_id"""
        # Arrange
        finish_data = {
            "notes": "Great meal!"
        }
        
        # Act
        response = client.post(
            '/api/cooking_session/cooking_session/finish',
            data=json.dumps(finish_data),
            content_type='application/json',
            headers={**auth_headers, "Idempotency-Key": "idem_finish_123"}
        )
        
        # Assert
        assert response.status_code == 400

    def test_finish_cooking_session_empty_body(self, client, auth_headers):
        """Test finish cooking session with empty body"""
        # Act
        response = client.post(
            '/api/cooking_session/cooking_session/finish',
            headers={**auth_headers, "Idempotency-Key": "idem_finish_123"}
        )
        
        # Assert
        assert response.status_code == 400

    def test_cooking_session_unauthorized_access(self, client):
        """Test all endpoints require authentication"""
        # Test start session
        response = client.post('/api/cooking_session/cooking_session/start')
        assert response.status_code == 401
        
        # Test complete step
        response = client.post('/api/cooking_session/cooking_session/complete_step')
        assert response.status_code == 401
        
        # Test finish session
        response = client.post('/api/cooking_session/cooking_session/finish')
        assert response.status_code == 401

    @patch('src.interface.controllers.cooking_session_controller.IdempotencyService')
    def test_idempotency_check_returns_cached_response(self, mock_idempotency_service, client, auth_headers):
        """Test that idempotency check returns cached response"""
        # Arrange
        mock_service_instance = Mock()
        mock_service_instance.check_idempotency.return_value = (201, {"cached": True})
        mock_idempotency_service.return_value = mock_service_instance
        
        session_data = {
            "recipe_uid": "recipe_123",
            "servings": 2,
            "level": "intermediate",
            "started_at": "2024-01-16T10:30:00Z"
        }
        
        # Act
        response = client.post(
            '/api/cooking_session/cooking_session/start',
            data=json.dumps(session_data),
            content_type='application/json',
            headers={**auth_headers, "Idempotency-Key": "idem_123"}
        )
        
        # Assert
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data["cached"] is True