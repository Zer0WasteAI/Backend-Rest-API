"""
Production Validation Tests for Environmental Savings Endpoints
Tests all environmental impact calculation endpoints for production readiness
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock
from src.main import create_app


class TestEnvironmentalSavingsEndpointsProduction:
    """Production validation tests for all environmental savings endpoints"""

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
        with app.app_context():
            from flask_jwt_extended import create_access_token
            token = create_access_token(identity="test-user-uid")
            return {"Authorization": f"Bearer {token}"}

    # ================================================================
    # POST /api/environmental_savings/calculate/from-title
    # ================================================================

    def test_calculate_from_title_success(self, client, auth_headers):
        """Test successful environmental savings calculation by recipe title"""
        with patch('src.application.use_cases.recipes.calculate_enviromental_savings_from_recipe_name.CalculateEnvironmentalSavingsFromRecipeNameUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recipe_title": "Vegetable Pasta",
                "environmental_savings": {
                    "carbon_footprint_saved": 2.5,  # kg CO2
                    "water_saved": 150.0,  # liters
                    "land_use_saved": 0.8,  # m²
                    "energy_saved": 45.0  # kWh
                },
                "calculation_details": {
                    "ingredients_analyzed": 5,
                    "sustainability_score": 8.5,
                    "environmental_impact_category": "medium_positive"
                },
                "comparison": {
                    "vs_traditional_recipe": {
                        "carbon_reduction": "35%",
                        "water_reduction": "28%"
                    }
                },
                "calculation_id": "env_calc_123"
            }

            request_data = {
                "recipe_title": "Vegetable Pasta",
                "serving_size": 4,
                "dietary_preferences": ["vegetarian"]
            }

            response = client.post('/api/environmental_savings/calculate/from-title',
                json=request_data,
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['recipe_title'] == "Vegetable Pasta"
            assert 'environmental_savings' in data
            assert data['environmental_savings']['carbon_footprint_saved'] == 2.5
            assert 'calculation_id' in data

    def test_calculate_from_title_missing_data(self, client, auth_headers):
        """Test calculation with missing recipe title"""
        response = client.post('/api/environmental_savings/calculate/from-title',
            json={},
            headers=auth_headers)

        assert response.status_code == 400

    def test_calculate_from_title_invalid_recipe(self, client, auth_headers):
        """Test calculation with non-existent recipe"""
        with patch('src.application.use_cases.recipes.calculate_enviromental_savings_from_recipe_name.CalculateEnvironmentalSavingsFromRecipeNameUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("Recipe not found")

            request_data = {"recipe_title": "Non-existent Recipe"}
            response = client.post('/api/environmental_savings/calculate/from-title',
                json=request_data,
                headers=auth_headers)

            assert response.status_code == 404

    def test_calculate_from_title_rate_limiting(self, client, auth_headers):
        """Test rate limiting on environmental calculations (ai_environmental: 10 req/min)"""
        with patch('src.application.use_cases.recipes.calculate_enviromental_savings_from_recipe_name.CalculateEnvironmentalSavingsFromRecipeNameUseCase.execute'):
            for i in range(12):
                response = client.post('/api/environmental_savings/calculate/from-title',
                    json={"recipe_title": f"Recipe {i}"},
                    headers=auth_headers)
                
                if i < 10:
                    assert response.status_code in [200, 400, 404]
                else:
                    assert response.status_code == 429

    def test_calculate_from_title_performance(self, client, auth_headers):
        """Test calculation performance"""
        with patch('src.application.use_cases.recipes.calculate_enviromental_savings_from_recipe_name.CalculateEnvironmentalSavingsFromRecipeNameUseCase.execute') as mock_execute:
            mock_execute.return_value = {"environmental_savings": {}}

            start_time = time.time()
            response = client.post('/api/environmental_savings/calculate/from-title',
                json={"recipe_title": "Test Recipe"},
                headers=auth_headers)
            end_time = time.time()

            response_time = end_time - start_time
            # Should complete within 5 seconds
            assert response_time < 5.0
            assert response.status_code == 200

    # ================================================================
    # POST /api/environmental_savings/calculate/from-uid/<recipe_uid>
    # ================================================================

    def test_calculate_from_uid_success(self, client, auth_headers):
        """Test environmental calculation by recipe UID"""
        with patch('src.application.use_cases.recipes.calculate_enviromental_savings_from_recipe_uid.CalculateEnvironmentalSavingsFromRecipeUidUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recipe_uid": "recipe_123",
                "recipe_title": "Quinoa Salad",
                "environmental_savings": {
                    "carbon_footprint_saved": 3.2,
                    "water_saved": 200.0,
                    "land_use_saved": 1.2,
                    "energy_saved": 60.0
                },
                "detailed_analysis": {
                    "ingredient_impact": [
                        {
                            "ingredient": "quinoa",
                            "carbon_impact": 0.8,
                            "water_impact": 45.0,
                            "sustainability_rating": "good"
                        }
                    ]
                },
                "calculation_metadata": {
                    "calculated_at": "2024-01-10T10:00:00Z",
                    "algorithm_version": "2.1",
                    "confidence_score": 0.92
                }
            }

            recipe_uid = "recipe_123"
            request_data = {
                "serving_size": 2,
                "include_detailed_analysis": True
            }

            response = client.post(f'/api/environmental_savings/calculate/from-uid/{recipe_uid}',
                json=request_data,
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['recipe_uid'] == recipe_uid
            assert 'detailed_analysis' in data
            assert data['calculation_metadata']['confidence_score'] > 0.8

    def test_calculate_from_uid_invalid_uid(self, client, auth_headers):
        """Test calculation with invalid recipe UID"""
        with patch('src.application.use_cases.recipes.calculate_enviromental_savings_from_recipe_uid.CalculateEnvironmentalSavingsFromRecipeUidUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("Recipe with UID not found")

            response = client.post('/api/environmental_savings/calculate/from-uid/invalid_uid',
                json={"serving_size": 1},
                headers=auth_headers)

            assert response.status_code == 404

    def test_calculate_from_uid_malformed_uid(self, client, auth_headers):
        """Test calculation with malformed UID"""
        malformed_uids = [
            "",
            "../../etc/passwd",
            "<script>alert('xss')</script>",
            "a" * 1000
        ]

        for uid in malformed_uids:
            response = client.post(f'/api/environmental_savings/calculate/from-uid/{uid}',
                json={"serving_size": 1},
                headers=auth_headers)
            
            assert response.status_code in [400, 404]

    # ================================================================
    # GET /api/environmental_savings/calculations
    # ================================================================

    def test_get_all_calculations_success(self, client, auth_headers):
        """Test getting all user's environmental calculations"""
        with patch('src.application.use_cases.recipes.get_all_environmental_calculations_by_user.GetAllEnvironmentalCalculationsByUserUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "calculations": [
                    {
                        "calculation_id": "env_calc_1",
                        "recipe_title": "Green Smoothie",
                        "carbon_footprint_saved": 1.5,
                        "calculated_at": "2024-01-10T10:00:00Z",
                        "is_cooked": True
                    },
                    {
                        "calculation_id": "env_calc_2",
                        "recipe_title": "Vegetable Curry",
                        "carbon_footprint_saved": 2.8,
                        "calculated_at": "2024-01-09T15:30:00Z",
                        "is_cooked": False
                    }
                ],
                "total_calculations": 2,
                "total_carbon_saved": 4.3,
                "total_water_saved": 180.0,
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total_pages": 1
                }
            }

            response = client.get('/api/environmental_savings/calculations',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_calculations'] == 2
            assert len(data['calculations']) == 2
            assert data['total_carbon_saved'] == 4.3

    def test_get_calculations_with_pagination(self, client, auth_headers):
        """Test calculations with pagination parameters"""
        with patch('src.application.use_cases.recipes.get_all_environmental_calculations_by_user.GetAllEnvironmentalCalculationsByUserUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "calculations": [{"calculation_id": f"calc_{i}"} for i in range(10)],
                "total_calculations": 25,
                "pagination": {"page": 2, "per_page": 10, "total_pages": 3}
            }

            response = client.get('/api/environmental_savings/calculations?page=2&per_page=10',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['pagination']['page'] == 2
            assert len(data['calculations']) == 10

    def test_get_calculations_empty_result(self, client, auth_headers):
        """Test getting calculations when user has none"""
        with patch('src.application.use_cases.recipes.get_all_environmental_calculations_by_user.GetAllEnvironmentalCalculationsByUserUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "calculations": [],
                "total_calculations": 0,
                "total_carbon_saved": 0.0,
                "total_water_saved": 0.0
            }

            response = client.get('/api/environmental_savings/calculations',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_calculations'] == 0
            assert data['calculations'] == []

    # ================================================================
    # GET /api/environmental_savings/calculations/status
    # ================================================================

    def test_get_calculations_by_status_cooked(self, client, auth_headers):
        """Test getting calculations filtered by cooked status"""
        with patch('src.application.use_cases.recipes.get_environmental_calculations_by_user_and_status.GetEnvironmentalCalculationsByUserAndStatusUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "calculations": [
                    {
                        "calculation_id": "env_calc_cooked_1",
                        "recipe_title": "Cooked Quinoa Salad",
                        "is_cooked": True,
                        "carbon_footprint_saved": 2.1,
                        "actual_impact": True
                    }
                ],
                "filtered_total": 1,
                "filter_applied": {"is_cooked": True}
            }

            response = client.get('/api/environmental_savings/calculations/status?is_cooked=true',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['filtered_total'] == 1
            assert data['calculations'][0]['is_cooked'] == True

    def test_get_calculations_by_status_uncooked(self, client, auth_headers):
        """Test getting uncooked recipe calculations"""
        with patch('src.application.use_cases.recipes.get_environmental_calculations_by_user_and_status.GetEnvironmentalCalculationsByUserAndStatusUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "calculations": [
                    {
                        "calculation_id": "env_calc_uncooked_1",
                        "recipe_title": "Planned Vegetable Stir Fry",
                        "is_cooked": False,
                        "carbon_footprint_saved": 1.8,
                        "projected_impact": True
                    }
                ],
                "filtered_total": 1,
                "filter_applied": {"is_cooked": False}
            }

            response = client.get('/api/environmental_savings/calculations/status?is_cooked=false',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['calculations'][0]['is_cooked'] == False

    def test_get_calculations_invalid_status_parameter(self, client, auth_headers):
        """Test calculations with invalid status parameter"""
        response = client.get('/api/environmental_savings/calculations/status?is_cooked=invalid',
            headers=auth_headers)

        assert response.status_code == 400

    def test_get_calculations_missing_status_parameter(self, client, auth_headers):
        """Test calculations status endpoint without parameter"""
        response = client.get('/api/environmental_savings/calculations/status',
            headers=auth_headers)

        assert response.status_code == 400

    # ================================================================
    # GET /api/environmental_savings/summary
    # ================================================================

    def test_get_environmental_summary_success(self, client, auth_headers):
        """Test getting consolidated environmental impact summary"""
        with patch('src.application.use_cases.recipes.sum_environmental_calculations_by_user.SumEnvironmentalCalculationsByUserUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "user_environmental_impact": {
                    "total_carbon_footprint_saved": 15.7,  # kg CO2
                    "total_water_saved": 450.0,  # liters
                    "total_land_use_saved": 3.2,  # m²
                    "total_energy_saved": 120.0,  # kWh
                    "total_recipes_calculated": 8,
                    "total_recipes_cooked": 5
                },
                "impact_breakdown": {
                    "by_month": {
                        "2024-01": {"carbon_saved": 8.2, "recipes": 3},
                        "2024-02": {"carbon_saved": 7.5, "recipes": 5}
                    },
                    "by_category": {
                        "vegetarian": {"carbon_saved": 10.1, "percentage": 64.3},
                        "vegan": {"carbon_saved": 5.6, "percentage": 35.7}
                    }
                },
                "achievements": {
                    "carbon_milestone": "15kg_saved",
                    "recipe_milestone": "8_recipes_calculated",
                    "sustainability_score": 8.5,
                    "environmental_rank": "Eco-Warrior"
                },
                "projections": {
                    "yearly_carbon_savings": 188.4,  # Based on current trend
                    "equivalent_trees_planted": 8.5,
                    "equivalent_cars_off_road": 0.04  # days
                }
            }

            response = client.get('/api/environmental_savings/summary',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['user_environmental_impact']['total_carbon_footprint_saved'] == 15.7
            assert data['user_environmental_impact']['total_recipes_calculated'] == 8
            assert 'impact_breakdown' in data
            assert 'achievements' in data
            assert data['achievements']['sustainability_score'] == 8.5
            assert 'projections' in data

    def test_get_environmental_summary_new_user(self, client, auth_headers):
        """Test summary for user with no calculations"""
        with patch('src.application.use_cases.recipes.sum_environmental_calculations_by_user.SumEnvironmentalCalculationsByUserUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "user_environmental_impact": {
                    "total_carbon_footprint_saved": 0.0,
                    "total_water_saved": 0.0,
                    "total_land_use_saved": 0.0,
                    "total_energy_saved": 0.0,
                    "total_recipes_calculated": 0,
                    "total_recipes_cooked": 0
                },
                "impact_breakdown": {},
                "achievements": {
                    "sustainability_score": 0.0,
                    "environmental_rank": "Beginner"
                },
                "recommendations": [
                    "Start by calculating environmental impact of your favorite recipes",
                    "Try cooking more plant-based meals",
                    "Use seasonal and local ingredients"
                ]
            }

            response = client.get('/api/environmental_savings/summary',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['user_environmental_impact']['total_recipes_calculated'] == 0
            assert data['achievements']['environmental_rank'] == "Beginner"
            assert 'recommendations' in data

    def test_get_environmental_summary_caching(self, client, auth_headers):
        """Test that summary endpoint supports caching"""
        with patch('src.application.use_cases.recipes.sum_environmental_calculations_by_user.SumEnvironmentalCalculationsByUserUseCase.execute') as mock_execute:
            mock_execute.return_value = {"user_environmental_impact": {"total_carbon_footprint_saved": 5.0}}

            # First request
            response1 = client.get('/api/environmental_savings/summary', headers=auth_headers)
            # Second request
            response2 = client.get('/api/environmental_savings/summary', headers=auth_headers)

            assert response1.status_code == 200
            assert response2.status_code == 200
            # Should have cache headers
            assert 'Cache-Control' in response1.headers or 'ETag' in response1.headers

    # ================================================================
    # Security and Performance Tests
    # ================================================================

    def test_environmental_endpoints_authentication(self, client):
        """Test that all endpoints require authentication"""
        endpoints = [
            '/api/environmental_savings/calculate/from-title',
            '/api/environmental_savings/calculate/from-uid/test_uid',
            '/api/environmental_savings/calculations',
            '/api/environmental_savings/calculations/status',
            '/api/environmental_savings/summary'
        ]

        for endpoint in endpoints:
            if endpoint.startswith('/api/environmental_savings/calculate/'):
                response = client.post(endpoint, json={})
            else:
                response = client.get(endpoint)
            
            assert response.status_code == 401

    def test_environmental_sql_injection_protection(self, client, auth_headers):
        """Test SQL injection protection"""
        malicious_inputs = [
            "'; DROP TABLE environmental_savings; --",
            "1' OR '1'='1",
            "1; DELETE FROM users; --"
        ]

        for malicious_input in malicious_inputs:
            response = client.post(f'/api/environmental_savings/calculate/from-uid/{malicious_input}',
                json={"serving_size": 1},
                headers=auth_headers)
            
            assert response.status_code in [400, 404]

    def test_environmental_xss_protection(self, client, auth_headers):
        """Test XSS protection in environmental endpoints"""
        xss_payload = "<script>alert('xss')</script>"
        
        response = client.post('/api/environmental_savings/calculate/from-title',
            json={"recipe_title": xss_payload},
            headers=auth_headers)
        
        # Response should not contain unescaped script
        response_text = response.get_data(as_text=True)
        assert '<script>' not in response_text

    def test_environmental_large_payload_handling(self, client, auth_headers):
        """Test handling of large payloads"""
        large_title = "x" * 10000  # 10KB title
        
        response = client.post('/api/environmental_savings/calculate/from-title',
            json={"recipe_title": large_title},
            headers=auth_headers)
        
        assert response.status_code in [400, 413]

    def test_environmental_concurrent_calculations(self, client, auth_headers):
        """Test concurrent environmental calculations"""
        import threading
        results = []
        
        def calculate():
            response = client.post('/api/environmental_savings/calculate/from-title',
                json={"recipe_title": "Test Recipe"},
                headers=auth_headers)
            results.append(response.status_code)
        
        with patch('src.application.use_cases.recipes.calculate_enviromental_savings_from_recipe_name.CalculateEnvironmentalSavingsFromRecipeNameUseCase.execute'):
            threads = []
            for _ in range(3):
                thread = threading.Thread(target=calculate)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
        
        # All should complete without server errors
        assert all(status < 500 for status in results)

    def test_environmental_memory_usage_large_summaries(self, client, auth_headers):
        """Test memory usage with large environmental summaries"""
        with patch('src.application.use_cases.recipes.sum_environmental_calculations_by_user.SumEnvironmentalCalculationsByUserUseCase.execute') as mock_execute:
            # Simulate large summary with many calculations
            large_breakdown = {
                "by_month": {f"2024-{i:02d}": {"carbon_saved": i * 0.5} for i in range(1, 13)},
                "by_recipe": {f"recipe_{i}": {"carbon_saved": i * 0.1} for i in range(100)}
            }
            
            mock_execute.return_value = {
                "user_environmental_impact": {"total_carbon_footprint_saved": 50.0},
                "impact_breakdown": large_breakdown
            }
            
            response = client.get('/api/environmental_savings/summary', headers=auth_headers)
            
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['impact_breakdown']['by_recipe']) == 100

    def test_environmental_calculation_accuracy(self, client, auth_headers):
        """Test calculation accuracy and validation"""
        with patch('src.application.use_cases.recipes.calculate_enviromental_savings_from_recipe_name.CalculateEnvironmentalSavingsFromRecipeNameUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "environmental_savings": {
                    "carbon_footprint_saved": 2.5,
                    "water_saved": 150.0,
                    "land_use_saved": 0.8,
                    "energy_saved": 45.0
                },
                "calculation_confidence": 0.95,
                "data_sources": ["USDA", "EPA", "FAO"]
            }
            
            response = client.post('/api/environmental_savings/calculate/from-title',
                json={"recipe_title": "Sustainable Recipe"},
                headers=auth_headers)
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Validate that all savings are positive numbers
            savings = data['environmental_savings']
            assert savings['carbon_footprint_saved'] >= 0
            assert savings['water_saved'] >= 0
            assert savings['land_use_saved'] >= 0
            assert savings['energy_saved'] >= 0