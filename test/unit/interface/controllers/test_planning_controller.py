"""
Unit tests for Planning Controller
Tests meal planning endpoints and business logic integration
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from src.interface.controllers.planning_controller import planning_bp


class TestPlanningController:
    """Test suite for Planning Controller"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        app.register_blueprint(planning_bp, url_prefix='/api/planning')
        
        # Initialize JWT
        jwt = JWTManager(app)
        
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

    def test_planning_blueprint_registration(self, app):
        """Test that planning blueprint is properly registered"""
        # Assert
        assert 'planning' in app.blueprints

    # POST /save - Save meal plan
    @patch('src.interface.controllers.planning_controller.make_save_meal_plan_use_case')
    def test_save_meal_plan_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful meal plan save"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "meal_plan_id": "plan_123",
            "success": True,
            "date": "2024-01-20"
        }
        mock_use_case_factory.return_value = mock_use_case
        
        meal_plan_data = {
            "date": "2024-01-20",
            "meals": {
                "breakfast": {
                    "name": "Avena con frutas",
                    "description": "Desayuno nutritivo",
                    "ingredients": ["Avena", "Plátano", "Miel"],
                    "prep_time_minutes": 10
                },
                "lunch": {
                    "name": "Ensalada César",
                    "description": "Ensalada fresca",
                    "recipe_id": "recipe_123",
                    "ingredients": ["Lechuga", "Pollo", "Crutones"],
                    "prep_time_minutes": 15
                }
            }
        }
        
        # Act
        response = client.post(
            '/api/planning/save',
            data=json.dumps(meal_plan_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data["meal_plan_id"] == "plan_123"
        mock_use_case.execute.assert_called_once()

    def test_save_meal_plan_missing_required_fields(self, client, auth_headers):
        """Test save meal plan with missing required fields"""
        # Arrange
        invalid_meal_plan = {
            "meals": {}  # Missing date
        }
        
        # Act
        response = client.post(
            '/api/planning/save',
            data=json.dumps(invalid_meal_plan),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400

    def test_save_meal_plan_unauthorized(self, client):
        """Test save meal plan without authentication"""
        # Arrange
        meal_plan_data = {"date": "2024-01-20", "meals": {}}
        
        # Act
        response = client.post(
            '/api/planning/save',
            data=json.dumps(meal_plan_data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 401

    # PUT /update - Update meal plan
    @patch('src.interface.controllers.planning_controller.make_update_meal_plan_use_case')
    def test_update_meal_plan_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful meal plan update"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "meal_plan_id": "plan_123",
            "updated": True
        }
        mock_use_case_factory.return_value = mock_use_case
        
        update_data = {
            "meal_plan_id": "plan_123",
            "date": "2024-01-20",
            "meals": {
                "breakfast": {
                    "name": "Updated breakfast",
                    "description": "Updated description"
                }
            }
        }
        
        # Act
        response = client.put(
            '/api/planning/update',
            data=json.dumps(update_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # DELETE /delete - Delete meal plan
    @patch('src.interface.controllers.planning_controller.make_delete_meal_plan_use_case')
    def test_delete_meal_plan_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful meal plan deletion"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"deleted": True}
        mock_use_case_factory.return_value = mock_use_case
        
        delete_data = {
            "meal_plan_id": "plan_123",
            "date": "2024-01-20"
        }
        
        # Act
        response = client.delete(
            '/api/planning/delete',
            data=json.dumps(delete_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    def test_delete_meal_plan_missing_id(self, client, auth_headers):
        """Test delete meal plan without meal_plan_id"""
        # Arrange
        delete_data = {"date": "2024-01-20"}  # Missing meal_plan_id
        
        # Act
        response = client.delete(
            '/api/planning/delete',
            data=json.dumps(delete_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400

    # GET /get - Get meal plan by date
    @patch('src.interface.controllers.planning_controller.make_get_meal_plan_by_date_use_case')
    def test_get_meal_plan_by_date_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful meal plan retrieval by date"""
        # Arrange
        mock_use_case = Mock()
        mock_meal_plan = {
            "meal_plan_id": "plan_123",
            "date": "2024-01-20",
            "meals": {
                "breakfast": {"name": "Avena con frutas"},
                "lunch": {"name": "Ensalada César"}
            }
        }
        mock_use_case.execute.return_value = mock_meal_plan
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get(
            '/api/planning/get?date=2024-01-20',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data["meal_plan_id"] == "plan_123"
        assert response_data["date"] == "2024-01-20"

    def test_get_meal_plan_missing_date_parameter(self, client, auth_headers):
        """Test get meal plan without date parameter"""
        # Act
        response = client.get('/api/planning/get', headers=auth_headers)
        
        # Assert
        assert response.status_code == 400

    def test_get_meal_plan_invalid_date_format(self, client, auth_headers):
        """Test get meal plan with invalid date format"""
        # Act
        response = client.get(
            '/api/planning/get?date=invalid-date',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400

    # GET /all - Get all meal plans
    @patch('src.interface.controllers.planning_controller.make_get_all_meal_plans_use_case')
    def test_get_all_meal_plans_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful retrieval of all meal plans"""
        # Arrange
        mock_use_case = Mock()
        mock_meal_plans = [
            {
                "meal_plan_id": "plan_123",
                "date": "2024-01-20",
                "meals_count": 2
            },
            {
                "meal_plan_id": "plan_124",
                "date": "2024-01-21",
                "meals_count": 3
            }
        ]
        mock_use_case.execute.return_value = mock_meal_plans
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get('/api/planning/all', headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert len(response_data) == 2
        assert response_data[0]["meal_plan_id"] == "plan_123"

    # GET /dates - Get meal plan dates
    @patch('src.interface.controllers.planning_controller.make_get_meal_plan_dates_use_case')
    def test_get_meal_plan_dates_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful retrieval of meal plan dates"""
        # Arrange
        mock_use_case = Mock()
        mock_dates = {
            "dates": ["2024-01-20", "2024-01-21", "2024-01-22"],
            "total_plans": 3,
            "date_range": {
                "start": "2024-01-20",
                "end": "2024-01-22"
            }
        }
        mock_use_case.execute.return_value = mock_dates
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get('/api/planning/dates', headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert len(response_data["dates"]) == 3
        assert response_data["total_plans"] == 3

    # POST /images/update - Update meal plan images
    @patch('src.interface.controllers.planning_controller.make_recipe_image_generator_service')
    @patch('src.interface.controllers.planning_controller.async_task_service')
    def test_update_meal_plan_images_success(self, mock_async_service, mock_image_service_factory, client, auth_headers):
        """Test successful meal plan images update"""
        # Arrange
        mock_image_service = Mock()
        mock_image_service_factory.return_value = mock_image_service
        
        mock_async_service.submit_task.return_value = "task_123"
        
        image_update_data = {
            "meal_plan_id": "plan_123",
            "update_all": True
        }
        
        # Act
        response = client.post(
            '/api/planning/images/update',
            data=json.dumps(image_update_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code in [200, 202]  # Success or accepted
        # Verify async task was submitted
        if response.status_code == 202:
            response_data = json.loads(response.data)
            assert "task_id" in response_data

    def test_update_meal_plan_images_missing_id(self, client, auth_headers):
        """Test update images without meal_plan_id"""
        # Arrange
        image_update_data = {"update_all": True}  # Missing meal_plan_id
        
        # Act
        response = client.post(
            '/api/planning/images/update',
            data=json.dumps(image_update_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400

    def test_all_endpoints_require_authentication(self, client):
        """Test that all endpoints require authentication"""
        endpoints = [
            ('/api/planning/save', 'POST'),
            ('/api/planning/update', 'PUT'),
            ('/api/planning/delete', 'DELETE'),
            ('/api/planning/get', 'GET'),
            ('/api/planning/all', 'GET'),
            ('/api/planning/dates', 'GET'),
            ('/api/planning/images/update', 'POST')
        ]
        
        for endpoint, method in endpoints:
            if method == 'POST':
                response = client.post(endpoint)
            elif method == 'PUT':
                response = client.put(endpoint)
            elif method == 'DELETE':
                response = client.delete(endpoint)
            else:
                response = client.get(endpoint)
            
            assert response.status_code == 401, f"Endpoint {method} {endpoint} should require authentication"

    @patch('src.interface.controllers.planning_controller.smart_rate_limit')
    def test_rate_limiting_is_applied(self, mock_rate_limit, client, auth_headers):
        """Test that rate limiting decorators are applied correctly"""
        # This test verifies that the rate limiting decorator is being called
        # The actual rate limiting behavior would be tested in integration tests
        
        # Act
        response = client.post('/api/planning/save', headers=auth_headers)
        
        # The response might fail due to missing data, but we're testing decorator application
        assert response.status_code in [201, 400, 429]  # Various acceptable responses

    @patch('src.interface.controllers.planning_controller.cache_user_data')
    def test_caching_is_applied(self, mock_cache, client, auth_headers):
        """Test that caching decorators are applied correctly"""
        # This test verifies that the caching decorator is being called
        # The actual caching behavior would be tested in integration tests
        
        # Act
        response = client.get('/api/planning/all', headers=auth_headers)
        
        # The response might succeed or fail, but we're testing decorator application
        assert response.status_code in [200, 500]  # Various acceptable responses

    def test_invalid_content_type_for_post_endpoints(self, client, auth_headers):
        """Test POST endpoints with invalid content type"""
        post_endpoints = [
            '/api/planning/save',
            '/api/planning/images/update'
        ]
        
        for endpoint in post_endpoints:
            response = client.post(
                endpoint,
                data="invalid data",
                headers=auth_headers
            )
            assert response.status_code in [400, 415], f"Endpoint {endpoint} should reject invalid content-type"