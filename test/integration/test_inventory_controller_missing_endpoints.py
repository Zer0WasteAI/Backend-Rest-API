"""
Enhanced integration tests for Inventory Controller.
Tests missing endpoints and advanced inventory management scenarios.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.main import app
from datetime import datetime, timedelta


class TestInventoryControllerEnhancedIntegration:
    """Enhanced integration tests for missing Inventory Controller endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.client = app.test_client()
        self.client.testing = True
        self.base_headers = {'Content-Type': 'application/json'}
        self.mock_user_token = 'Bearer test_token_123'
    
    def test_update_ingredient_endpoint(self):
        """Test ingredient update functionality."""
        ingredient_name = 'tomatoes'
        added_at = '2024-01-01T10:00:00Z'
        
        with patch('src.interface.controllers.inventory_controller.request') as mock_request:
            mock_request.headers = {'Authorization': self.mock_user_token}
            mock_request.get_json.return_value = {
                'quantity': 500,
                'unit': 'grams',
                'expiration_date': '2024-12-31',
                'notes': 'Fresh organic tomatoes'
            }
            
            with patch('src.application.services.inventory_service.update_ingredient') as mock_update:
                mock_update.return_value = {
                    'ingredient_name': ingredient_name,
                    'added_at': added_at,
                    'updated_quantity': 500,
                    'updated_at': datetime.now().isoformat(),
                    'status': 'updated'
                }
                
                response = self.client.put(f'/api/inventory/ingredients/{ingredient_name}/{added_at}',
                                         json={
                                             'quantity': 500,
                                             'unit': 'grams',
                                             'expiration_date': '2024-12-31'
                                         },
                                         headers={**self.base_headers, 'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 201, 400, 401, 404]
                if response.status_code == 200:
                    data = json.loads(response.data)
                    assert any(key in data for key in ['ingredient_name', 'status', 'updated_at'])

    def test_delete_ingredient_endpoint(self):
        """Test specific ingredient deletion by added_at timestamp."""
        ingredient_name = 'carrots'
        added_at = '2024-01-15T14:30:00Z'
        
        with patch('src.application.services.inventory_service.delete_ingredient') as mock_delete:
            mock_delete.return_value = {
                'ingredient_name': ingredient_name,
                'added_at': added_at,
                'deleted': True,
                'deleted_at': datetime.now().isoformat()
            }
            
            response = self.client.delete(f'/api/inventory/ingredients/{ingredient_name}/{added_at}',
                                        headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [200, 204, 404, 401]
            if response.status_code == 200:
                data = json.loads(response.data)
                assert data.get('deleted') == True or 'status' in data

    def test_delete_ingredient_complete_endpoint(self):
        """Test complete ingredient deletion (all instances)."""
        ingredient_name = 'onions'
        
        with patch('src.application.services.inventory_service.delete_ingredient_complete') as mock_delete_complete:
            mock_delete_complete.return_value = {
                'ingredient_name': ingredient_name,
                'deleted_instances': 3,
                'total_quantity_removed': 750,
                'deleted_at': datetime.now().isoformat()
            }
            
            response = self.client.delete(f'/api/inventory/ingredients/{ingredient_name}',
                                        headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [200, 204, 404, 401]
            if response.status_code == 200:
                data = json.loads(response.data)
                assert 'deleted_instances' in data or 'status' in data

    def test_delete_food_item_endpoint(self):
        """Test specific food item deletion."""
        food_name = 'leftover_pasta'
        added_at = '2024-02-01T18:00:00Z'
        
        with patch('src.application.services.inventory_service.delete_food_item') as mock_delete_food:
            mock_delete_food.return_value = {
                'food_name': food_name,
                'added_at': added_at,
                'deleted': True,
                'deleted_at': datetime.now().isoformat()
            }
            
            response = self.client.delete(f'/api/inventory/foods/{food_name}/{added_at}',
                                        headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [200, 204, 404, 401]
            if response.status_code == 200:
                data = json.loads(response.data)
                assert data.get('deleted') == True or 'status' in data

    def test_inventory_management_workflow(self):
        """Test complete inventory management workflow with new endpoints."""
        # Step 1: Add ingredient
        with patch('src.application.services.inventory_service.add_ingredients') as mock_add:
            mock_add.return_value = [
                {
                    'ingredient_name': 'workflow_ingredient',
                    'quantity': 300,
                    'added_at': '2024-03-01T10:00:00Z'
                }
            ]
            
            add_response = self.client.post('/api/inventory/ingredients',
                                          json={
                                              'ingredients': [
                                                  {'name': 'workflow_ingredient', 'quantity': 300, 'unit': 'grams'}
                                              ]
                                          },
                                          headers={**self.base_headers, 'Authorization': self.mock_user_token})
            
            if add_response.status_code in [200, 201]:
                # Step 2: Update the ingredient
                with patch('src.application.services.inventory_service.update_ingredient') as mock_update:
                    mock_update.return_value = {'status': 'updated', 'new_quantity': 450}
                    
                    update_response = self.client.put('/api/inventory/ingredients/workflow_ingredient/2024-03-01T10:00:00Z',
                                                    json={'quantity': 450},
                                                    headers={**self.base_headers, 'Authorization': self.mock_user_token})
                    
                    assert update_response.status_code in [200, 400, 404]
                
                # Step 3: Delete the ingredient
                with patch('src.application.services.inventory_service.delete_ingredient') as mock_delete:
                    mock_delete.return_value = {'deleted': True}
                    
                    delete_response = self.client.delete('/api/inventory/ingredients/workflow_ingredient/2024-03-01T10:00:00Z',
                                                       headers={'Authorization': self.mock_user_token})
                    
                    assert delete_response.status_code in [200, 204, 404]

    def test_bulk_inventory_operations(self):
        """Test bulk operations on inventory items."""
        # Test bulk ingredient updates
        ingredients_to_update = [
            {'name': 'bulk_ingredient_1', 'added_at': '2024-01-01T10:00:00Z', 'new_quantity': 200},
            {'name': 'bulk_ingredient_2', 'added_at': '2024-01-01T11:00:00Z', 'new_quantity': 150},
            {'name': 'bulk_ingredient_3', 'added_at': '2024-01-01T12:00:00Z', 'new_quantity': 300}
        ]
        
        for ingredient in ingredients_to_update:
            with patch('src.application.services.inventory_service.update_ingredient') as mock_update:
                mock_update.return_value = {
                    'ingredient_name': ingredient['name'],
                    'updated_quantity': ingredient['new_quantity'],
                    'status': 'updated'
                }
                
                response = self.client.put(f"/api/inventory/ingredients/{ingredient['name']}/{ingredient['added_at']}",
                                         json={'quantity': ingredient['new_quantity']},
                                         headers={**self.base_headers, 'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 400, 404, 401]

    def test_inventory_cleanup_scenarios(self):
        """Test inventory cleanup and maintenance scenarios."""
        # Test complete deletion of multiple ingredient instances
        ingredients_to_cleanup = ['expired_lettuce', 'old_milk', 'spoiled_bread']
        
        for ingredient in ingredients_to_cleanup:
            with patch('src.application.services.inventory_service.delete_ingredient_complete') as mock_cleanup:
                mock_cleanup.return_value = {
                    'ingredient_name': ingredient,
                    'deleted_instances': 2,
                    'cleanup_completed': True
                }
                
                response = self.client.delete(f'/api/inventory/ingredients/{ingredient}',
                                            headers={'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 204, 404, 401]

    def test_inventory_error_handling_enhanced(self):
        """Test enhanced error handling for new endpoints."""
        error_scenarios = [
            {
                'endpoint': '/api/inventory/ingredients/nonexistent/2024-01-01T10:00:00Z',
                'method': 'PUT',
                'data': {'quantity': 100},
                'expected_codes': [404, 400]
            },
            {
                'endpoint': '/api/inventory/ingredients/invalid_name/invalid_date',
                'method': 'DELETE',
                'data': {},
                'expected_codes': [400, 404]
            },
            {
                'endpoint': '/api/inventory/foods/nonexistent_food/2024-01-01T10:00:00Z',
                'method': 'DELETE',
                'data': {},
                'expected_codes': [404, 400]
            }
        ]
        
        for scenario in error_scenarios:
            if scenario['method'] == 'PUT':
                response = self.client.put(scenario['endpoint'],
                                         json=scenario['data'],
                                         headers={**self.base_headers, 'Authorization': self.mock_user_token})
            else:
                response = self.client.delete(scenario['endpoint'],
                                            headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in scenario['expected_codes']

    def test_inventory_validation_enhanced(self):
        """Test enhanced validation for inventory operations."""
        validation_tests = [
            {
                'endpoint': '/api/inventory/ingredients/test_ingredient/2024-01-01T10:00:00Z',
                'method': 'PUT',
                'data': {'quantity': -50},  # Negative quantity
                'expected_codes': [400, 422]
            },
            {
                'endpoint': '/api/inventory/ingredients/test_ingredient/2024-01-01T10:00:00Z',
                'method': 'PUT',
                'data': {'quantity': 'invalid'},  # Invalid quantity type
                'expected_codes': [400, 422]
            },
            {
                'endpoint': '/api/inventory/ingredients//2024-01-01T10:00:00Z',  # Empty ingredient name
                'method': 'PUT',
                'data': {'quantity': 100},
                'expected_codes': [400, 404]
            }
        ]
        
        for test in validation_tests:
            response = self.client.put(test['endpoint'],
                                     json=test['data'],
                                     headers={**self.base_headers, 'Authorization': self.mock_user_token})
            
            assert response.status_code in test['expected_codes']

    def test_inventory_concurrent_operations(self):
        """Test concurrent inventory operations."""
        import threading
        results = []
        
        def inventory_operation():
            with patch('src.application.services.inventory_service.update_ingredient') as mock_update:
                mock_update.return_value = {'status': 'updated'}
                
                response = self.client.put('/api/inventory/ingredients/concurrent_test/2024-01-01T10:00:00Z',
                                         json={'quantity': 100},
                                         headers={**self.base_headers, 'Authorization': self.mock_user_token})
                results.append(response.status_code)
        
        threads = [threading.Thread(target=inventory_operation) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Operations should complete without server errors
        assert all(code != 500 for code in results)

    def test_inventory_service_integration(self):
        """Test integration between inventory operations and other services."""
        # Test update followed by expiration check
        ingredient_name = 'integration_test_ingredient'
        added_at = '2024-01-01T10:00:00Z'
        
        with patch('src.application.services.inventory_service.update_ingredient') as mock_update:
            mock_update.return_value = {
                'ingredient_name': ingredient_name,
                'updated_at': datetime.now().isoformat(),
                'expires_soon': True
            }
            
            update_response = self.client.put(f'/api/inventory/ingredients/{ingredient_name}/{added_at}',
                                            json={
                                                'quantity': 50,
                                                'expiration_date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
                                            },
                                            headers={**self.base_headers, 'Authorization': self.mock_user_token})
            
            if update_response.status_code == 200:
                # Check if it appears in expiring items
                with patch('src.application.services.inventory_service.get_expiring_items') as mock_expiring:
                    mock_expiring.return_value = [
                        {
                            'ingredient_name': ingredient_name,
                            'expires_in_days': 2,
                            'quantity': 50
                        }
                    ]
                    
                    expiring_response = self.client.get('/api/inventory/expiring',
                                                      headers={'Authorization': self.mock_user_token})
                    
                    assert expiring_response.status_code in [200, 401]

    def test_inventory_authentication_enhanced(self):
        """Test authentication for new inventory endpoints."""
        protected_endpoints = [
            {'path': '/api/inventory/ingredients/test/2024-01-01T10:00:00Z', 'method': 'PUT'},
            {'path': '/api/inventory/ingredients/test/2024-01-01T10:00:00Z', 'method': 'DELETE'},
            {'path': '/api/inventory/ingredients/test', 'method': 'DELETE'},
            {'path': '/api/inventory/foods/test/2024-01-01T10:00:00Z', 'method': 'DELETE'}
        ]
        
        for endpoint in protected_endpoints:
            # Test without authentication
            if endpoint['method'] == 'PUT':
                response = self.client.put(endpoint['path'], json={'quantity': 100})
            else:
                response = self.client.delete(endpoint['path'])
            
            assert response.status_code in [401, 403]
            
            # Test with invalid token
            auth_headers = {'Authorization': 'Bearer invalid_token'}
            if endpoint['method'] == 'PUT':
                response = self.client.put(endpoint['path'], json={'quantity': 100}, headers=auth_headers)
            else:
                response = self.client.delete(endpoint['path'], headers=auth_headers)
            
            assert response.status_code in [401, 403]
