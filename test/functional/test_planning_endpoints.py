"""
Functional tests for Planning endpoints
Tests end-to-end meal planning flows
"""
import pytest


def test_create_meal_plan_success(client, auth_header, monkeypatch):
    """Test successful meal plan creation"""
    from src.interface.controllers import planning_controller as ctrl
    
    class FakeCreateMealPlanUseCase:
        def execute(self, user_uid, plan_data):
            return {
                "plan_id": "plan_123",
                "user_uid": user_uid,
                "name": plan_data["name"],
                "description": plan_data.get("description", ""),
                "start_date": plan_data["start_date"],
                "end_date": plan_data["end_date"],
                "total_days": 7,
                "meals": [
                    {
                        "day": 1,
                        "date": "2025-08-20",
                        "breakfast": {
                            "recipe_id": "recipe_001",
                            "recipe_name": "Oatmeal with Berries",
                            "portions": 2,
                            "estimated_prep_time": 10
                        },
                        "lunch": {
                            "recipe_id": "recipe_002", 
                            "recipe_name": "Caesar Salad",
                            "portions": 2,
                            "estimated_prep_time": 15
                        },
                        "dinner": {
                            "recipe_id": "recipe_003",
                            "recipe_name": "Spaghetti Carbonara", 
                            "portions": 2,
                            "estimated_prep_time": 30
                        }
                    }
                ],
                "shopping_list": {
                    "ingredients": [
                        {"name": "oats", "quantity": "1 cup", "category": "grains"},
                        {"name": "berries", "quantity": "200g", "category": "fruits"},
                        {"name": "spaghetti", "quantity": "400g", "category": "pasta"}
                    ],
                    "total_items": 3,
                    "estimated_cost": 25.50
                },
                "nutritional_summary": {
                    "total_calories": 1800,
                    "total_protein": 75,
                    "total_carbs": 210,
                    "total_fat": 60
                },
                "created_at": "2025-08-19T15:00:00Z",
                "status": "active"
            }
    
    monkeypatch.setattr(ctrl, "make_create_meal_plan_use_case", lambda: FakeCreateMealPlanUseCase())
    
    plan_data = {
        "name": "Weekly Family Plan",
        "description": "Healthy meals for the family",
        "start_date": "2025-08-20",
        "end_date": "2025-08-26",
        "dietary_preferences": ["vegetarian"],
        "servings": 4,
        "budget_limit": 150.00
    }
    
    rv = client.post("/api/planning/meal-plans", json=plan_data, headers=auth_header)
    
    assert rv.status_code in [200, 201]
    data = rv.get_json()
    assert "plan_id" in data
    assert data["name"] == "Weekly Family Plan"
    assert data["total_days"] == 7
    assert "meals" in data
    assert "shopping_list" in data
    assert data["shopping_list"]["total_items"] == 3


def test_get_meal_plans_success(client, auth_header, monkeypatch):
    """Test successful retrieval of meal plans"""
    from src.interface.controllers import planning_controller as ctrl
    
    class FakeGetMealPlansUseCase:
        def execute(self, user_uid):
            return {
                "meal_plans": [
                    {
                        "plan_id": "plan_123",
                        "name": "Weekly Family Plan",
                        "description": "Healthy meals for the family",
                        "start_date": "2025-08-20",
                        "end_date": "2025-08-26",
                        "status": "active",
                        "total_meals": 21,
                        "completed_meals": 5,
                        "progress_percentage": 23,
                        "created_at": "2025-08-19T15:00:00Z"
                    },
                    {
                        "plan_id": "plan_124",
                        "name": "Quick Lunch Ideas",
                        "description": "Fast and healthy lunch options",
                        "start_date": "2025-08-15",
                        "end_date": "2025-08-21",
                        "status": "completed",
                        "total_meals": 7,
                        "completed_meals": 7,
                        "progress_percentage": 100,
                        "created_at": "2025-08-14T10:00:00Z"
                    },
                    {
                        "plan_id": "plan_125",
                        "name": "Low Carb Challenge",
                        "description": "30-day low carb meal plan",
                        "start_date": "2025-09-01",
                        "end_date": "2025-09-30",
                        "status": "draft",
                        "total_meals": 90,
                        "completed_meals": 0,
                        "progress_percentage": 0,
                        "created_at": "2025-08-18T14:30:00Z"
                    }
                ],
                "total_plans": 3,
                "active_plans": 1,
                "completed_plans": 1,
                "draft_plans": 1
            }
    
    monkeypatch.setattr(ctrl, "make_get_meal_plans_use_case", lambda: FakeGetMealPlansUseCase())
    
    rv = client.get("/api/planning/meal-plans", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "meal_plans" in data
    assert len(data["meal_plans"]) == 3
    assert data["total_plans"] == 3
    assert data["active_plans"] == 1
    
    # Check different plan statuses
    active_plan = next(p for p in data["meal_plans"] if p["status"] == "active")
    assert active_plan["progress_percentage"] == 23
    
    completed_plan = next(p for p in data["meal_plans"] if p["status"] == "completed")
    assert completed_plan["progress_percentage"] == 100


def test_get_meal_plan_by_id_success(client, auth_header, monkeypatch):
    """Test successful retrieval of specific meal plan"""
    from src.interface.controllers import planning_controller as ctrl
    
    class FakeGetMealPlanByIdUseCase:
        def execute(self, user_uid, plan_id):
            return {
                "plan_id": plan_id,
                "name": "Weekly Family Plan",
                "description": "Healthy meals for the family",
                "start_date": "2025-08-20",
                "end_date": "2025-08-26",
                "status": "active",
                "detailed_meals": [
                    {
                        "day": 1,
                        "date": "2025-08-20",
                        "day_name": "Tuesday",
                        "meals": {
                            "breakfast": {
                                "recipe_id": "recipe_001",
                                "recipe_name": "Greek Yogurt Parfait",
                                "portions": 2,
                                "estimated_prep_time": 5,
                                "calories": 250,
                                "completed": False
                            },
                            "lunch": {
                                "recipe_id": "recipe_002",
                                "recipe_name": "Quinoa Salad",
                                "portions": 2, 
                                "estimated_prep_time": 20,
                                "calories": 350,
                                "completed": False
                            },
                            "dinner": {
                                "recipe_id": "recipe_003",
                                "recipe_name": "Grilled Salmon",
                                "portions": 2,
                                "estimated_prep_time": 25,
                                "calories": 400,
                                "completed": True
                            }
                        },
                        "daily_nutrition": {
                            "calories": 1000,
                            "protein": 50,
                            "carbs": 80,
                            "fat": 35
                        }
                    }
                ],
                "shopping_list": {
                    "ingredients": [
                        {
                            "name": "Greek yogurt",
                            "quantity": "500g",
                            "category": "dairy",
                            "purchased": False,
                            "estimated_price": 3.99
                        },
                        {
                            "name": "salmon fillets",
                            "quantity": "400g",
                            "category": "seafood",
                            "purchased": True,
                            "estimated_price": 12.99
                        }
                    ],
                    "total_items": 2,
                    "purchased_items": 1,
                    "estimated_total_cost": 16.98
                },
                "progress": {
                    "total_meals": 21,
                    "completed_meals": 7,
                    "percentage": 33,
                    "current_streak": 3
                }
            }
    
    monkeypatch.setattr(ctrl, "make_get_meal_plan_by_id_use_case", lambda: FakeGetMealPlanByIdUseCase())
    
    rv = client.get("/api/planning/meal-plans/plan_123", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["plan_id"] == "plan_123"
    assert "detailed_meals" in data
    assert "shopping_list" in data
    assert data["progress"]["percentage"] == 33
    
    # Check meal details
    day_meals = data["detailed_meals"][0]["meals"]
    assert day_meals["dinner"]["completed"] is True
    assert day_meals["breakfast"]["completed"] is False


def test_update_meal_plan_success(client, auth_header, monkeypatch):
    """Test successful meal plan update"""
    from src.interface.controllers import planning_controller as ctrl
    
    class FakeUpdateMealPlanUseCase:
        def execute(self, user_uid, plan_id, update_data):
            return {
                "plan_id": plan_id,
                "name": update_data.get("name", "Updated Plan Name"),
                "description": update_data.get("description", "Updated description"),
                "updated_at": "2025-08-19T16:00:00Z",
                "changes": {
                    "meals_modified": update_data.get("meals_modified", 0),
                    "ingredients_added": update_data.get("ingredients_added", 0),
                    "ingredients_removed": update_data.get("ingredients_removed", 0)
                },
                "message": "Meal plan updated successfully"
            }
    
    monkeypatch.setattr(ctrl, "make_update_meal_plan_use_case", lambda: FakeUpdateMealPlanUseCase())
    
    update_data = {
        "name": "Updated Weekly Plan",
        "description": "Modified family meal plan",
        "meals_modified": 3,
        "ingredients_added": 5,
        "ingredients_removed": 2
    }
    
    rv = client.put("/api/planning/meal-plans/plan_123", json=update_data, headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["plan_id"] == "plan_123"
    assert data["name"] == "Updated Weekly Plan"
    assert "changes" in data
    assert data["changes"]["meals_modified"] == 3


def test_delete_meal_plan_success(client, auth_header, monkeypatch):
    """Test successful meal plan deletion"""
    from src.interface.controllers import planning_controller as ctrl
    
    class FakeDeleteMealPlanUseCase:
        def execute(self, user_uid, plan_id):
            return {
                "plan_id": plan_id,
                "deleted_at": "2025-08-19T16:30:00Z",
                "message": "Meal plan deleted successfully",
                "cleanup_summary": {
                    "meals_removed": 21,
                    "shopping_list_cleared": True,
                    "reminders_cancelled": 5
                }
            }
    
    monkeypatch.setattr(ctrl, "make_delete_meal_plan_use_case", lambda: FakeDeleteMealPlanUseCase())
    
    rv = client.delete("/api/planning/meal-plans/plan_123", headers=auth_header)
    
    assert rv.status_code in [200, 204]
    if rv.status_code == 200:
        data = rv.get_json()
        assert data["plan_id"] == "plan_123"
        assert "cleanup_summary" in data
        assert data["cleanup_summary"]["meals_removed"] == 21


def test_generate_shopping_list_success(client, auth_header, monkeypatch):
    """Test successful shopping list generation"""
    from src.interface.controllers import planning_controller as ctrl
    
    class FakeGenerateShoppingListUseCase:
        def execute(self, user_uid, plan_id):
            return {
                "plan_id": plan_id,
                "shopping_list": {
                    "categories": {
                        "produce": [
                            {"name": "tomatoes", "quantity": "1kg", "estimated_price": 4.50},
                            {"name": "onions", "quantity": "500g", "estimated_price": 2.00}
                        ],
                        "dairy": [
                            {"name": "milk", "quantity": "1L", "estimated_price": 3.50},
                            {"name": "cheese", "quantity": "200g", "estimated_price": 5.99}
                        ],
                        "meat": [
                            {"name": "chicken breast", "quantity": "800g", "estimated_price": 12.99}
                        ]
                    },
                    "summary": {
                        "total_items": 5,
                        "estimated_total_cost": 28.98,
                        "categories_count": 3
                    },
                    "optimization_tips": [
                        "Buy tomatoes and onions from produce section first",
                        "Check dairy expiration dates",
                        "Consider buying chicken in bulk for savings"
                    ]
                },
                "generated_at": "2025-08-19T17:00:00Z",
                "valid_until": "2025-08-26T23:59:59Z"
            }
    
    monkeypatch.setattr(ctrl, "make_generate_shopping_list_use_case", lambda: FakeGenerateShoppingListUseCase())
    
    rv = client.post("/api/planning/meal-plans/plan_123/shopping-list", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["plan_id"] == "plan_123"
    assert "shopping_list" in data
    assert data["shopping_list"]["summary"]["total_items"] == 5
    assert len(data["shopping_list"]["categories"]) == 3
    assert "optimization_tips" in data["shopping_list"]


def test_get_meal_plan_analytics_success(client, auth_header, monkeypatch):
    """Test successful meal plan analytics retrieval"""
    from src.interface.controllers import planning_controller as ctrl
    
    class FakeGetMealPlanAnalyticsUseCase:
        def execute(self, user_uid, plan_id):
            return {
                "plan_id": plan_id,
                "analytics": {
                    "completion_rate": 75,
                    "average_prep_time": 22,
                    "favorite_meals": [
                        {"recipe_name": "Grilled Salmon", "times_completed": 5},
                        {"recipe_name": "Caesar Salad", "times_completed": 4}
                    ],
                    "nutrition_tracking": {
                        "average_daily_calories": 1850,
                        "protein_goal_achievement": 85,
                        "carb_distribution": {"breakfast": 35, "lunch": 40, "dinner": 25}
                    },
                    "cost_analysis": {
                        "actual_cost": 142.50,
                        "budgeted_cost": 150.00,
                        "savings": 7.50,
                        "cost_per_meal": 6.79
                    },
                    "time_analysis": {
                        "total_prep_time": 450,  # minutes
                        "average_meal_prep": 21,
                        "quickest_meal": "Overnight Oats (5 min)",
                        "longest_meal": "Beef Stew (45 min)"
                    }
                },
                "trends": {
                    "most_active_day": "Sunday",
                    "completion_by_meal": {"breakfast": 90, "lunch": 70, "dinner": 65},
                    "weekly_progress": [20, 35, 50, 65, 75]
                },
                "recommendations": [
                    "Try meal prepping on Sundays",
                    "Consider adding more quick breakfast options",
                    "Your dinner completion rate could improve with simpler recipes"
                ]
            }
    
    monkeypatch.setattr(ctrl, "make_get_meal_plan_analytics_use_case", lambda: FakeGetMealPlanAnalyticsUseCase())
    
    rv = client.get("/api/planning/meal-plans/plan_123/analytics", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["plan_id"] == "plan_123"
    assert "analytics" in data
    assert data["analytics"]["completion_rate"] == 75
    assert "cost_analysis" in data["analytics"]
    assert "trends" in data
    assert len(data["recommendations"]) == 3


def test_planning_endpoints_require_auth(client):
    """Test that planning endpoints require authentication"""
    endpoints = [
        ("POST", "/api/planning/meal-plans", {"name": "test", "start_date": "2025-08-20", "end_date": "2025-08-26"}),
        ("GET", "/api/planning/meal-plans", None),
        ("GET", "/api/planning/meal-plans/plan_123", None), 
        ("PUT", "/api/planning/meal-plans/plan_123", {"name": "updated"}),
        ("DELETE", "/api/planning/meal-plans/plan_123", None),
        ("POST", "/api/planning/meal-plans/plan_123/shopping-list", None),
        ("GET", "/api/planning/meal-plans/plan_123/analytics", None)
    ]
    
    for method, endpoint, data in endpoints:
        if method == "POST":
            rv = client.post(endpoint, json=data)
        elif method == "GET":
            rv = client.get(endpoint)
        elif method == "PUT":
            rv = client.put(endpoint, json=data)
        elif method == "DELETE":
            rv = client.delete(endpoint)
            
        assert rv.status_code == 401


def test_create_meal_plan_validation_errors(client, auth_header, monkeypatch):
    """Test meal plan creation validation errors"""
    from src.interface.controllers import planning_controller as ctrl
    
    class FakeCreateMealPlanUseCase:
        def execute(self, user_uid, plan_data):
            if not plan_data.get("name"):
                raise ValueError("Plan name is required")
            if not plan_data.get("start_date"):
                raise ValueError("Start date is required")
            return {"plan_id": "test"}
    
    monkeypatch.setattr(ctrl, "make_create_meal_plan_use_case", lambda: FakeCreateMealPlanUseCase())
    
    # Test missing name
    rv = client.post("/api/planning/meal-plans", json={"start_date": "2025-08-20", "end_date": "2025-08-26"}, headers=auth_header)
    assert rv.status_code in [400, 422, 500]
    
    # Test missing start_date
    rv = client.post("/api/planning/meal-plans", json={"name": "Test Plan", "end_date": "2025-08-26"}, headers=auth_header)
    assert rv.status_code in [400, 422, 500]


def test_get_meal_plan_not_found(client, auth_header, monkeypatch):
    """Test getting non-existent meal plan"""
    from src.interface.controllers import planning_controller as ctrl
    
    class FakeGetMealPlanByIdUseCase:
        def execute(self, user_uid, plan_id):
            raise ValueError(f"Meal plan {plan_id} not found")
    
    monkeypatch.setattr(ctrl, "make_get_meal_plan_by_id_use_case", lambda: FakeGetMealPlanByIdUseCase())
    
    rv = client.get("/api/planning/meal-plans/nonexistent_plan", headers=auth_header)
    assert rv.status_code in [404, 500]
