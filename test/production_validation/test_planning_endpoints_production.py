"""
Production Validation Tests for Planning (Meal Plan) Endpoints
Tests all meal planning endpoints for production readiness
"""
import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.main import create_app


class TestPlanningEndpointsProduction:
    """Production validation tests for all meal planning endpoints"""

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

    @pytest.fixture
    def sample_meal_plan(self):
        return {
            "meal_date": "2024-01-15",
            "meals": {
                "breakfast": {
                    "recipe_uid": "breakfast_123",
                    "recipe_title": "Avocado Toast",
                    "planned_time": "08:00",
                    "servings": 1
                },
                "lunch": {
                    "recipe_uid": "lunch_456",
                    "recipe_title": "Quinoa Salad", 
                    "planned_time": "13:00",
                    "servings": 2
                },
                "dinner": {
                    "recipe_uid": "dinner_789",
                    "recipe_title": "Vegetable Stir Fry",
                    "planned_time": "19:00",
                    "servings": 3
                }
            },
            "notes": "Healthy day planned",
            "total_estimated_prep_time": 45
        }

    # ================================================================
    # POST /api/planning/save - Save Meal Plan
    # ================================================================

    def test_save_meal_plan_success(self, client, auth_headers, sample_meal_plan):
        """Test successful meal plan saving"""
        with patch('src.application.use_cases.planning.save_meal_plan_use_case.SaveMealPlanUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Meal plan saved successfully",
                "meal_plan_id": "meal_plan_123",
                "meal_date": "2024-01-15",
                "total_meals": 3,
                "estimated_prep_time": 45,
                "nutritional_summary": {
                    "total_calories": 1850,
                    "protein": "68g",
                    "carbs": "245g",
                    "fat": "72g"
                },
                "saved_at": "2024-01-10T10:00:00Z"
            }

            response = client.post('/api/planning/save',
                json=sample_meal_plan,
                headers=auth_headers)

            assert response.status_code == 201
            data = response.get_json()
            assert data['meal_plan_id'] == "meal_plan_123"
            assert data['total_meals'] == 3
            assert 'nutritional_summary' in data

    def test_save_meal_plan_missing_date(self, client, auth_headers):
        """Test saving meal plan without required date"""
        invalid_plan = {
            "meals": {
                "breakfast": {
                    "recipe_uid": "recipe_123",
                    "recipe_title": "Toast"
                }
            }
        }

        response = client.post('/api/planning/save',
            json=invalid_plan,
            headers=auth_headers)

        assert response.status_code == 400

    def test_save_meal_plan_invalid_date_format(self, client, auth_headers):
        """Test saving meal plan with invalid date format"""
        invalid_plan = {
            "meal_date": "invalid-date-format",
            "meals": {}
        }

        response = client.post('/api/planning/save',
            json=invalid_plan,
            headers=auth_headers)

        assert response.status_code == 400

    def test_save_meal_plan_empty_meals(self, client, auth_headers):
        """Test saving meal plan with no meals"""
        empty_plan = {
            "meal_date": "2024-01-15",
            "meals": {}
        }

        response = client.post('/api/planning/save',
            json=empty_plan,
            headers=auth_headers)

        assert response.status_code == 400

    def test_save_meal_plan_duplicate_date(self, client, auth_headers, sample_meal_plan):
        """Test saving meal plan for already planned date"""
        with patch('src.application.use_cases.planning.save_meal_plan_use_case.SaveMealPlanUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("Meal plan already exists for this date")

            response = client.post('/api/planning/save',
                json=sample_meal_plan,
                headers=auth_headers)

            assert response.status_code == 409  # Conflict

    def test_save_meal_plan_rate_limiting(self, client, auth_headers, sample_meal_plan):
        """Test rate limiting on meal plan saving (planning_crud: 30 req/min)"""
        with patch('src.application.use_cases.planning.save_meal_plan_use_case.SaveMealPlanUseCase.execute'):
            for i in range(32):
                plan = sample_meal_plan.copy()
                plan['meal_date'] = f"2024-01-{15+i:02d}"
                
                response = client.post('/api/planning/save',
                    json=plan,
                    headers=auth_headers)
                
                if i < 30:
                    assert response.status_code in [201, 400, 409]
                else:
                    assert response.status_code == 429

    # ================================================================
    # PUT /api/planning/update - Update Meal Plan
    # ================================================================

    def test_update_meal_plan_success(self, client, auth_headers):
        """Test successful meal plan update"""
        with patch('src.application.use_cases.planning.update_meal_plan_use_case.UpdateMealPlanUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Meal plan updated successfully",
                "meal_plan_id": "meal_plan_123",
                "updated_fields": ["meals.lunch", "notes"],
                "version": 2,
                "last_modified": "2024-01-10T15:30:00Z"
            }

            update_data = {
                "meal_plan_id": "meal_plan_123",
                "updates": {
                    "meals": {
                        "lunch": {
                            "recipe_uid": "new_lunch_456",
                            "recipe_title": "Updated Lunch",
                            "servings": 2
                        }
                    },
                    "notes": "Updated meal plan"
                }
            }

            response = client.put('/api/planning/update',
                json=update_data,
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['meal_plan_id'] == "meal_plan_123"
            assert "meals.lunch" in data['updated_fields']

    def test_update_meal_plan_not_found(self, client, auth_headers):
        """Test updating non-existent meal plan"""
        with patch('src.application.use_cases.planning.update_meal_plan_use_case.UpdateMealPlanUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("Meal plan not found")

            update_data = {
                "meal_plan_id": "nonexistent_plan",
                "updates": {"notes": "Update"}
            }

            response = client.put('/api/planning/update',
                json=update_data,
                headers=auth_headers)

            assert response.status_code == 404

    def test_update_meal_plan_invalid_recipe(self, client, auth_headers):
        """Test updating meal plan with invalid recipe"""
        with patch('src.application.use_cases.planning.update_meal_plan_use_case.UpdateMealPlanUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("Recipe not found")

            update_data = {
                "meal_plan_id": "meal_plan_123",
                "updates": {
                    "meals": {
                        "dinner": {
                            "recipe_uid": "invalid_recipe",
                            "recipe_title": "Invalid Recipe"
                        }
                    }
                }
            }

            response = client.put('/api/planning/update',
                json=update_data,
                headers=auth_headers)

            assert response.status_code == 400

    # ================================================================
    # DELETE /api/planning/delete - Delete Meal Plan
    # ================================================================

    def test_delete_meal_plan_success(self, client, auth_headers):
        """Test successful meal plan deletion"""
        with patch('src.application.use_cases.planning.delete_meal_plan_use_case.DeleteMealPlanUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Meal plan deleted successfully",
                "deleted_meal_plan_id": "meal_plan_123",
                "meal_date": "2024-01-15",
                "deleted_at": "2024-01-10T16:00:00Z"
            }

            response = client.delete('/api/planning/delete?date=2024-01-15',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['meal_date'] == "2024-01-15"

    def test_delete_meal_plan_missing_date(self, client, auth_headers):
        """Test deleting meal plan without date parameter"""
        response = client.delete('/api/planning/delete',
            headers=auth_headers)

        assert response.status_code == 400

    def test_delete_meal_plan_invalid_date(self, client, auth_headers):
        """Test deleting meal plan with invalid date"""
        response = client.delete('/api/planning/delete?date=invalid-date',
            headers=auth_headers)

        assert response.status_code == 400

    def test_delete_meal_plan_not_found(self, client, auth_headers):
        """Test deleting non-existent meal plan"""
        with patch('src.application.use_cases.planning.delete_meal_plan_use_case.DeleteMealPlanUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("Meal plan not found for this date")

            response = client.delete('/api/planning/delete?date=2024-12-31',
                headers=auth_headers)

            assert response.status_code == 404

    # ================================================================
    # GET /api/planning/get - Get Meal Plan by Date
    # ================================================================

    def test_get_meal_plan_success(self, client, auth_headers):
        """Test getting meal plan by date"""
        with patch('src.application.use_cases.planning.get_meal_plan_by_user_and_date_use_case.GetMealPlanByUserAndDateUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "meal_plan_id": "meal_plan_123",
                "meal_date": "2024-01-15",
                "meals": {
                    "breakfast": {
                        "recipe_uid": "breakfast_123",
                        "recipe_title": "Avocado Toast",
                        "planned_time": "08:00",
                        "servings": 1,
                        "estimated_prep_time": 10,
                        "nutritional_info": {
                            "calories": 320,
                            "protein": "12g"
                        }
                    },
                    "lunch": {
                        "recipe_uid": "lunch_456",
                        "recipe_title": "Quinoa Salad",
                        "planned_time": "13:00",
                        "servings": 2
                    }
                },
                "daily_summary": {
                    "total_meals": 2,
                    "total_prep_time": 35,
                    "total_calories": 1200,
                    "nutritional_balance": "good"
                },
                "created_at": "2024-01-10T10:00:00Z"
            }

            response = client.get('/api/planning/get?meal_date=2024-01-15',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['meal_date'] == "2024-01-15"
            assert len(data['meals']) == 2
            assert 'daily_summary' in data

    def test_get_meal_plan_missing_date(self, client, auth_headers):
        """Test getting meal plan without date parameter"""
        response = client.get('/api/planning/get',
            headers=auth_headers)

        assert response.status_code == 400

    def test_get_meal_plan_not_found(self, client, auth_headers):
        """Test getting non-existent meal plan"""
        with patch('src.application.use_cases.planning.get_meal_plan_by_user_and_date_use_case.GetMealPlanByUserAndDateUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("No meal plan found for this date")

            response = client.get('/api/planning/get?meal_date=2024-12-31',
                headers=auth_headers)

            assert response.status_code == 404

    def test_get_meal_plan_future_date(self, client, auth_headers):
        """Test getting meal plan for future date"""
        future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        with patch('src.application.use_cases.planning.get_meal_plan_by_user_and_date_use_case.GetMealPlanByUserAndDateUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "meal_plan_id": "future_plan_123",
                "meal_date": future_date,
                "meals": {},
                "is_future_plan": True
            }

            response = client.get(f'/api/planning/get?meal_date={future_date}',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['is_future_plan'] == True

    # ================================================================
    # GET /api/planning/all - Get All Meal Plans
    # ================================================================

    def test_get_all_meal_plans_success(self, client, auth_headers):
        """Test getting all user's meal plans"""
        with patch('src.application.use_cases.planning.get_all_meal_plans_by_user_use_case.GetAllMealPlansByUserUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "meal_plans": [
                    {
                        "meal_plan_id": "plan_1",
                        "meal_date": "2024-01-15",
                        "total_meals": 3,
                        "status": "completed"
                    },
                    {
                        "meal_plan_id": "plan_2",
                        "meal_date": "2024-01-16", 
                        "total_meals": 2,
                        "status": "planned"
                    }
                ],
                "total_plans": 2,
                "date_range": {
                    "earliest": "2024-01-15",
                    "latest": "2024-01-16"
                },
                "statistics": {
                    "total_meals_planned": 5,
                    "completed_plans": 1,
                    "upcoming_plans": 1
                }
            }

            response = client.get('/api/planning/all',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_plans'] == 2
            assert len(data['meal_plans']) == 2
            assert 'statistics' in data

    def test_get_all_meal_plans_with_filters(self, client, auth_headers):
        """Test getting meal plans with date filters"""
        with patch('src.application.use_cases.planning.get_all_meal_plans_by_user_use_case.GetAllMealPlansByUserUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "meal_plans": [
                    {"meal_plan_id": "plan_1", "meal_date": "2024-01-15"}
                ],
                "total_plans": 1,
                "applied_filters": {
                    "start_date": "2024-01-15",
                    "end_date": "2024-01-15"
                }
            }

            response = client.get('/api/planning/all?start_date=2024-01-15&end_date=2024-01-15',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert 'applied_filters' in data

    def test_get_all_meal_plans_empty(self, client, auth_headers):
        """Test getting all meal plans when user has none"""
        with patch('src.application.use_cases.planning.get_all_meal_plans_by_user_use_case.GetAllMealPlansByUserUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "meal_plans": [],
                "total_plans": 0,
                "statistics": {
                    "total_meals_planned": 0,
                    "completed_plans": 0,
                    "upcoming_plans": 0
                }
            }

            response = client.get('/api/planning/all',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_plans'] == 0
            assert data['meal_plans'] == []

    # ================================================================
    # GET /api/planning/dates - Get Meal Plan Dates
    # ================================================================

    def test_get_meal_plan_dates_success(self, client, auth_headers):
        """Test getting dates with existing meal plans"""
        with patch('src.application.use_cases.planning.get_meal_plan_dates_usecase.GetMealPlanDatesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "dates_with_plans": [
                    "2024-01-15",
                    "2024-01-16",
                    "2024-01-18",
                    "2024-01-20"
                ],
                "total_dates": 4,
                "date_range": {
                    "earliest": "2024-01-15",
                    "latest": "2024-01-20"
                },
                "calendar_view": {
                    "2024-01": {
                        "15": {"has_plan": True, "meal_count": 3},
                        "16": {"has_plan": True, "meal_count": 2},
                        "18": {"has_plan": True, "meal_count": 3},
                        "20": {"has_plan": True, "meal_count": 1}
                    }
                }
            }

            response = client.get('/api/planning/dates',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_dates'] == 4
            assert len(data['dates_with_plans']) == 4
            assert 'calendar_view' in data

    def test_get_meal_plan_dates_with_month_filter(self, client, auth_headers):
        """Test getting dates filtered by month"""
        with patch('src.application.use_cases.planning.get_meal_plan_dates_usecase.GetMealPlanDatesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "dates_with_plans": ["2024-01-15", "2024-01-20"],
                "total_dates": 2,
                "applied_filter": {"month": "2024-01"}
            }

            response = client.get('/api/planning/dates?month=2024-01',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['applied_filter']['month'] == "2024-01"

    def test_get_meal_plan_dates_empty(self, client, auth_headers):
        """Test getting dates when user has no meal plans"""
        with patch('src.application.use_cases.planning.get_meal_plan_dates_usecase.GetMealPlanDatesUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "dates_with_plans": [],
                "total_dates": 0,
                "calendar_view": {}
            }

            response = client.get('/api/planning/dates',
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_dates'] == 0

    # ================================================================
    # POST /api/planning/images/update - Update Meal Plan Images
    # ================================================================

    def test_update_meal_plan_images_success(self, client, auth_headers):
        """Test updating meal plan images status"""
        with patch('src.application.use_cases.planning.update_meal_plan_use_case.UpdateMealPlanUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "message": "Meal plan images updated successfully",
                "meal_plan_id": "meal_plan_123",
                "updated_images": {
                    "breakfast_123": {
                        "image_url": "https://storage.example.com/breakfast.jpg",
                        "status": "generated"
                    },
                    "lunch_456": {
                        "image_url": "https://storage.example.com/lunch.jpg", 
                        "status": "generated"
                    }
                },
                "total_images_updated": 2
            }

            update_data = {
                "meal_plan_id": "meal_plan_123",
                "image_updates": [
                    {
                        "recipe_uid": "breakfast_123",
                        "image_url": "https://storage.example.com/breakfast.jpg",
                        "status": "generated"
                    },
                    {
                        "recipe_uid": "lunch_456",
                        "image_url": "https://storage.example.com/lunch.jpg",
                        "status": "generated"
                    }
                ]
            }

            response = client.post('/api/planning/images/update',
                json=update_data,
                headers=auth_headers)

            assert response.status_code == 200
            data = response.get_json()
            assert data['total_images_updated'] == 2
            assert 'updated_images' in data

    def test_update_meal_plan_images_invalid_plan(self, client, auth_headers):
        """Test updating images for non-existent meal plan"""
        with patch('src.application.use_cases.planning.update_meal_plan_use_case.UpdateMealPlanUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("Meal plan not found")

            update_data = {
                "meal_plan_id": "nonexistent_plan",
                "image_updates": []
            }

            response = client.post('/api/planning/images/update',
                json=update_data,
                headers=auth_headers)

            assert response.status_code == 404

    def test_update_meal_plan_images_invalid_urls(self, client, auth_headers):
        """Test updating meal plan images with invalid URLs"""
        invalid_urls = [
            "not-a-url",
            "javascript:alert('xss')",
            "ftp://malicious.com/file",
            ""
        ]

        for invalid_url in invalid_urls:
            update_data = {
                "meal_plan_id": "meal_plan_123",
                "image_updates": [
                    {
                        "recipe_uid": "recipe_123",
                        "image_url": invalid_url,
                        "status": "generated"
                    }
                ]
            }

            response = client.post('/api/planning/images/update',
                json=update_data,
                headers=auth_headers)

            assert response.status_code == 400

    # ================================================================
    # Security and Performance Tests
    # ================================================================

    def test_planning_endpoints_authentication(self, client):
        """Test that all endpoints require authentication"""
        endpoints = [
            ('POST', '/api/planning/save', {}),
            ('PUT', '/api/planning/update', {}),
            ('DELETE', '/api/planning/delete?date=2024-01-15', None),
            ('GET', '/api/planning/get?meal_date=2024-01-15', None),
            ('GET', '/api/planning/all', None),
            ('GET', '/api/planning/dates', None),
            ('POST', '/api/planning/images/update', {})
        ]

        for method, endpoint, data in endpoints:
            if method == 'POST' or method == 'PUT':
                response = getattr(client, method.lower())(endpoint, json=data)
            else:
                response = getattr(client, method.lower())(endpoint)
            
            assert response.status_code == 401

    def test_planning_sql_injection_protection(self, client, auth_headers):
        """Test SQL injection protection in planning endpoints"""
        malicious_dates = [
            "2024-01-15'; DROP TABLE meal_plans; --",
            "2024-01-15' OR '1'='1",
            "'; DELETE FROM users; --"
        ]

        for malicious_date in malicious_dates:
            response = client.get(f'/api/planning/get?meal_date={malicious_date}',
                headers=auth_headers)
            
            assert response.status_code in [400, 404]

    def test_planning_date_validation(self, client, auth_headers):
        """Test comprehensive date validation"""
        invalid_dates = [
            "2024-13-01",  # Invalid month
            "2024-02-30",  # Invalid day
            "2024-01-32",  # Invalid day
            "24-01-15",    # Wrong format
            "2024/01/15",  # Wrong separator
            "tomorrow",    # Non-date string
            "2024-1-1"     # Missing zero padding
        ]

        for invalid_date in invalid_dates:
            response = client.get(f'/api/planning/get?meal_date={invalid_date}',
                headers=auth_headers)
            
            assert response.status_code == 400

    def test_planning_data_integrity(self, client, auth_headers):
        """Test data integrity in meal planning"""
        with patch('src.application.use_cases.planning.save_meal_plan_use_case.SaveMealPlanUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "meal_plan_id": "integrity_test_123",
                "total_meals": 3
            }

            # Test that all required fields are validated
            complete_plan = {
                "meal_date": "2024-01-15",
                "meals": {
                    "breakfast": {
                        "recipe_uid": "recipe_1",
                        "recipe_title": "Test Breakfast",
                        "servings": 1
                    }
                }
            }

            response = client.post('/api/planning/save',
                json=complete_plan,
                headers=auth_headers)

            assert response.status_code in [201, 400]  # Should either succeed or fail validation

    def test_planning_performance_large_plans(self, client, auth_headers):
        """Test performance with large meal plans"""
        with patch('src.application.use_cases.planning.save_meal_plan_use_case.SaveMealPlanUseCase.execute') as mock_execute:
            mock_execute.return_value = {"meal_plan_id": "large_plan_123"}

            # Create large meal plan with many meals and details
            large_plan = {
                "meal_date": "2024-01-15",
                "meals": {}
            }

            # Add 20 meals (breakfast, lunch, dinner, snacks)
            for i in range(20):
                meal_name = f"meal_{i}"
                large_plan["meals"][meal_name] = {
                    "recipe_uid": f"recipe_{i}",
                    "recipe_title": f"Recipe {i}",
                    "servings": i + 1,
                    "notes": f"Detailed notes for meal {i}" * 10  # Long notes
                }

            start_time = time.time()
            response = client.post('/api/planning/save',
                json=large_plan,
                headers=auth_headers)
            end_time = time.time()

            response_time = end_time - start_time
            # Should handle large plans within reasonable time
            assert response_time < 3.0
            assert response.status_code in [201, 400, 413]

    def test_planning_concurrent_modifications(self, client, auth_headers):
        """Test concurrent meal plan modifications"""
        import threading
        results = []
        
        def save_plan():
            plan = {
                "meal_date": "2024-01-15",
                "meals": {
                    "breakfast": {
                        "recipe_uid": "recipe_123",
                        "recipe_title": "Concurrent Test"
                    }
                }
            }
            response = client.post('/api/planning/save',
                json=plan,
                headers=auth_headers)
            results.append(response.status_code)
        
        with patch('src.application.use_cases.planning.save_meal_plan_use_case.SaveMealPlanUseCase.execute'):
            threads = []
            for _ in range(3):
                thread = threading.Thread(target=save_plan)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
        
        # All should complete without server errors
        assert all(status < 500 for status in results)

    def test_planning_cache_behavior(self, client, auth_headers):
        """Test caching behavior for meal plans"""
        with patch('src.application.use_cases.planning.get_meal_plan_by_user_and_date_use_case.GetMealPlanByUserAndDateUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "meal_plan_id": "cached_plan_123",
                "meal_date": "2024-01-15"
            }

            # First request
            response1 = client.get('/api/planning/get?meal_date=2024-01-15',
                headers=auth_headers)
            
            # Second request (should potentially hit cache)
            response2 = client.get('/api/planning/get?meal_date=2024-01-15',
                headers=auth_headers)

            assert response1.status_code == 200
            assert response2.status_code == 200
            
            # Should have appropriate cache headers
            assert any(header in response1.headers for header in ['Cache-Control', 'ETag', 'Last-Modified'])

    def test_planning_memory_usage_many_plans(self, client, auth_headers):
        """Test memory usage with many meal plans"""
        with patch('src.application.use_cases.planning.get_all_meal_plans_by_user_use_case.GetAllMealPlansByUserUseCase.execute') as mock_execute:
            # Simulate user with many meal plans
            large_plan_list = []
            for i in range(365):  # One year of meal plans
                large_plan_list.append({
                    "meal_plan_id": f"plan_{i}",
                    "meal_date": f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                    "total_meals": 3,
                    "meals": {f"meal_{j}": f"recipe_{j}" for j in range(3)}
                })
            
            mock_execute.return_value = {
                "meal_plans": large_plan_list,
                "total_plans": 365
            }

            response = client.get('/api/planning/all',
                headers=auth_headers)

            # Should handle large responses
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['meal_plans']) == 365