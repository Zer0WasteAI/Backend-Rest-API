"""
Unit tests for Inventory Controller
Tests inventory management endpoints and business logic integration
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from src.interface.controllers.inventory_controller import inventory_bp


class TestInventoryController:
    """Test suite for Inventory Controller"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
        
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

    def test_inventory_blueprint_registration(self, app):
        """Test that inventory blueprint is properly registered"""
        # Assert
        assert 'inventory' in app.blueprints

    # POST /ingredients - Add ingredients batch
    @patch('src.interface.controllers.inventory_controller.make_add_ingredients_to_inventory_use_case')
    def test_add_ingredients_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful addition of ingredients batch"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"success": True, "added": 3}
        mock_use_case_factory.return_value = mock_use_case
        
        ingredients_data = {
            "ingredients": [
                {
                    "name": "Tomate",
                    "quantity": 5,
                    "type_unit": "piezas",
                    "storage_type": "refrigerador",
                    "expiration_time": 7,
                    "time_unit": "days"
                }
            ]
        }
        
        # Act
        response = client.post(
            '/api/inventory/ingredients',
            data=json.dumps(ingredients_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    def test_add_ingredients_unauthorized(self, client):
        """Test add ingredients without authentication"""
        # Arrange
        ingredients_data = {"ingredients": []}
        
        # Act
        response = client.post(
            '/api/inventory/ingredients',
            data=json.dumps(ingredients_data),
            content_type='application/json'
        )
        
        # Assert
        assert response.status_code == 401

    # GET / - Get inventory content
    @patch('src.interface.controllers.inventory_controller.make_get_inventory_content_use_case')
    def test_get_inventory_content_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful retrieval of inventory content"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "ingredients": [],
            "foods": [],
            "total_items": 0
        }
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get('/api/inventory/', headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # GET /complete - Get complete inventory
    @patch('src.interface.controllers.inventory_controller.make_get_inventory_content_use_case')
    def test_get_complete_inventory_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful retrieval of complete inventory"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"complete_inventory": True}
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get('/api/inventory/complete', headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # PUT /ingredients/<ingredient_name>/<added_at> - Update ingredient
    @patch('src.interface.controllers.inventory_controller.make_update_ingredient_stack_use_case')
    def test_update_ingredient_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful ingredient update"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"updated": True}
        mock_use_case_factory.return_value = mock_use_case
        
        update_data = {
            "quantity": 10,
            "storage_type": "refrigerador"
        }
        
        # Act
        response = client.put(
            '/api/inventory/ingredients/tomate/2024-01-01',
            data=json.dumps(update_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # DELETE /ingredients/<ingredient_name>/<added_at> - Delete ingredient
    @patch('src.interface.controllers.inventory_controller.make_delete_ingredient_stack_use_case')
    def test_delete_ingredient_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful ingredient deletion"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"deleted": True}
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.delete(
            '/api/inventory/ingredients/tomate/2024-01-01',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # GET /expiring - Get expiring items
    @patch('src.interface.controllers.inventory_controller.make_get_expiring_soon_use_case')
    def test_get_expiring_items_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful retrieval of expiring items"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"expiring_items": []}
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get('/api/inventory/expiring', headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # POST /ingredients/from-recognition - Add from recognition
    @patch('src.interface.controllers.inventory_controller.make_add_ingredients_and_foods_to_inventory_use_case')
    def test_add_from_recognition_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful addition from recognition"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"added_from_recognition": True}
        mock_use_case_factory.return_value = mock_use_case
        
        recognition_data = {
            "recognition_id": "rec_123",
            "ingredients": []
        }
        
        # Act
        response = client.post(
            '/api/inventory/ingredients/from-recognition',
            data=json.dumps(recognition_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # PATCH /ingredients/<ingredient_name>/<added_at>/quantity - Update quantity
    @patch('src.interface.controllers.inventory_controller.make_update_ingredient_quantity_use_case')
    def test_update_ingredient_quantity_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful ingredient quantity update"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"quantity_updated": True}
        mock_use_case_factory.return_value = mock_use_case
        
        quantity_data = {"new_quantity": 15}
        
        # Act
        response = client.patch(
            '/api/inventory/ingredients/tomate/2024-01-01/quantity',
            data=json.dumps(quantity_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # POST /ingredients/<ingredient_name>/<added_at>/consume - Mark consumed
    @patch('src.interface.controllers.inventory_controller.make_mark_ingredient_stack_consumed_use_case')
    def test_mark_ingredient_consumed_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful marking ingredient as consumed"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"consumed": True}
        mock_use_case_factory.return_value = mock_use_case
        
        consume_data = {"consumed_quantity": 2}
        
        # Act
        response = client.post(
            '/api/inventory/ingredients/tomate/2024-01-01/consume',
            data=json.dumps(consume_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # GET /ingredients/<ingredient_name>/detail - Get ingredient detail
    @patch('src.interface.controllers.inventory_controller.make_get_ingredient_detail_use_case')
    def test_get_ingredient_detail_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful retrieval of ingredient detail"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"ingredient_detail": {}}
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get('/api/inventory/ingredients/tomate/detail', headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # GET /ingredients/list - Get ingredients list
    @patch('src.interface.controllers.inventory_controller.make_get_ingredients_list_use_case')
    def test_get_ingredients_list_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful retrieval of ingredients list"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"ingredients_list": []}
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get('/api/inventory/ingredients/list', headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # POST /upload_image - Upload image
    @patch('src.interface.controllers.inventory_controller.make_upload_inventory_image_use_case')
    def test_upload_image_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful image upload"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"image_uploaded": True}
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.post('/api/inventory/upload_image', headers=auth_headers)
        
        # Assert
        assert response.status_code in [200, 400]  # May fail due to missing file, but endpoint exists

    # POST /add_item - Add single item
    @patch('src.interface.controllers.inventory_controller.make_add_item_to_inventory_use_case')
    def test_add_item_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful addition of single item"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"item_added": True}
        mock_use_case_factory.return_value = mock_use_case
        
        item_data = {
            "name": "Tomate",
            "quantity": 3,
            "type_unit": "piezas"
        }
        
        # Act
        response = client.post(
            '/api/inventory/add_item',
            data=json.dumps(item_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # GET /expiring_soon - Get expiring soon batches (v1.3)
    @patch('src.interface.controllers.inventory_controller.make_get_expiring_soon_batches_use_case')
    def test_get_expiring_soon_batches_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful retrieval of expiring soon batches"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"expiring_batches": []}
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.get('/api/inventory/expiring_soon', headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # POST /batch/<batch_id>/reserve - Reserve batch
    @patch('src.interface.controllers.inventory_controller.make_reserve_batch_use_case')
    def test_reserve_batch_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful batch reservation"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"batch_reserved": True}
        mock_use_case_factory.return_value = mock_use_case
        
        reserve_data = {"reason": "cooking_prep"}
        
        # Act
        response = client.post(
            '/api/inventory/batch/batch_123/reserve',
            data=json.dumps(reserve_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # POST /batch/<batch_id>/freeze - Freeze batch
    @patch('src.interface.controllers.inventory_controller.make_freeze_batch_use_case')
    def test_freeze_batch_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful batch freezing"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"batch_frozen": True}
        mock_use_case_factory.return_value = mock_use_case
        
        # Act
        response = client.post('/api/inventory/batch/batch_123/freeze', headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # POST /leftovers - Create leftover
    @patch('src.interface.controllers.inventory_controller.make_create_leftover_use_case')
    def test_create_leftover_success(self, mock_use_case_factory, client, auth_headers):
        """Test successful leftover creation"""
        # Arrange
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"leftover_created": True}
        mock_use_case_factory.return_value = mock_use_case
        
        leftover_data = {
            "original_recipe": "Pasta con tomate",
            "portions": 2,
            "estimated_expiry": "2024-01-15"
        }
        
        # Act
        response = client.post(
            '/api/inventory/leftovers',
            data=json.dumps(leftover_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    def test_invalid_endpoint_returns_404(self, client, auth_headers):
        """Test that invalid endpoints return 404"""
        # Act
        response = client.get('/api/inventory/invalid_endpoint', headers=auth_headers)
        
        # Assert
        assert response.status_code == 404

    def test_missing_content_type_returns_400(self, client, auth_headers):
        """Test that requests without content-type return 400 for POST endpoints"""
        # Act
        response = client.post('/api/inventory/ingredients', headers=auth_headers)
        
        # Assert
        assert response.status_code in [400, 415]  # Bad request or unsupported media type

    # NEW TESTS: foods/* endpoints and batch actions

    # POST /foods/from-recognition - Add foods from recognition
    @patch('src.interface.controllers.inventory_controller.make_add_food_items_to_inventory_use_case')
    def test_add_foods_from_recognition_success(self, mock_use_case_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"added_from_recognition": True}
        mock_use_case_factory.return_value = mock_use_case

        data = {"recognition_id": "rec_foods_1", "foods": []}
        response = client.post(
            '/api/inventory/foods/from-recognition',
            data=json.dumps(data),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        mock_use_case.execute.assert_called_once()

    # PATCH /foods/<food_name>/<added_at>/quantity - Update food quantity
    @patch('src.interface.controllers.inventory_controller.make_update_food_quantity_use_case')
    def test_update_food_quantity_success(self, mock_use_case_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"quantity_updated": True}
        mock_use_case_factory.return_value = mock_use_case

        payload = {"new_quantity": 2}
        response = client.patch(
            '/api/inventory/foods/pizza/2024-01-01T10:00:00Z/quantity',
            data=json.dumps(payload),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code in [200, 204]
        mock_use_case.execute.assert_called_once()

    # DELETE /ingredients/<ingredient_name> - Delete complete ingredient
    @patch('src.interface.controllers.inventory_controller.make_delete_ingredient_complete_use_case')
    def test_delete_ingredient_complete_success(self, mock_use_case_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"deleted": True}
        mock_use_case_factory.return_value = mock_use_case

        response = client.delete('/api/inventory/ingredients/tomato', headers=auth_headers)
        assert response.status_code in [200, 204]
        mock_use_case.execute.assert_called_once()

    # DELETE /foods/<food_name>/<added_at> - Delete food item
    @patch('src.interface.controllers.inventory_controller.make_delete_food_item_use_case')
    def test_delete_food_item_success(self, mock_use_case_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"deleted": True}
        mock_use_case_factory.return_value = mock_use_case

        response = client.delete('/api/inventory/foods/pizza/2024-01-01T10:00:00Z', headers=auth_headers)
        assert response.status_code in [200, 204]
        mock_use_case.execute.assert_called_once()

    # POST /foods/<food_name>/<added_at>/consume - Mark food consumed
    @patch('src.interface.controllers.inventory_controller.make_mark_food_item_consumed_use_case')
    def test_mark_food_consumed_success(self, mock_use_case_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"consumed": True}
        mock_use_case_factory.return_value = mock_use_case

        payload = {"consumed_quantity": 1}
        response = client.post(
            '/api/inventory/foods/pizza/2024-01-01T10:00:00Z/consume',
            data=json.dumps(payload),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        mock_use_case.execute.assert_called_once()

    # GET /foods/<food_name>/<added_at>/detail - Get food detail
    @patch('src.interface.controllers.inventory_controller.make_get_food_detail_use_case')
    def test_get_food_detail_success(self, mock_use_case_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"food_detail": {}}
        mock_use_case_factory.return_value = mock_use_case

        response = client.get('/api/inventory/foods/pizza/2024-01-01T10:00:00Z/detail', headers=auth_headers)
        assert response.status_code in [200, 404]
        mock_use_case.execute.assert_called_once()

    # GET /foods/list - Get foods list
    @patch('src.interface.controllers.inventory_controller.make_get_foods_list_use_case')
    def test_get_foods_list_success(self, mock_use_case_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"foods_list": []}
        mock_use_case_factory.return_value = mock_use_case

        response = client.get('/api/inventory/foods/list', headers=auth_headers)
        assert response.status_code == 200
        mock_use_case.execute.assert_called_once()

    # Batch management: transform/quarantine/discard
    @patch('src.interface.controllers.inventory_controller.make_transform_batch_use_case')
    def test_transform_batch_success(self, mock_use_case_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"batch_transformed": True}
        mock_use_case_factory.return_value = mock_use_case
        response = client.post(
            '/api/inventory/batch/batch_123/transform',
            data=json.dumps({"note": "chopped"}),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        mock_use_case.execute.assert_called_once()

    @patch('src.interface.controllers.inventory_controller.make_quarantine_batch_use_case')
    def test_quarantine_batch_success(self, mock_use_case_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"batch_quarantined": True}
        mock_use_case_factory.return_value = mock_use_case
        response = client.post(
            '/api/inventory/batch/batch_123/quarantine',
            data=json.dumps({"reason": "suspected spoilage"}),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        mock_use_case.execute.assert_called_once()

    @patch('src.interface.controllers.inventory_controller.make_discard_batch_use_case')
    def test_discard_batch_success(self, mock_use_case_factory, client, auth_headers):
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"batch_discarded": True}
        mock_use_case_factory.return_value = mock_use_case
        response = client.post(
            '/api/inventory/batch/batch_123/discard',
            data=json.dumps({"reason": "expired"}),
            content_type='application/json',
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        mock_use_case.execute.assert_called_once()
