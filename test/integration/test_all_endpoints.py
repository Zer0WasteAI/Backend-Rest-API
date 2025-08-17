import pytest
import json
import uuid
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_testing import TestCase


class TestAllV13Endpoints(TestCase):
    """Comprehensive test suite for all v1.3 endpoints"""

    def create_app(self):
        """Create test app"""
        # Import here to avoid circular imports
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app

    def setUp(self):
        """Setup test fixtures"""
        self.user_uid = "test_user_123"
        self.recipe_uid = "recipe_test_001"
        self.session_id = str(uuid.uuid4())
        self.batch_id = str(uuid.uuid4())
        self.leftover_id = str(uuid.uuid4())
        
        # Mock JWT token
        self.auth_headers = {
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
        }

    # ===============================
    # MISE EN PLACE ENDPOINTS
    # ===============================

    @patch('src.interface.controllers.cooking_session_controller.get_jwt_identity')
    @patch('src.application.factories.cooking_session_factory.make_get_mise_en_place_use_case')
    def test_mise_en_place_endpoint_comprehensive(self, mock_factory, mock_jwt):
        """Test comprehensive mise en place endpoint functionality"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        
        mock_use_case = Mock()
        mock_mise_en_place = Mock()
        mock_mise_en_place.to_dict.return_value = {
            "recipe_uid": self.recipe_uid,
            "servings": 4,
            "tools": ["cuchillo", "tabla de cortar", "sartén", "olla mediana"],
            "preheat": [
                {
                    "device": "stove",
                    "setting": "medium",
                    "duration_ms": 60000
                }
            ],
            "prep_tasks": [
                {
                    "id": "mp1",
                    "text": "Picar cebolla en cubos (160 g)",
                    "ingredient_uid": "ing_onion",
                    "suggested_qty": 160,
                    "unit": "g"
                },
                {
                    "id": "mp2",
                    "text": "Deshilachar pollo cocido (640 g)",
                    "ingredient_uid": "ing_chicken_breast",
                    "suggested_qty": 640,
                    "unit": "g"
                }
            ],
            "measured_ingredients": [
                {
                    "ingredient_uid": "ing_onion",
                    "qty": 160,
                    "unit": "g",
                    "lot_suggestion": "batch_onion_777"
                },
                {
                    "ingredient_uid": "ing_chicken_breast",
                    "qty": 640,
                    "unit": "g",
                    "lot_suggestion": "batch_chicken_888"
                },
                {
                    "ingredient_uid": "ing_bread",
                    "qty": 100,
                    "unit": "g",
                    "lot_suggestion": None
                }
            ]
        }
        
        mock_use_case.execute.return_value = mock_mise_en_place
        mock_factory.return_value = mock_use_case
        
        # Act
        response = self.client.get(
            f'/api/recipes/{self.recipe_uid}/mise_en_place?servings=4',
            headers=self.auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify complete structure
        assert data["recipe_uid"] == self.recipe_uid
        assert data["servings"] == 4
        assert "tools" in data
        assert "preheat" in data
        assert "prep_tasks" in data
        assert "measured_ingredients" in data
        
        # Verify tools
        assert "cuchillo" in data["tools"]
        assert "sartén" in data["tools"]
        
        # Verify preheat instructions
        assert len(data["preheat"]) == 1
        assert data["preheat"][0]["device"] == "stove"
        assert data["preheat"][0]["duration_ms"] == 60000
        
        # Verify prep tasks with scaling
        assert len(data["prep_tasks"]) == 2
        onion_task = next(t for t in data["prep_tasks"] if "cebolla" in t["text"])
        assert onion_task["suggested_qty"] == 160  # Scaled for 4 servings
        
        # Verify FEFO suggestions
        assert len(data["measured_ingredients"]) == 3
        onion_ingredient = next(i for i in data["measured_ingredients"] if i["ingredient_uid"] == "ing_onion")
        assert onion_ingredient["lot_suggestion"] == "batch_onion_777"

    @patch('src.interface.controllers.cooking_session_controller.get_jwt_identity')
    def test_mise_en_place_invalid_servings(self, mock_jwt):
        """Test mise en place with invalid servings parameter"""
        mock_jwt.return_value = self.user_uid
        
        response = self.client.get(
            f'/api/recipes/{self.recipe_uid}/mise_en_place?servings=0',
            headers=self.auth_headers
        )
        
        assert response.status_code in [400, 422]

    @patch('src.interface.controllers.cooking_session_controller.get_jwt_identity')
    @patch('src.application.factories.cooking_session_factory.make_get_mise_en_place_use_case')
    def test_mise_en_place_recipe_not_found(self, mock_factory, mock_jwt):
        """Test mise en place with non-existent recipe"""
        from src.shared.exceptions.custom import RecipeNotFoundException
        
        mock_jwt.return_value = self.user_uid
        mock_use_case = Mock()
        mock_use_case.execute.side_effect = RecipeNotFoundException("Recipe not found")
        mock_factory.return_value = mock_use_case
        
        response = self.client.get(
            f'/api/recipes/non_existent_recipe/mise_en_place?servings=2',
            headers=self.auth_headers
        )
        
        assert response.status_code == 404

    # ===============================
    # COOKING SESSION ENDPOINTS
    # ===============================

    @patch('src.interface.controllers.cooking_session_controller.get_jwt_identity')
    @patch('src.application.factories.cooking_session_factory.make_start_cooking_session_use_case')
    def test_start_cooking_session_comprehensive(self, mock_factory, mock_jwt):
        """Test comprehensive cooking session start"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        
        mock_use_case = Mock()
        mock_session = Mock()
        mock_session.session_id = self.session_id
        mock_use_case.execute.return_value = mock_session
        mock_factory.return_value = mock_use_case
        
        request_data = {
            "recipe_uid": self.recipe_uid,
            "servings": 3,
            "level": "intermediate",
            "started_at": datetime.utcnow().isoformat()
        }
        
        # Act
        with patch('src.infrastructure.services.idempotency_service.IdempotencyService.check_idempotency', return_value=None):
            with patch('src.infrastructure.services.idempotency_service.IdempotencyService.store_response'):
                response = self.client.post(
                    '/api/recipes/cooking_session/start',
                    data=json.dumps(request_data),
                    headers={**self.auth_headers, 'Idempotency-Key': str(uuid.uuid4())}
                )
        
        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["session_id"] == self.session_id
        assert data["status"] == "running"

    @patch('src.interface.controllers.cooking_session_controller.get_jwt_identity')
    @patch('src.application.factories.cooking_session_factory.make_complete_step_use_case')
    def test_complete_cooking_step_comprehensive(self, mock_factory, mock_jwt):
        """Test comprehensive cooking step completion"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "ok": True,
            "inventory_updates": [
                {"lot_id": "batch_chicken_123", "new_qty": 300.0},
                {"lot_id": "batch_onion_456", "new_qty": 150.0}
            ],
            "step_completed_at": datetime.utcnow().isoformat()
        }
        mock_factory.return_value = mock_use_case
        
        request_data = {
            "session_id": self.session_id,
            "step_id": "S2",
            "timer_ms": 180000,  # 3 minutes
            "consumptions": [
                {
                    "ingredient_uid": "ing_chicken_breast",
                    "lot_id": "batch_chicken_123",
                    "qty": 320,
                    "unit": "g"
                },
                {
                    "ingredient_uid": "ing_onion",
                    "lot_id": "batch_onion_456",
                    "qty": 80,
                    "unit": "g"
                }
            ]
        }
        
        # Act
        with patch('src.infrastructure.services.idempotency_service.IdempotencyService.check_idempotency', return_value=None):
            with patch('src.infrastructure.services.idempotency_service.IdempotencyService.store_response'):
                response = self.client.post(
                    '/api/recipes/cooking_session/complete_step',
                    data=json.dumps(request_data),
                    headers={**self.auth_headers, 'Idempotency-Key': str(uuid.uuid4())}
                )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["ok"] is True
        assert len(data["inventory_updates"]) == 2
        assert data["inventory_updates"][0]["lot_id"] == "batch_chicken_123"
        assert data["inventory_updates"][0]["new_qty"] == 300.0

    @patch('src.interface.controllers.cooking_session_controller.get_jwt_identity')
    @patch('src.application.factories.cooking_session_factory.make_finish_cooking_session_use_case')
    def test_finish_cooking_session_comprehensive(self, mock_factory, mock_jwt):
        """Test comprehensive cooking session finish with environmental calculation"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "ok": True,
            "session_id": self.session_id,
            "finished_at": datetime.utcnow().isoformat(),
            "total_cooking_time_ms": 2700000,  # 45 minutes
            "environmental_saving": {
                "co2e_kg": 0.65,
                "water_l": 145.0,
                "waste_kg": 0.22
            },
            "leftover_suggestion": {
                "portions": 2,
                "eat_by": (date.today() + timedelta(days=2)).isoformat()
            }
        }
        mock_factory.return_value = mock_use_case
        
        request_data = {
            "session_id": self.session_id,
            "notes": "Delicious meal! Perfect seasoning.",
            "photo_url": "https://example.com/photos/my_dish.jpg"
        }
        
        # Act
        with patch('src.infrastructure.services.idempotency_service.IdempotencyService.check_idempotency', return_value=None):
            with patch('src.infrastructure.services.idempotency_service.IdempotencyService.store_response'):
                response = self.client.post(
                    '/api/recipes/cooking_session/finish',
                    data=json.dumps(request_data),
                    headers={**self.auth_headers, 'Idempotency-Key': str(uuid.uuid4())}
                )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["ok"] is True
        assert data["session_id"] == self.session_id
        assert data["total_cooking_time_ms"] == 2700000
        
        # Check environmental savings
        env_saving = data["environmental_saving"]
        assert env_saving["co2e_kg"] == 0.65
        assert env_saving["water_l"] == 145.0
        assert env_saving["waste_kg"] == 0.22
        
        # Check leftover suggestion
        leftover_suggestion = data["leftover_suggestion"]
        assert leftover_suggestion["portions"] == 2

    # ===============================
    # BATCH MANAGEMENT ENDPOINTS
    # ===============================

    @patch('src.interface.controllers.inventory_controller.get_jwt_identity')
    @patch('src.application.factories.batch_management_factory.make_get_expiring_soon_batches_use_case')
    def test_get_expiring_soon_comprehensive(self, mock_factory, mock_jwt):
        """Test comprehensive expiring soon endpoint"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = [
            {
                "batch_id": "batch_urgent_001",
                "ingredient_uid": "ing_spinach",
                "qty": 120,
                "unit": "g",
                "expiry_date": (datetime.utcnow() + timedelta(hours=18)).isoformat(),
                "storage_location": "fridge",
                "label_type": "use_by",
                "state": "expiring_soon",
                "urgency_score": 0.95,
                "days_to_expiry": 0
            },
            {
                "batch_id": "batch_urgent_002",
                "ingredient_uid": "ing_milk",
                "qty": 500,
                "unit": "ml",
                "expiry_date": (datetime.utcnow() + timedelta(days=2)).isoformat(),
                "storage_location": "fridge",
                "label_type": "use_by",
                "state": "available",
                "urgency_score": 0.85,
                "days_to_expiry": 2
            },
            {
                "batch_id": "batch_moderate_003",
                "ingredient_uid": "ing_bread",
                "qty": 1,
                "unit": "units",
                "expiry_date": (datetime.utcnow() + timedelta(days=3)).isoformat(),
                "storage_location": "pantry",
                "label_type": "best_before",
                "state": "available",
                "urgency_score": 0.60,
                "days_to_expiry": 3
            }
        ]
        mock_factory.return_value = mock_use_case
        
        # Act
        response = self.client.get(
            '/api/inventory/expiring_soon?withinDays=4&storage=fridge',
            headers=self.auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 3
        
        # Verify ordering by urgency (highest first)
        assert data[0]["urgency_score"] >= data[1]["urgency_score"]
        assert data[1]["urgency_score"] >= data[2]["urgency_score"]
        
        # Verify most urgent item
        most_urgent = data[0]
        assert most_urgent["batch_id"] == "batch_urgent_001"
        assert most_urgent["urgency_score"] == 0.95
        assert most_urgent["label_type"] == "use_by"

    @patch('src.interface.controllers.inventory_controller.get_jwt_identity')
    @patch('src.application.factories.batch_management_factory.make_freeze_batch_use_case')
    def test_freeze_batch_comprehensive(self, mock_factory, mock_jwt):
        """Test comprehensive batch freezing"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        
        mock_use_case = Mock()
        new_expiry = datetime.utcnow() + timedelta(days=90)  # 3 months frozen storage
        mock_use_case.execute.return_value = {
            "batch_id": self.batch_id,
            "state": "frozen",
            "storage_location": "freezer",
            "new_expiry_date": new_expiry.isoformat()
        }
        mock_factory.return_value = mock_use_case
        
        request_data = {
            "new_best_before": new_expiry.isoformat()
        }
        
        # Act
        response = self.client.post(
            f'/api/inventory/batch/{self.batch_id}/freeze',
            data=json.dumps(request_data),
            headers=self.auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["batch_id"] == self.batch_id
        assert data["state"] == "frozen"
        assert data["storage_location"] == "freezer"

    @patch('src.interface.controllers.inventory_controller.get_jwt_identity')
    @patch('src.application.factories.batch_management_factory.make_transform_batch_use_case')
    def test_transform_batch_comprehensive(self, mock_factory, mock_jwt):
        """Test comprehensive batch transformation"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        
        mock_use_case = Mock()
        new_batch_id = str(uuid.uuid4())
        mock_use_case.execute.return_value = {
            "original_batch_id": self.batch_id,
            "new_batch_id": new_batch_id,
            "output_type": "sofrito",
            "yield_qty": 250.0,
            "unit": "g",
            "eat_by": (date.today() + timedelta(days=3)).isoformat()
        }
        mock_factory.return_value = mock_use_case
        
        request_data = {
            "output_type": "sofrito",
            "yield_qty": 250.0,
            "unit": "g",
            "eat_by": (datetime.utcnow() + timedelta(days=3)).isoformat()
        }
        
        # Act
        response = self.client.post(
            f'/api/inventory/batch/{self.batch_id}/transform',
            data=json.dumps(request_data),
            headers=self.auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["original_batch_id"] == self.batch_id
        assert data["new_batch_id"] == new_batch_id
        assert data["output_type"] == "sofrito"
        assert data["yield_qty"] == 250.0

    @patch('src.interface.controllers.inventory_controller.get_jwt_identity')
    @patch('src.application.factories.batch_management_factory.make_discard_batch_use_case')
    def test_discard_batch_with_environmental_impact(self, mock_factory, mock_jwt):
        """Test comprehensive batch discard with environmental impact calculation"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        
        mock_use_case = Mock()
        waste_id = str(uuid.uuid4())
        mock_use_case.execute.return_value = {
            "waste_id": waste_id,
            "batch_id": self.batch_id,
            "co2e_wasted_kg": 0.275,  # Environmental impact of 550g food waste
            "discarded_at": datetime.utcnow().isoformat()
        }
        mock_factory.return_value = mock_use_case
        
        request_data = {
            "estimated_weight": 550.0,
            "unit": "g",
            "reason": "bad_condition"
        }
        
        # Act
        response = self.client.post(
            f'/api/inventory/batch/{self.batch_id}/discard',
            data=json.dumps(request_data),
            headers=self.auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["waste_id"] == waste_id
        assert data["batch_id"] == self.batch_id
        assert data["co2e_wasted_kg"] == 0.275

    # ===============================
    # LEFTOVER MANAGEMENT ENDPOINTS
    # ===============================

    @patch('src.interface.controllers.inventory_controller.get_jwt_identity')
    @patch('src.application.factories.leftover_factory.make_create_leftover_use_case')
    def test_create_leftover_comprehensive(self, mock_factory, mock_jwt):
        """Test comprehensive leftover creation with planner integration"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "leftover_id": self.leftover_id,
            "title": "Ají de gallina (sobras)",
            "portions": 3,
            "eat_by": (date.today() + timedelta(days=2)).isoformat(),
            "storage_location": "fridge",
            "created_at": datetime.utcnow().isoformat(),
            "planner_suggestion": {
                "date": date.today().isoformat(),
                "meal_type": "dinner"
            }
        }
        mock_factory.return_value = mock_use_case
        
        request_data = {
            "recipe_uid": self.recipe_uid,
            "title": "Ají de gallina (sobras)",
            "portions": 3,
            "eat_by": (date.today() + timedelta(days=2)).isoformat(),
            "storage_location": "fridge",
            "session_id": self.session_id
        }
        
        # Act
        response = self.client.post(
            '/api/inventory/leftovers',
            data=json.dumps(request_data),
            headers=self.auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["leftover_id"] == self.leftover_id
        assert data["title"] == "Ají de gallina (sobras)"
        assert data["portions"] == 3
        assert "planner_suggestion" in data
        assert data["planner_suggestion"]["meal_type"] == "dinner"

    # ===============================
    # ENVIRONMENTAL SAVINGS ENDPOINTS
    # ===============================

    @patch('src.interface.controllers.environmental_savings_controller.get_jwt_identity')
    @patch('src.application.factories.environmental_savings_factory.make_calculate_environmental_savings_from_session_use_case')
    def test_calculate_environmental_savings_from_session_comprehensive(self, mock_factory, mock_jwt):
        """Test comprehensive environmental savings calculation from session"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        
        mock_use_case = Mock()
        calculation_id = str(uuid.uuid4())
        mock_use_case.execute.return_value = {
            "calculation_id": calculation_id,
            "session_id": self.session_id,
            "co2e_kg": 0.58,
            "water_l": 165.0,
            "waste_kg": 0.23,
            "basis": "per_session",
            "consumptions_analyzed": 4,
            "calculated_at": datetime.utcnow().isoformat()
        }
        mock_factory.return_value = mock_use_case
        
        request_data = {
            "session_id": self.session_id,
            "actual_consumptions": [
                {"ingredient_uid": "ing_chicken_breast", "qty": 380, "unit": "g"},
                {"ingredient_uid": "ing_onion", "qty": 120, "unit": "g"},
                {"ingredient_uid": "ing_olive_oil", "qty": 25, "unit": "ml"},
                {"ingredient_uid": "ing_garlic", "qty": 15, "unit": "g"}
            ]
        }
        
        # Act
        response = self.client.post(
            '/api/environmental_savings/calculate/from-session',
            data=json.dumps(request_data),
            headers=self.auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["calculation_id"] == calculation_id
        assert data["session_id"] == self.session_id
        assert data["co2e_kg"] == 0.58
        assert data["water_l"] == 165.0
        assert data["waste_kg"] == 0.23
        assert data["basis"] == "per_session"
        assert data["consumptions_analyzed"] == 4

    # ===============================
    # ERROR HANDLING AND EDGE CASES
    # ===============================

    def test_missing_auth_headers(self):
        """Test endpoints require authentication"""
        endpoints = [
            ('/api/recipes/test_recipe/mise_en_place', 'GET'),
            ('/api/recipes/cooking_session/start', 'POST'),
            ('/api/inventory/expiring_soon', 'GET'),
            ('/api/inventory/leftovers', 'POST'),
        ]
        
        for endpoint, method in endpoints:
            if method == 'GET':
                response = self.client.get(endpoint)
            else:
                response = self.client.post(
                    endpoint,
                    data=json.dumps({}),
                    headers={'Content-Type': 'application/json'}
                )
            
            assert response.status_code in [401, 422]

    @patch('src.interface.controllers.cooking_session_controller.get_jwt_identity')
    def test_missing_idempotency_key_post_requests(self, mock_jwt):
        """Test POST requests require idempotency key"""
        mock_jwt.return_value = self.user_uid
        
        endpoints = [
            '/api/recipes/cooking_session/start',
            '/api/recipes/cooking_session/complete_step',
            '/api/recipes/cooking_session/finish'
        ]
        
        for endpoint in endpoints:
            response = self.client.post(
                endpoint,
                data=json.dumps({}),
                headers=self.auth_headers  # Missing Idempotency-Key
            )
            
            assert response.status_code in [400, 422]

    @patch('src.interface.controllers.inventory_controller.get_jwt_identity')
    def test_invalid_batch_operations(self, mock_jwt):
        """Test batch operations with invalid data"""
        mock_jwt.return_value = self.user_uid
        
        # Test invalid freeze date
        response = self.client.post(
            f'/api/inventory/batch/{self.batch_id}/freeze',
            data=json.dumps({"new_best_before": "invalid-date"}),
            headers=self.auth_headers
        )
        assert response.status_code in [400, 422]
        
        # Test missing required fields for transform
        response = self.client.post(
            f'/api/inventory/batch/{self.batch_id}/transform',
            data=json.dumps({"output_type": "sofrito"}),  # Missing other required fields
            headers=self.auth_headers
        )
        assert response.status_code in [400, 422]

    @patch('src.interface.controllers.inventory_controller.get_jwt_identity')
    def test_invalid_leftover_creation(self, mock_jwt):
        """Test leftover creation with invalid data"""
        mock_jwt.return_value = self.user_uid
        
        # Test past eat_by date
        past_date = date.today() - timedelta(days=1)
        response = self.client.post(
            '/api/inventory/leftovers',
            data=json.dumps({
                "recipe_uid": self.recipe_uid,
                "title": "Test Leftover",
                "portions": 2,
                "eat_by": past_date.isoformat(),
                "storage_location": "fridge"
            }),
            headers=self.auth_headers
        )
        assert response.status_code in [400, 422]
        
        # Test zero portions
        response = self.client.post(
            '/api/inventory/leftovers',
            data=json.dumps({
                "recipe_uid": self.recipe_uid,
                "title": "Test Leftover",
                "portions": 0,
                "eat_by": (date.today() + timedelta(days=2)).isoformat(),
                "storage_location": "fridge"
            }),
            headers=self.auth_headers
        )
        assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__])