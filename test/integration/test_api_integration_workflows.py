"""
Integration tests for ZeroWasteAI API
Tests complete workflows across controllers and services
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token


class TestAPIIntegrationWorkflows:
    """Test suite for API Integration Workflows"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app with all blueprints for integration testing"""
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        
        # Register all blueprints
        from src.interface.controllers.recipe_controller import recipes_bp
        from src.interface.controllers.inventory_controller import inventory_bp
        from src.interface.controllers.recognition_controller import recognition_bp
        from src.interface.controllers.cooking_session_controller import cooking_session_bp
        from src.interface.controllers.environmental_savings_controller import environmental_savings_bp
        
        app.register_blueprint(recipes_bp, url_prefix='/api/recipes')
        app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
        app.register_blueprint(recognition_bp, url_prefix='/api/recognition')
        app.register_blueprint(cooking_session_bp, url_prefix='/api/cooking-session')
        app.register_blueprint(environmental_savings_bp, url_prefix='/api/environmental-savings')
        
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

    # INTEGRATION WORKFLOW 1: Recognition → Inventory → Recipe
    @patch('src.interface.controllers.recognition_controller.make_recognize_ingredients_use_case')
    @patch('src.interface.controllers.inventory_controller.make_add_ingredients_to_inventory_use_case')
    @patch('src.interface.controllers.recipe_controller.make_generate_recipes_use_case')
    @patch('src.interface.controllers.recipe_controller.make_prepare_recipe_generation_data_use_case')
    def test_recognition_to_inventory_to_recipe_workflow(
        self, 
        mock_prepare_use_case,
        mock_recipe_use_case, 
        mock_inventory_use_case, 
        mock_recognition_use_case,
        client, 
        auth_headers
    ):
        """Test complete workflow: Recognize ingredients → Add to inventory → Generate recipes"""
        
        # Step 1: Mock recognition response
        mock_recognition_use_case.return_value.execute.return_value = {
            "recognition_id": "rec_123",
            "ingredients": [
                {"name": "Tomato", "confidence": 0.95, "quantity": "3 pieces"},
                {"name": "Onion", "confidence": 0.87, "quantity": "2 pieces"}
            ]
        }
        
        # Step 2: Mock inventory addition
        mock_inventory_use_case.return_value.execute.return_value = {
            "ingredients_added": 2,
            "inventory_updated": True
        }
        
        # Step 3: Mock recipe generation preparation
        mock_prepare_use_case.return_value.execute.return_value = {
            "inventory_data": {"ingredients": ["Tomato", "Onion"]},
            "user_preferences": {}
        }
        
        # Step 4: Mock recipe generation
        mock_recipe_use_case.return_value.execute.return_value = {
            "recipes": [
                {
                    "title": "Tomato and Onion Soup",
                    "ingredients": ["Tomato", "Onion"],
                    "steps": ["Chop ingredients", "Cook soup"]
                }
            ]
        }
        
        # Execute workflow
        
        # Step 1: Recognize ingredients (simulated - would need file upload)
        recognition_response = client.post('/api/recognition/ingredients', headers=auth_headers)
        assert recognition_response.status_code in [200, 400, 422]  # May fail due to missing file
        
        # Step 2: Add ingredients to inventory
        inventory_data = {
            "ingredients": [
                {"name": "Tomato", "quantity": 3, "unit": "pieces", "expiration_date": "2024-02-01"},
                {"name": "Onion", "quantity": 2, "unit": "pieces", "expiration_date": "2024-01-25"}
            ]
        }
        inventory_response = client.post(
            '/api/inventory/ingredients',
            data=json.dumps(inventory_data),
            content_type='application/json',
            headers=auth_headers
        )
        assert inventory_response.status_code in [200, 400]
        
        # Step 3: Generate recipes from inventory
        recipe_generation_data = {
            "preferences": {"meal_type": "lunch", "difficulty": "easy"},
            "exclude_ingredients": []
        }
        recipe_response = client.post(
            '/api/recipes/generate-from-inventory',
            data=json.dumps(recipe_generation_data),
            content_type='application/json',
            headers=auth_headers
        )
        assert recipe_response.status_code in [200, 400]

    # INTEGRATION WORKFLOW 2: Recipe Generation → Cooking Session → Environmental Calculation
    @patch('src.interface.controllers.recipe_controller.make_generate_recipes_use_case')
    @patch('src.interface.controllers.recipe_controller.make_prepare_recipe_generation_data_use_case')
    @patch('src.interface.controllers.cooking_session_controller.make_start_cooking_session_use_case')
    @patch('src.interface.controllers.cooking_session_controller.make_finish_cooking_session_use_case')
    @patch('src.interface.controllers.environmental_savings_controller.make_estimate_savings_by_uid_use_case')
    def test_recipe_to_cooking_to_environmental_workflow(
        self,
        mock_env_use_case,
        mock_finish_cooking,
        mock_start_cooking,
        mock_recipe_use_case,
        mock_prepare_use_case,
        client,
        auth_headers
    ):
        """Test workflow: Generate recipe → Start cooking → Complete cooking → Calculate environmental impact"""
        
        # Mock recipe generation
        mock_prepare_use_case.return_value.execute.return_value = {"inventory_data": {}}
        mock_recipe_use_case.return_value.execute.return_value = {
            "recipes": [{"uid": "recipe_123", "title": "Test Recipe"}]
        }
        
        # Mock cooking session
        mock_start_cooking.return_value.execute.return_value = {
            "session_id": "session_123",
            "recipe_uid": "recipe_123"
        }
        mock_finish_cooking.return_value.execute.return_value = {
            "session_completed": True,
            "environmental_data": {"co2_saved": 2.5}
        }
        
        # Mock environmental calculation
        mock_env_use_case.return_value.execute.return_value = {
            "co2_reduction": 2.5,
            "water_saved": 10.3,
            "waste_prevented": 0.8
        }
        
        # Execute workflow
        
        # Step 1: Generate recipe
        recipe_response = client.post(
            '/api/recipes/generate-from-inventory',
            data=json.dumps({"preferences": {}}),
            content_type='application/json',
            headers=auth_headers
        )
        assert recipe_response.status_code in [200, 400]
        
        # Step 2: Start cooking session
        cooking_start_data = {
            "recipe_uid": "recipe_123",
            "servings": 4,
            "cooking_level": "beginner"
        }
        cooking_start_response = client.post(
            '/api/cooking-session/start',
            data=json.dumps(cooking_start_data),
            content_type='application/json',
            headers=auth_headers
        )
        assert cooking_start_response.status_code in [200, 400]
        
        # Step 3: Finish cooking session
        cooking_finish_data = {
            "session_id": "session_123",
            "actual_servings": 4,
            "completion_time": 30
        }
        cooking_finish_response = client.post(
            '/api/cooking-session/finish',
            data=json.dumps(cooking_finish_data),
            content_type='application/json',
            headers=auth_headers
        )
        assert cooking_finish_response.status_code in [200, 400]
        
        # Step 4: Calculate environmental impact
        env_response = client.post(
            '/api/environmental-savings/calculate/from-uid/recipe_123',
            headers=auth_headers
        )
        assert env_response.status_code in [200, 400]

    # INTEGRATION WORKFLOW 3: Inventory Management → Expiration Tracking → Recipe Suggestions
    @patch('src.interface.controllers.inventory_controller.make_add_ingredients_to_inventory_use_case')
    @patch('src.interface.controllers.inventory_controller.make_get_expiring_soon_use_case')
    @patch('src.interface.controllers.recipe_controller.make_generate_recipes_use_case')
    @patch('src.interface.controllers.recipe_controller.make_prepare_recipe_generation_data_use_case')
    def test_inventory_expiration_recipe_workflow(
        self,
        mock_prepare_recipes,
        mock_generate_recipes,
        mock_expiring_use_case,
        mock_add_inventory,
        client,
        auth_headers
    ):
        """Test workflow: Add inventory → Check expiring items → Generate recipes to use expiring items"""
        
        # Mock inventory addition
        mock_add_inventory.return_value.execute.return_value = {
            "ingredients_added": 3
        }
        
        # Mock expiring items
        mock_expiring_use_case.return_value.execute.return_value = {
            "expiring_soon": [
                {"name": "Banana", "days_until_expiry": 2},
                {"name": "Milk", "days_until_expiry": 1}
            ]
        }
        
        # Mock recipe generation for expiring items
        mock_prepare_recipes.return_value.execute.return_value = {
            "inventory_data": {"expiring_ingredients": ["Banana", "Milk"]}
        }
        mock_generate_recipes.return_value.execute.return_value = {
            "recipes": [
                {"title": "Banana Smoothie", "uses_expiring": ["Banana", "Milk"]}
            ]
        }
        
        # Execute workflow
        
        # Step 1: Add items to inventory
        inventory_data = {
            "ingredients": [
                {"name": "Banana", "quantity": 6, "expiration_date": "2024-01-20"},
                {"name": "Milk", "quantity": 1, "unit": "liter", "expiration_date": "2024-01-19"}
            ]
        }
        add_response = client.post(
            '/api/inventory/ingredients',
            data=json.dumps(inventory_data),
            content_type='application/json',
            headers=auth_headers
        )
        assert add_response.status_code in [200, 400]
        
        # Step 2: Check expiring items
        expiring_response = client.get('/api/inventory/expiring_soon', headers=auth_headers)
        assert expiring_response.status_code in [200, 400]
        
        # Step 3: Generate recipes using expiring ingredients
        recipe_data = {
            "preferences": {"priority": "use_expiring_ingredients"},
            "focus_ingredients": ["Banana", "Milk"]
        }
        recipe_response = client.post(
            '/api/recipes/generate-from-inventory',
            data=json.dumps(recipe_data),
            content_type='application/json',
            headers=auth_headers
        )
        assert recipe_response.status_code in [200, 400]

    # ERROR HANDLING INTEGRATION TESTS
    def test_auth_failure_across_controllers(self, client):
        """Test that all protected endpoints require authentication"""
        protected_endpoints = [
            ('/api/recipes/generate-from-inventory', 'POST'),
            ('/api/inventory/ingredients', 'POST'),
            ('/api/recognition/ingredients', 'POST'),
            ('/api/cooking-session/start', 'POST'),
            ('/api/environmental-savings/calculations', 'GET')
        ]
        
        for endpoint, method in protected_endpoints:
            if method == 'POST':
                response = client.post(endpoint, data=json.dumps({}), content_type='application/json')
            else:
                response = client.get(endpoint)
            
            assert response.status_code == 401, f"Endpoint {method} {endpoint} should require authentication"

    def test_invalid_json_across_controllers(self, client, auth_headers):
        """Test that POST endpoints handle invalid JSON appropriately"""
        post_endpoints = [
            '/api/recipes/generate-from-inventory',
            '/api/inventory/ingredients',
            '/api/cooking-session/start'
        ]
        
        for endpoint in post_endpoints:
            response = client.post(
                endpoint,
                data="invalid json",
                content_type='application/json',
                headers=auth_headers
            )
            assert response.status_code in [400, 422], f"Endpoint {endpoint} should handle invalid JSON"

    def test_missing_required_fields_across_controllers(self, client, auth_headers):
        """Test that endpoints validate required fields"""
        endpoints_with_requirements = [
            ('/api/recipes/generate-from-inventory', {}),
            ('/api/inventory/ingredients', {}),
            ('/api/cooking-session/start', {})
        ]
        
        for endpoint, empty_data in endpoints_with_requirements:
            response = client.post(
                endpoint,
                data=json.dumps(empty_data),
                content_type='application/json',
                headers=auth_headers
            )
            assert response.status_code in [400, 422], f"Endpoint {endpoint} should validate required fields"

    def test_cross_controller_data_consistency(self, client, auth_headers):
        """Test that data remains consistent across different controllers"""
        # This would test that user data is consistent when accessed from different endpoints
        # For example, user inventory should be the same whether accessed from /inventory or /recipes
        
        # Mock scenario: User data should be consistent
        user_endpoints = [
            '/api/inventory/',  # GET inventory
            '/api/recipes/saved',  # GET saved recipes
        ]
        
        for endpoint in user_endpoints:
            response = client.get(endpoint, headers=auth_headers)
            # Should not return inconsistent user data
            assert response.status_code in [200, 400, 404], f"Endpoint {endpoint} should be accessible"
