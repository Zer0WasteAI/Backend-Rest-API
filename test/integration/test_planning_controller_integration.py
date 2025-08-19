"""
Integration tests for Planning Controller
Tests end-to-end meal planning workflows and integrations
"""
import pytest
import json
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token


class TestPlanningControllerIntegration:
    """Integration test suite for Planning Controller"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for integration testing"""
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        
        # Register planning blueprint
        from src.interface.controllers.planning_controller import planning_bp
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

    # INTEGRATION TEST 1: Complete Meal Planning Workflow
    @patch('src.interface.controllers.planning_controller.make_save_meal_plan_use_case')
    @patch('src.interface.controllers.planning_controller.make_get_meal_plan_by_date_use_case')
    @patch('src.interface.controllers.planning_controller.make_update_meal_plan_use_case')
    def test_complete_meal_planning_workflow(
        self, 
        mock_update_use_case,
        mock_get_use_case,
        mock_save_use_case,
        client, 
        auth_headers
    ):
        """Test complete meal planning workflow: Save → Get → Update"""
        
        # Step 1: Save meal plan
        mock_save_use_case.return_value.execute.return_value = {
            "plan_id": "plan_integration_001",
            "date": "2025-08-20",
            "breakfast": {"recipe_name": "Oatmeal", "portions": 2},
            "lunch": {"recipe_name": "Salad", "portions": 2},
            "dinner": {"recipe_name": "Pasta", "portions": 2},
            "created_at": "2025-08-19T15:00:00Z"
        }
        
        meal_plan_data = {
            "date": "2025-08-20",
            "breakfast": {"recipe_name": "Oatmeal", "portions": 2},
            "lunch": {"recipe_name": "Salad", "portions": 2},
            "dinner": {"recipe_name": "Pasta", "portions": 2}
        }
        
        response = client.post("/api/planning/save", 
                              json=meal_plan_data, 
                              headers=auth_headers)
        
        assert response.status_code in [200, 201]
        save_data = response.get_json()
        assert "plan_id" in save_data
        plan_id = save_data["plan_id"]
        
        # Step 2: Get meal plan by date
        mock_get_use_case.return_value.execute.return_value = {
            "plan_id": plan_id,
            "date": "2025-08-20",
            "breakfast": {"recipe_name": "Oatmeal", "portions": 2},
            "lunch": {"recipe_name": "Salad", "portions": 2},
            "dinner": {"recipe_name": "Pasta", "portions": 2},
            "shopping_list": ["oats", "lettuce", "pasta"],
            "nutritional_summary": {"calories": 1500, "protein": 60}
        }
        
        response = client.get(f"/api/planning/get?date=2025-08-20", 
                             headers=auth_headers)
        
        assert response.status_code == 200
        get_data = response.get_json()
        assert get_data["date"] == "2025-08-20"
        assert "shopping_list" in get_data
        
        # Step 3: Update meal plan
        mock_update_use_case.return_value.execute.return_value = {
            "plan_id": plan_id,
            "date": "2025-08-20",
            "breakfast": {"recipe_name": "Smoothie Bowl", "portions": 2},  # Updated
            "lunch": {"recipe_name": "Salad", "portions": 2},
            "dinner": {"recipe_name": "Pasta", "portions": 2},
            "updated_at": "2025-08-19T16:00:00Z"
        }
        
        update_data = {
            "date": "2025-08-20",
            "breakfast": {"recipe_name": "Smoothie Bowl", "portions": 2}
        }
        
        response = client.put("/api/planning/update", 
                             json=update_data, 
                             headers=auth_headers)
        
        assert response.status_code == 200
        update_response_data = response.get_json()
        assert update_response_data["breakfast"]["recipe_name"] == "Smoothie Bowl"

    # INTEGRATION TEST 2: Meal Plan with Recipe Integration
    @patch('src.interface.controllers.planning_controller.make_save_meal_plan_use_case')
    @patch('src.interface.controllers.recipe_controller.make_get_all_recipes_use_case')
    def test_meal_plan_recipe_integration(
        self,
        mock_recipe_use_case, 
        mock_save_use_case,
        client, 
        auth_headers
    ):
        """Test meal planning with recipe controller integration"""
        
        # Mock available recipes
        mock_recipe_use_case.return_value.execute.return_value = {
            "recipes": [
                {"recipe_uid": "recipe_001", "title": "Chicken Stir Fry", "difficulty": "easy"},
                {"recipe_uid": "recipe_002", "title": "Vegetable Soup", "difficulty": "easy"},
                {"recipe_uid": "recipe_003", "title": "Pasta Primavera", "difficulty": "medium"}
            ]
        }
        
        # Mock meal plan save with recipe integration
        mock_save_use_case.return_value.execute.return_value = {
            "plan_id": "plan_recipe_integration",
            "date": "2025-08-21",
            "lunch": {
                "recipe_uid": "recipe_001",
                "recipe_name": "Chicken Stir Fry",
                "portions": 3,
                "ingredients_needed": ["chicken", "vegetables", "soy sauce"]
            },
            "dinner": {
                "recipe_uid": "recipe_003",
                "recipe_name": "Pasta Primavera",
                "portions": 3,
                "ingredients_needed": ["pasta", "mixed vegetables", "olive oil"]
            },
            "total_ingredients": ["chicken", "vegetables", "soy sauce", "pasta", "mixed vegetables", "olive oil"]
        }
        
        meal_plan_with_recipes = {
            "date": "2025-08-21",
            "lunch": {"recipe_uid": "recipe_001", "portions": 3},
            "dinner": {"recipe_uid": "recipe_003", "portions": 3}
        }
        
        response = client.post("/api/planning/save",
                              json=meal_plan_with_recipes,
                              headers=auth_headers)
        
        assert response.status_code in [200, 201]
        data = response.get_json()
        assert "total_ingredients" in data
        assert len(data["total_ingredients"]) == 6

    # INTEGRATION TEST 3: Get All Meal Plans with Pagination
    @patch('src.interface.controllers.planning_controller.make_get_all_meal_plans_use_case')
    def test_get_all_meal_plans_pagination(
        self,
        mock_get_all_use_case,
        client,
        auth_headers
    ):
        """Test getting all meal plans with pagination"""
        
        mock_get_all_use_case.return_value.execute.return_value = {
            "meal_plans": [
                {
                    "plan_id": f"plan_{i}",
                    "date": f"2025-08-{20+i}",
                    "meals_count": 3,
                    "status": "active" if i < 3 else "completed"
                }
                for i in range(10)
            ],
            "pagination": {
                "current_page": 1,
                "total_pages": 2,
                "total_plans": 15,
                "per_page": 10
            },
            "summary": {
                "active_plans": 3,
                "completed_plans": 7,
                "total_planned_meals": 30
            }
        }
        
        response = client.get("/api/planning/all?page=1&limit=10",
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert "meal_plans" in data
        assert "pagination" in data
        assert len(data["meal_plans"]) == 10
        assert data["pagination"]["total_pages"] == 2

    # INTEGRATION TEST 4: Meal Plan Dates Calendar View
    @patch('src.interface.controllers.planning_controller.make_get_meal_plan_dates_use_case')
    def test_meal_plan_dates_calendar(
        self,
        mock_dates_use_case,
        client,
        auth_headers
    ):
        """Test meal plan dates for calendar integration"""
        
        mock_dates_use_case.return_value.execute.return_value = {
            "planned_dates": [
                {
                    "date": "2025-08-20",
                    "meals_count": 3,
                    "status": "complete",
                    "has_breakfast": True,
                    "has_lunch": True,
                    "has_dinner": True
                },
                {
                    "date": "2025-08-21",
                    "meals_count": 2,
                    "status": "partial",
                    "has_breakfast": False,
                    "has_lunch": True,
                    "has_dinner": True
                },
                {
                    "date": "2025-08-22",
                    "meals_count": 1,
                    "status": "minimal",
                    "has_breakfast": False,
                    "has_lunch": False,
                    "has_dinner": True
                }
            ],
            "date_range": {
                "start_date": "2025-08-20",
                "end_date": "2025-08-22"
            },
            "calendar_summary": {
                "total_planned_days": 3,
                "complete_days": 1,
                "partial_days": 1,
                "minimal_days": 1
            }
        }
        
        response = client.get("/api/planning/dates?start=2025-08-20&end=2025-08-22",
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert "planned_dates" in data
        assert "calendar_summary" in data
        assert len(data["planned_dates"]) == 3
        assert data["calendar_summary"]["complete_days"] == 1

    # INTEGRATION TEST 5: Delete Meal Plan with Cleanup
    @patch('src.interface.controllers.planning_controller.make_delete_meal_plan_use_case')
    def test_delete_meal_plan_cleanup(
        self,
        mock_delete_use_case,
        client,
        auth_headers
    ):
        """Test meal plan deletion with proper cleanup"""
        
        mock_delete_use_case.return_value.execute.return_value = {
            "deleted_plan_id": "plan_to_delete",
            "date": "2025-08-25",
            "deleted_at": "2025-08-19T17:00:00Z",
            "cleanup_summary": {
                "meals_removed": 3,
                "shopping_list_cleared": True,
                "notifications_cancelled": 2,
                "related_data_cleaned": True
            },
            "message": "Meal plan successfully deleted"
        }
        
        delete_data = {
            "date": "2025-08-25",
            "confirm_deletion": True
        }
        
        response = client.delete("/api/planning/delete",
                                json=delete_data,
                                headers=auth_headers)
        
        assert response.status_code in [200, 204]
        if response.status_code == 200:
            data = response.get_json()
            assert "cleanup_summary" in data
            assert data["cleanup_summary"]["meals_removed"] == 3

    # INTEGRATION TEST 6: Update Meal Plan Images
    @patch('src.interface.controllers.planning_controller.make_update_meal_plan_images_use_case')
    def test_update_meal_plan_images(
        self,
        mock_update_images_use_case,
        client,
        auth_headers
    ):
        """Test updating meal plan images"""
        
        mock_update_images_use_case.return_value.execute.return_value = {
            "plan_id": "plan_with_images",
            "date": "2025-08-23",
            "updated_images": {
                "breakfast_image": "https://storage.googleapis.com/breakfast_001.jpg",
                "lunch_image": "https://storage.googleapis.com/lunch_001.jpg",
                "dinner_image": "https://storage.googleapis.com/dinner_001.jpg"
            },
            "images_updated": 3,
            "updated_at": "2025-08-19T17:30:00Z"
        }
        
        images_data = {
            "date": "2025-08-23",
            "images": {
                "breakfast_image": "https://storage.googleapis.com/breakfast_001.jpg",
                "lunch_image": "https://storage.googleapis.com/lunch_001.jpg",
                "dinner_image": "https://storage.googleapis.com/dinner_001.jpg"
            }
        }
        
        response = client.put("/api/planning/images/update",
                             json=images_data,
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert "updated_images" in data
        assert data["images_updated"] == 3

    # INTEGRATION TEST 7: Authentication and Authorization
    def test_planning_endpoints_require_authentication(self, client):
        """Test that all planning endpoints require authentication"""
        
        endpoints_to_test = [
            ("POST", "/api/planning/save", {"date": "2025-08-20"}),
            ("GET", "/api/planning/get?date=2025-08-20", None),
            ("PUT", "/api/planning/update", {"date": "2025-08-20"}),
            ("DELETE", "/api/planning/delete", {"date": "2025-08-20"}),
            ("GET", "/api/planning/all", None),
            ("GET", "/api/planning/dates", None),
            ("PUT", "/api/planning/images/update", {"date": "2025-08-20"})
        ]
        
        for method, endpoint, data in endpoints_to_test:
            if method == "POST":
                response = client.post(endpoint, json=data)
            elif method == "GET":
                response = client.get(endpoint)
            elif method == "PUT":
                response = client.put(endpoint, json=data)
            elif method == "DELETE":
                response = client.delete(endpoint, json=data)
                
            assert response.status_code == 401, f"Endpoint {method} {endpoint} should require authentication"

    # INTEGRATION TEST 8: Error Handling Integration
    @patch('src.interface.controllers.planning_controller.make_save_meal_plan_use_case')
    def test_planning_error_handling_integration(
        self,
        mock_save_use_case,
        client,
        auth_headers
    ):
        """Test error handling across planning endpoints"""
        
        # Test validation error
        mock_save_use_case.return_value.execute.side_effect = ValueError("Invalid meal plan data")
        
        invalid_data = {
            "date": "invalid-date",
            "breakfast": {}  # Empty meal data
        }
        
        response = client.post("/api/planning/save",
                              json=invalid_data,
                              headers=auth_headers)
        
        assert response.status_code in [400, 422, 500]
        
        # Test successful recovery
        mock_save_use_case.return_value.execute.side_effect = None
        mock_save_use_case.return_value.execute.return_value = {
            "plan_id": "recovered_plan",
            "date": "2025-08-20",
            "status": "saved"
        }
        
        valid_data = {
            "date": "2025-08-20",
            "breakfast": {"recipe_name": "Toast", "portions": 1}
        }
        
        response = client.post("/api/planning/save",
                              json=valid_data,
                              headers=auth_headers)
        
        assert response.status_code in [200, 201]
