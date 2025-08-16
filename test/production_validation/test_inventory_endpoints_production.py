"""
Production Validation Tests for Inventory Management Endpoints
Tests all 25+ inventory endpoints with comprehensive scenarios for production readiness
"""
import pytest
import json
import io
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage
from src.main import create_app


class TestInventoryEndpointsProduction:
    """Production validation tests for all inventory management endpoints"""

    @pytest.fixture(scope="class")
    def app(self):
        app = create_app()
        app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "JWT_ACCESS_TOKEN_EXPIRES": False,
        })
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def auth_headers(self, app):
        """Create valid auth headers for testing"""
        with app.app_context():
            from flask_jwt_extended import create_access_token
            token = create_access_token(identity="test-user-uid")
            return {"Authorization": f"Bearer {token}"}

    # ================================================================
    # POST /api/inventory/ingredients - Add Ingredients Batch
    # ================================================================

    def test_add_ingredients_batch_success(self, client, auth_headers):
        """Test successful batch addition of ingredients"""
        with patch('src.application.use_cases.inventory.add_ingredients_to_inventory_use_case.AddIngredientsToInventoryUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Ingredients added successfully",
                "added_count": 3,
                "ingredients": ["tomato", "onion", "garlic"]
            }

            ingredients_data = {
                "ingredients": [
                    {
                        "name": "tomato",
                        "quantity": 5,
                        "unit": "pieces",
                        "expiration_date": "2024-01-15",
                        "category": "vegetable"
                    },
                    {
                        "name": "onion", 
                        "quantity": 2,
                        "unit": "pieces",
                        "expiration_date": "2024-01-20"
                    }
                ]
            }

            response = client.post('/api/inventory/ingredients',
                json=ingredients_data,
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['added_count'] == 3
            assert 'tomato' in data['ingredients']

    def test_add_ingredients_invalid_data(self, client, auth_headers):
        """Test adding ingredients with invalid data"""
        invalid_data = {
            "ingredients": [
                {
                    "name": "",  # Empty name
                    "quantity": -5,  # Negative quantity
                    "unit": "pieces"
                }
            ]
        }

        response = client.post('/api/inventory/ingredients',
            json=invalid_data,
            headers=auth_headers)

        assert response.status_code == 400

    def test_add_ingredients_unauthorized(self, client):
        """Test adding ingredients without authentication"""
        response = client.post('/api/inventory/ingredients',
            json={"ingredients": []})

        assert response.status_code == 401

    def test_add_ingredients_rate_limiting(self, client, auth_headers):
        """Test rate limiting on ingredient addition (inventory_bulk: 10 req/min)"""
        with patch('src.application.use_cases.inventory.add_ingredients_to_inventory_use_case.AddIngredientsToInventoryUseCase.execute'):
            for i in range(12):
                response = client.post('/api/inventory/ingredients',
                    json={"ingredients": [{"name": f"item{i}", "quantity": 1}]},
                    headers=auth_headers)
                
                if i < 10:
                    assert response.status_code in [200, 400]
                else:
                    assert response.status_code == 429

    # ================================================================
    # GET /api/inventory - Get Inventory Overview
    # ================================================================

    def test_get_inventory_overview_success(self, client, auth_headers):
        """Test successful inventory overview retrieval"""
        with patch('src.application.use_cases.inventory.get_inventory_content_use_case.GetInventoryContentUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "total_items": 25,
                "categories": {
                    "vegetables": 10,
                    "fruits": 8,
                    "dairy": 4,
                    "meat": 3
                },
                "expiring_soon": 3,
                "last_updated": "2024-01-10T10:00:00Z"
            }

            response = client.get('/api/inventory', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_items'] == 25
            assert 'categories' in data
            assert 'expiring_soon' in data

    def test_get_inventory_overview_unauthorized(self, client):
        """Test inventory overview without authentication"""
        response = client.get('/api/inventory')
        assert response.status_code == 401

    def test_get_inventory_overview_caching(self, client, auth_headers):
        """Test that inventory overview is properly cached"""
        with patch('src.application.use_cases.inventory.get_inventory_content_use_case.GetInventoryContentUseCase.execute') as mock_execute:
            mock_execute.return_value = {"total_items": 25}

            # First request
            response1 = client.get('/api/inventory', headers=auth_headers)
            # Second request (should hit cache)
            response2 = client.get('/api/inventory', headers=auth_headers)

            assert response1.status_code == 200
            assert response2.status_code == 200
            # Cache header should be present
            assert 'Cache-Control' in response1.headers or 'ETag' in response1.headers

    # ================================================================
    # GET /api/inventory/complete - Get Complete Inventory
    # ================================================================

    def test_get_complete_inventory_success(self, client, auth_headers):
        """Test getting complete detailed inventory"""
        with patch('src.application.use_cases.inventory.get_inventory_content_use_case.GetInventoryContentUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "ingredients": [
                    {
                        "name": "tomato",
                        "quantity": 5,
                        "unit": "pieces",
                        "expiration_date": "2024-01-15",
                        "added_at": "2024-01-01T10:00:00Z",
                        "category": "vegetable"
                    }
                ],
                "foods": [
                    {
                        "name": "leftover_pizza", 
                        "quantity": 2,
                        "unit": "slices",
                        "expiration_date": "2024-01-12"
                    }
                ]
            }

            response = client.get('/api/inventory/complete', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert 'ingredients' in data
            assert 'foods' in data
            assert len(data['ingredients']) == 1

    def test_get_complete_inventory_rate_limiting(self, client, auth_headers):
        """Test rate limiting on complete inventory (ai_inventory_complete: 3 req/min)"""
        with patch('src.application.use_cases.inventory.get_inventory_content_use_case.GetInventoryContentUseCase.execute'):
            for i in range(5):
                response = client.get('/api/inventory/complete', headers=auth_headers)
                
                if i < 3:
                    assert response.status_code == 200
                else:
                    assert response.status_code == 429

    # ================================================================
    # GET /api/inventory/expiring - Get Expiring Items
    # ================================================================

    def test_get_expiring_items_success(self, client, auth_headers):
        """Test getting items expiring soon"""
        with patch('src.application.use_cases.inventory.get_expiring_soon_use_case.GetExpiringSoonUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "expiring_items": [
                    {
                        "name": "milk",
                        "expiration_date": "2024-01-12",
                        "days_until_expiry": 2,
                        "quantity": 1,
                        "unit": "liter"
                    }
                ],
                "total_expiring": 1
            }

            response = client.get('/api/inventory/expiring', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert 'expiring_items' in data
            assert data['total_expiring'] == 1

    def test_get_expiring_items_with_days_param(self, client, auth_headers):
        """Test getting expiring items with custom days parameter"""
        with patch('src.application.use_cases.inventory.get_expiring_soon_use_case.GetExpiringSoonUseCase.execute') as mock_execute:
            mock_execute.return_value = {"expiring_items": [], "total_expiring": 0}

            response = client.get('/api/inventory/expiring?days=7', headers=auth_headers)

            assert response.status_code == 200

    # ================================================================
    # Ingredient Management Endpoints
    # ================================================================

    def test_get_ingredients_list_success(self, client, auth_headers):
        """Test getting ingredients list"""
        with patch('src.application.use_cases.inventory.get_ingredients_list_use_case.GetIngredientsListUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "ingredients": [
                    {"name": "tomato", "total_quantity": 5, "stacks": 2},
                    {"name": "onion", "total_quantity": 3, "stacks": 1}
                ]
            }

            response = client.get('/api/inventory/ingredients/list', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert len(data['ingredients']) == 2

    def test_get_ingredient_detail_success(self, client, auth_headers):
        """Test getting specific ingredient details"""
        with patch('src.application.use_cases.inventory.get_ingredient_detail_use_case.GetIngredientDetailUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "name": "tomato",
                "stacks": [
                    {
                        "quantity": 3,
                        "unit": "pieces",
                        "added_at": "2024-01-01T10:00:00Z",
                        "expiration_date": "2024-01-15"
                    }
                ],
                "total_quantity": 3
            }

            response = client.get('/api/inventory/ingredients/tomato/detail', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['name'] == 'tomato'
            assert data['total_quantity'] == 3

    def test_get_ingredient_detail_not_found(self, client, auth_headers):
        """Test getting details for non-existent ingredient"""
        with patch('src.application.use_cases.inventory.get_ingredient_detail_use_case.GetIngredientDetailUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("Ingredient not found")

            response = client.get('/api/inventory/ingredients/nonexistent/detail', headers=auth_headers)

            assert response.status_code == 404

    # ================================================================
    # Ingredient Modification Endpoints
    # ================================================================

    def test_update_ingredient_stack_success(self, client, auth_headers):
        """Test updating ingredient stack"""
        with patch('src.application.use_cases.inventory.update_ingredient_stack_use_case.UpdateIngredientStackUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Ingredient stack updated successfully",
                "ingredient": "tomato",
                "new_quantity": 4
            }

            update_data = {
                "quantity": 4,
                "unit": "pieces",
                "expiration_date": "2024-01-20"
            }

            response = client.put('/api/inventory/ingredients/tomato/2024-01-01T10:00:00Z',
                json=update_data,
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['new_quantity'] == 4

    def test_update_ingredient_quantity_success(self, client, auth_headers):
        """Test updating ingredient quantity only"""
        with patch('src.application.use_cases.inventory.update_ingredient_quantity_use_case.UpdateIngredientQuantityUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Quantity updated successfully",
                "new_quantity": 3
            }

            response = client.patch('/api/inventory/ingredients/tomato/2024-01-01T10:00:00Z/quantity',
                json={"quantity": 3},
                headers=auth_headers)

            assert response.status_code == 200

    def test_update_ingredient_invalid_quantity(self, client, auth_headers):
        """Test updating ingredient with invalid quantity"""
        response = client.patch('/api/inventory/ingredients/tomato/2024-01-01T10:00:00Z/quantity',
            json={"quantity": -1},
            headers=auth_headers)

        assert response.status_code == 400

    def test_delete_ingredient_stack_success(self, client, auth_headers):
        """Test deleting specific ingredient stack"""
        with patch('src.application.use_cases.inventory.delete_ingredient_status_use_case.DeleteIngredientStatusUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Ingredient stack deleted successfully"
            }

            response = client.delete('/api/inventory/ingredients/tomato/2024-01-01T10:00:00Z',
                headers=auth_headers)

            assert response.status_code == 200

    def test_delete_all_ingredient_stacks_success(self, client, auth_headers):
        """Test deleting all stacks of an ingredient"""
        with patch('src.application.use_cases.inventory.delete_ingredient_complete_use_case.DeleteIngredientCompleteUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "All ingredient stacks deleted successfully",
                "deleted_stacks": 3
            }

            response = client.delete('/api/inventory/ingredients/tomato',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['deleted_stacks'] == 3

    # ================================================================
    # Food Item Management Endpoints
    # ================================================================

    def test_get_foods_list_success(self, client, auth_headers):
        """Test getting foods list"""
        with patch('src.application.use_cases.inventory.get_foods_list_use_case.GetFoodsListUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "foods": [
                    {"name": "leftover_pizza", "quantity": 2, "added_at": "2024-01-01T10:00:00Z"},
                    {"name": "cooked_rice", "quantity": 1, "added_at": "2024-01-02T10:00:00Z"}
                ]
            }

            response = client.get('/api/inventory/foods/list', headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert len(data['foods']) == 2

    def test_get_food_detail_success(self, client, auth_headers):
        """Test getting specific food details"""
        with patch('src.application.use_cases.inventory.get_food_detail_use_case.GetFoodDetailUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "name": "leftover_pizza",
                "quantity": 2,
                "unit": "slices",
                "added_at": "2024-01-01T10:00:00Z",
                "expiration_date": "2024-01-12"
            }

            response = client.get('/api/inventory/foods/leftover_pizza/2024-01-01T10:00:00Z/detail',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['name'] == 'leftover_pizza'

    def test_update_food_quantity_success(self, client, auth_headers):
        """Test updating food quantity"""
        with patch('src.application.use_cases.inventory.update_food_quantity_use_case.UpdateFoodQuantityUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Food quantity updated successfully",
                "new_quantity": 1
            }

            response = client.patch('/api/inventory/foods/leftover_pizza/2024-01-01T10:00:00Z/quantity',
                json={"quantity": 1},
                headers=auth_headers)

            assert response.status_code == 200

    def test_delete_food_item_success(self, client, auth_headers):
        """Test deleting food item"""
        with patch('src.application.use_cases.inventory.delete_food_item_use_case.DeleteFoodItemUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Food item deleted successfully"
            }

            response = client.delete('/api/inventory/foods/leftover_pizza/2024-01-01T10:00:00Z',
                headers=auth_headers)

            assert response.status_code == 200

    # ================================================================
    # Consumption Tracking Endpoints
    # ================================================================

    def test_mark_ingredient_consumed_success(self, client, auth_headers):
        """Test marking ingredient as consumed"""
        with patch('src.application.use_cases.inventory.mark_ingredient_stack_consumed_use_case.MarkIngredientStackConsumedUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Ingredient marked as consumed",
                "consumed_quantity": 2,
                "remaining_quantity": 1
            }

            response = client.post('/api/inventory/ingredients/tomato/2024-01-01T10:00:00Z/consume',
                json={"consumed_quantity": 2},
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['consumed_quantity'] == 2

    def test_mark_food_consumed_success(self, client, auth_headers):
        """Test marking food as consumed"""
        with patch('src.application.use_cases.inventory.mark_food_item_consumed_use_case.MarkFoodItemConsumedUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Food marked as consumed",
                "consumed_quantity": 1,
                "remaining_quantity": 1
            }

            response = client.post('/api/inventory/foods/leftover_pizza/2024-01-01T10:00:00Z/consume',
                json={"consumed_quantity": 1},
                headers=auth_headers)

            assert response.status_code == 200

    def test_mark_consumed_invalid_quantity(self, client, auth_headers):
        """Test marking consumed with invalid quantity"""
        response = client.post('/api/inventory/ingredients/tomato/2024-01-01T10:00:00Z/consume',
            json={"consumed_quantity": 0},
            headers=auth_headers)

        assert response.status_code == 400

    # ================================================================
    # Recognition Integration Endpoints
    # ================================================================

    def test_add_ingredients_from_recognition_success(self, client, auth_headers):
        """Test adding ingredients from recognition results"""
        with patch('src.application.use_cases.inventory.add_ingredients_and_foods_to_inventory_use_case.AddIngredientsAndFoodsToInventoryUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Items added from recognition",
                "added_ingredients": 3,
                "added_foods": 0
            }

            recognition_data = {
                "recognition_id": "rec_12345",
                "ingredients": [
                    {"name": "tomato", "quantity": 5},
                    {"name": "onion", "quantity": 2}
                ]
            }

            response = client.post('/api/inventory/ingredients/from-recognition',
                json=recognition_data,
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['added_ingredients'] == 3

    def test_add_foods_from_recognition_success(self, client, auth_headers):
        """Test adding foods from recognition results"""
        with patch('src.application.use_cases.inventory.add_ingredients_and_foods_to_inventory_use_case.AddIngredientsAndFoodsToInventoryUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Foods added from recognition",
                "added_ingredients": 0,
                "added_foods": 2
            }

            recognition_data = {
                "recognition_id": "rec_12345",
                "foods": [
                    {"name": "leftover_pizza", "quantity": 2}
                ]
            }

            response = client.post('/api/inventory/foods/from-recognition',
                json=recognition_data,
                headers=auth_headers)

            assert response.status_code == 200

    # ================================================================
    # Image Upload Endpoints
    # ================================================================

    def test_upload_inventory_image_success(self, client, auth_headers):
        """Test inventory image upload"""
        with patch('src.application.use_cases.inventory.upload_inventory_image_use_case.UploadInventoryImageUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Image uploaded successfully",
                "image_url": "https://storage.example.com/inventory/image.jpg",
                "image_id": "img_12345"
            }

            # Create mock file
            data = {
                'image': (io.BytesIO(b'fake image data'), 'test_image.jpg')
            }

            response = client.post('/api/inventory/upload_image',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')

            assert response.status_code == 200
            data = response.get_json()
            assert 'image_url' in data

    def test_upload_inventory_image_invalid_file(self, client, auth_headers):
        """Test inventory image upload with invalid file"""
        data = {
            'image': (io.BytesIO(b'fake pdf data'), 'test_file.pdf')
        }

        response = client.post('/api/inventory/upload_image',
            data=data,
            headers=auth_headers,
            content_type='multipart/form-data')

        assert response.status_code == 400

    def test_upload_inventory_image_missing_file(self, client, auth_headers):
        """Test inventory image upload without file"""
        response = client.post('/api/inventory/upload_image',
            data={},
            headers=auth_headers,
            content_type='multipart/form-data')

        assert response.status_code == 400

    # ================================================================
    # Single Item Addition Endpoint
    # ================================================================

    def test_add_single_item_success(self, client, auth_headers):
        """Test adding single item to inventory"""
        with patch('src.application.use_cases.inventory.add_item_to_inventory_use_case.AddItemToInventoryUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Item added successfully",
                "item_type": "ingredient",
                "item_name": "tomato"
            }

            item_data = {
                "name": "tomato",
                "quantity": 3,
                "unit": "pieces",
                "item_type": "ingredient",
                "expiration_date": "2024-01-15"
            }

            response = client.post('/api/inventory/add_item',
                json=item_data,
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['item_name'] == 'tomato'

    def test_add_single_item_missing_required_fields(self, client, auth_headers):
        """Test adding item with missing required fields"""
        incomplete_data = {
            "quantity": 3
            # Missing name, unit, item_type
        }

        response = client.post('/api/inventory/add_item',
            json=incomplete_data,
            headers=auth_headers)

        assert response.status_code == 400

    # ================================================================
    # Security and Performance Tests
    # ================================================================

    def test_inventory_endpoints_security_headers(self, client, auth_headers):
        """Test that inventory endpoints have proper security headers"""
        response = client.get('/api/inventory', headers=auth_headers)
        
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers

    def test_inventory_sql_injection_protection(self, client, auth_headers):
        """Test SQL injection protection in inventory endpoints"""
        malicious_name = "'; DROP TABLE inventory; --"
        
        response = client.get(f'/api/inventory/ingredients/{malicious_name}/detail',
            headers=auth_headers)
        
        # Should handle malicious input safely
        assert response.status_code in [400, 404]

    def test_inventory_large_batch_handling(self, client, auth_headers):
        """Test handling large ingredient batches"""
        with patch('src.application.use_cases.inventory.add_ingredients_to_inventory_use_case.AddIngredientsToInventoryUseCase.execute'):
            large_batch = {
                "ingredients": [
                    {"name": f"ingredient_{i}", "quantity": 1, "unit": "piece"}
                    for i in range(100)
                ]
            }
            
            response = client.post('/api/inventory/ingredients',
                json=large_batch,
                headers=auth_headers)
            
            # Should handle large batches gracefully
            assert response.status_code in [200, 400, 413]

    def test_inventory_concurrent_modifications(self, client, auth_headers):
        """Test concurrent inventory modifications"""
        import threading
        results = []
        
        def update_quantity():
            response = client.patch('/api/inventory/ingredients/tomato/2024-01-01T10:00:00Z/quantity',
                json={"quantity": 5},
                headers=auth_headers)
            results.append(response.status_code)
        
        # Start 3 concurrent updates
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=update_quantity)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should complete without server errors
        assert all(status < 500 for status in results)

    def test_inventory_response_time(self, client, auth_headers):
        """Test inventory endpoint response times"""
        import time
        
        with patch('src.application.use_cases.inventory.get_inventory_content_use_case.GetInventoryContentUseCase.execute'):
            start_time = time.time()
            response = client.get('/api/inventory', headers=auth_headers)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Should respond within 2 seconds
            assert response_time < 2.0
            assert response.status_code == 200

    def test_inventory_memory_usage_large_lists(self, client, auth_headers):
        """Test memory usage with large inventory lists"""
        with patch('src.application.use_cases.inventory.get_ingredients_list_use_case.GetIngredientsListUseCase.execute') as mock_execute:
            # Simulate large inventory
            mock_execute.return_value = {
                "ingredients": [
                    {"name": f"ingredient_{i}", "total_quantity": i}
                    for i in range(1000)
                ]
            }
            
            response = client.get('/api/inventory/ingredients/list', headers=auth_headers)
            
            # Should handle large responses
            assert response.status_code == 200
            assert len(response.get_json()['ingredients']) == 1000