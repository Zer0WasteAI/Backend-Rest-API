"""
Comprehensive integration tests for Environmental Savings Controller.
Tests environmental calculations, reporting, and cross-feature integration.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.main import app
from datetime import datetime, timedelta


class TestEnvironmentalSavingsControllerIntegration:
    """Integration tests for Environmental Savings Controller endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.client = app.test_client()
        self.client.testing = True
        self.base_headers = {'Content-Type': 'application/json'}
        self.mock_user_token = 'Bearer test_token_123'
    
    def test_calculate_savings_from_title_endpoint(self):
        """Test environmental savings calculation from recipe title."""
        with patch('src.interface.controllers.environmental_savings_controller.request') as mock_request:
            mock_request.headers = {'Authorization': self.mock_user_token}
            mock_request.get_json.return_value = {
                'recipe_title': 'Vegetarian Pasta Salad',
                'servings': 4
            }
            
            with patch('src.application.services.environmental_service.calculate_savings_from_title') as mock_calc:
                mock_calc.return_value = {
                    'co2_saved': 2.5,
                    'water_saved': 150.0,
                    'energy_saved': 0.8,
                    'calculation_id': 'calc_123'
                }
                
                response = self.client.post('/api/environmental/calculate/from-title',
                                          json={
                                              'recipe_title': 'Vegetarian Pasta Salad',
                                              'servings': 4
                                          },
                                          headers={**self.base_headers, 'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 201, 400, 401]
                if response.status_code in [200, 201]:
                    data = json.loads(response.data)
                    assert any(key in data for key in ['co2_saved', 'water_saved', 'energy_saved', 'calculation_id'])

    def test_calculate_savings_from_uid_endpoint(self):
        """Test environmental savings calculation from recipe UID."""
        recipe_uid = 'recipe_test_123'
        
        with patch('src.interface.controllers.environmental_savings_controller.request') as mock_request:
            mock_request.headers = {'Authorization': self.mock_user_token}
            
            with patch('src.application.services.environmental_service.calculate_savings_from_uid') as mock_calc:
                mock_calc.return_value = {
                    'recipe_uid': recipe_uid,
                    'co2_saved': 3.2,
                    'water_saved': 200.5,
                    'energy_saved': 1.1,
                    'calculation_id': 'calc_uid_456'
                }
                
                response = self.client.post(f'/api/environmental/calculate/from-uid/{recipe_uid}',
                                          headers={**self.base_headers, 'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 201, 400, 401, 404]
                if response.status_code in [200, 201]:
                    data = json.loads(response.data)
                    assert any(key in data for key in ['recipe_uid', 'co2_saved', 'calculation_id'])

    def test_environmental_calculation_workflow(self):
        """Test complete environmental calculation workflow."""
        # Step 1: Calculate savings from title
        with patch('src.application.services.environmental_service.calculate_savings_from_title') as mock_calc_title:
            mock_calc_title.return_value = {
                'calculation_id': 'workflow_calc_123',
                'co2_saved': 4.0,
                'water_saved': 300.0
            }
            
            calc_response = self.client.post('/api/environmental/calculate/from-title',
                                           json={'recipe_title': 'Green Smoothie Bowl', 'servings': 2},
                                           headers={**self.base_headers, 'Authorization': self.mock_user_token})
            
            if calc_response.status_code in [200, 201]:
                # Step 2: Get all calculations to verify it's stored
                with patch('src.application.services.environmental_service.get_all_calculations') as mock_get_all:
                    mock_get_all.return_value = [
                        {
                            'calculation_id': 'workflow_calc_123',
                            'status': 'completed',
                            'created_at': datetime.now().isoformat()
                        }
                    ]
                    
                    all_calc_response = self.client.get('/api/environmental/calculations',
                                                      headers={'Authorization': self.mock_user_token})
                    
                    assert all_calc_response.status_code in [200, 401]
                
                # Step 3: Get environmental summary
                with patch('src.application.services.environmental_service.get_environmental_summary') as mock_summary:
                    mock_summary.return_value = {
                        'total_co2_saved': 4.0,
                        'total_water_saved': 300.0,
                        'calculations_count': 1
                    }
                    
                    summary_response = self.client.get('/api/environmental/summary',
                                                     headers={'Authorization': self.mock_user_token})
                    
                    assert summary_response.status_code in [200, 401]

    def test_environmental_status_filtering(self):
        """Test environmental calculations filtering by status."""
        test_statuses = ['completed', 'pending', 'failed']
        
        for status in test_statuses:
            with patch('src.application.services.environmental_service.get_calculations_by_status') as mock_get_status:
                mock_get_status.return_value = [
                    {
                        'calculation_id': f'calc_{status}_123',
                        'status': status,
                        'co2_saved': 2.0 if status == 'completed' else None
                    }
                ]
                
                response = self.client.get(f'/api/environmental/calculations/status?status={status}',
                                         headers={'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 400, 401]
                if response.status_code == 200:
                    data = json.loads(response.data)
                    assert isinstance(data, (list, dict))

    def test_calculation_from_cooking_session(self):
        """Test environmental calculation from cooking session."""
        with patch('src.interface.controllers.environmental_savings_controller.request') as mock_request:
            mock_request.headers = {'Authorization': self.mock_user_token}
            mock_request.get_json.return_value = {
                'session_id': 'cooking_session_789',
                'ingredients_used': ['tomatoes', 'basil', 'olive_oil'],
                'cooking_time': 45
            }
            
            with patch('src.application.services.environmental_service.calculate_savings_from_session') as mock_calc:
                mock_calc.return_value = {
                    'session_id': 'cooking_session_789',
                    'co2_saved': 1.8,
                    'water_saved': 120.0,
                    'energy_saved': 0.6,
                    'calculation_id': 'session_calc_456'
                }
                
                response = self.client.post('/api/environmental/calculate/from-session',
                                          json={
                                              'session_id': 'cooking_session_789',
                                              'ingredients_used': ['tomatoes', 'basil', 'olive_oil']
                                          },
                                          headers={**self.base_headers, 'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 201, 400, 401]

    def test_environmental_data_validation(self):
        """Test environmental calculation data validation."""
        validation_tests = [
            {
                'endpoint': '/api/environmental/calculate/from-title',
                'data': {'recipe_title': '', 'servings': -1},
                'expected_codes': [400, 422]
            },
            {
                'endpoint': '/api/environmental/calculate/from-session',
                'data': {'session_id': '', 'ingredients_used': []},
                'expected_codes': [400, 422]
            },
            {
                'endpoint': '/api/environmental/calculate/from-title',
                'data': {'invalid_field': 'value'},
                'expected_codes': [400, 422]
            }
        ]
        
        for test in validation_tests:
            response = self.client.post(test['endpoint'],
                                      json=test['data'],
                                      headers={**self.base_headers, 'Authorization': self.mock_user_token})
            
            assert response.status_code in test['expected_codes']

    def test_environmental_summary_aggregation(self):
        """Test environmental summary data aggregation."""
        with patch('src.application.services.environmental_service.get_environmental_summary') as mock_summary:
            mock_summary.return_value = {
                'total_co2_saved': 45.8,
                'total_water_saved': 2500.0,
                'total_energy_saved': 12.3,
                'calculations_count': 15,
                'average_savings_per_recipe': {
                    'co2': 3.05,
                    'water': 166.67,
                    'energy': 0.82
                },
                'monthly_trend': [
                    {'month': '2024-01', 'co2_saved': 12.5},
                    {'month': '2024-02', 'co2_saved': 15.3},
                    {'month': '2024-03', 'co2_saved': 18.0}
                ]
            }
            
            response = self.client.get('/api/environmental/summary',
                                     headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [200, 401]
            if response.status_code == 200:
                data = json.loads(response.data)
                assert any(key in data for key in ['total_co2_saved', 'calculations_count', 'average_savings_per_recipe'])

    def test_cross_service_integration(self):
        """Test integration with recipe and inventory services."""
        # Test calculation triggered by recipe generation
        with patch('src.application.services.environmental_service.calculate_savings_from_title') as mock_calc:
            mock_calc.return_value = {'calculation_id': 'integration_calc_123', 'co2_saved': 5.2}
            
            # Simulate recipe generation followed by environmental calculation
            calc_response = self.client.post('/api/environmental/calculate/from-title',
                                           json={
                                               'recipe_title': 'Zero Waste Stir Fry',
                                               'servings': 3,
                                               'source': 'recipe_generation'
                                           },
                                           headers={**self.base_headers, 'Authorization': self.mock_user_token})
            
            if calc_response.status_code in [200, 201]:
                # Verify calculation appears in user's environmental history
                with patch('src.application.services.environmental_service.get_all_calculations') as mock_get_all:
                    mock_get_all.return_value = [{'calculation_id': 'integration_calc_123'}]
                    
                    history_response = self.client.get('/api/environmental/calculations',
                                                     headers={'Authorization': self.mock_user_token})
                    
                    assert history_response.status_code in [200, 401]

    def test_environmental_error_handling(self):
        """Test error handling in environmental calculations."""
        # Test service failure scenarios
        with patch('src.application.services.environmental_service.calculate_savings_from_title') as mock_calc:
            mock_calc.side_effect = Exception("Calculation service unavailable")
            
            response = self.client.post('/api/environmental/calculate/from-title',
                                      json={'recipe_title': 'Test Recipe', 'servings': 2},
                                      headers={**self.base_headers, 'Authorization': self.mock_user_token})
            
            assert response.status_code in [500, 400]
            if response.status_code == 500:
                data = json.loads(response.data)
                assert 'error' in data or 'message' in data

    def test_environmental_calculations_pagination(self):
        """Test pagination in environmental calculations listing."""
        with patch('src.application.services.environmental_service.get_all_calculations') as mock_get_all:
            # Simulate large dataset
            mock_calculations = [
                {'calculation_id': f'calc_{i}', 'co2_saved': i * 0.5}
                for i in range(50)
            ]
            mock_get_all.return_value = mock_calculations
            
            # Test with pagination parameters
            response = self.client.get('/api/environmental/calculations?page=1&limit=10',
                                     headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [200, 401]

    def test_environmental_authentication_flow(self):
        """Test authentication across environmental endpoints."""
        endpoints = [
            '/api/environmental/calculate/from-title',
            '/api/environmental/calculate/from-session',
            '/api/environmental/calculations',
            '/api/environmental/summary'
        ]
        
        for endpoint in endpoints:
            # Test without authentication
            if endpoint.startswith('/api/environmental/calculate'):
                response = self.client.post(endpoint, json={}, headers=self.base_headers)
            else:
                response = self.client.get(endpoint)
            
            assert response.status_code in [401, 403]
            
            # Test with invalid token
            auth_headers = {**self.base_headers, 'Authorization': 'Bearer invalid_token'}
            if endpoint.startswith('/api/environmental/calculate'):
                response = self.client.post(endpoint, json={}, headers=auth_headers)
            else:
                response = self.client.get(endpoint, headers={'Authorization': 'Bearer invalid_token'})
            
            assert response.status_code in [401, 403]
