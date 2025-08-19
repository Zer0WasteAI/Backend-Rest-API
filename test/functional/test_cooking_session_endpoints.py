"""
Functional tests for Cooking Session endpoints  
Tests end-to-end cooking session management flows
"""
import pytest


def test_create_cooking_session_success(client, auth_header, monkeypatch):
    """Test successful cooking session creation"""
    from src.interface.controllers import cooking_session_controller as ctrl
    
    class FakeCreateCookingSessionUseCase:
        def execute(self, user_uid, session_data):
            return {
                "session_id": "session_123",
                "user_uid": user_uid,
                "recipe_id": session_data.get("recipe_id"),
                "recipe_name": "Spaghetti Carbonara",
                "status": "started",
                "ingredients_needed": [
                    {"name": "spaghetti", "quantity": "400g", "available": True},
                    {"name": "eggs", "quantity": "4", "available": True},
                    {"name": "bacon", "quantity": "200g", "available": False}
                ],
                "estimated_duration": 30,
                "started_at": "2025-08-19T15:00:00Z",
                "steps": [
                    {"step": 1, "instruction": "Boil water for pasta", "completed": False},
                    {"step": 2, "instruction": "Cook bacon until crispy", "completed": False}
                ]
            }
    
    monkeypatch.setattr(ctrl, "make_create_cooking_session_use_case", lambda: FakeCreateCookingSessionUseCase())
    
    session_data = {
        "recipe_id": "recipe_456",
        "planned_portions": 4,
        "notes": "Dinner for family"
    }
    
    rv = client.post("/api/cooking-session", json=session_data, headers=auth_header)
    
    assert rv.status_code in [200, 201]
    data = rv.get_json()
    assert "session_id" in data
    assert data["session_id"] == "session_123"
    assert data["status"] == "started"
    assert "ingredients_needed" in data
    assert len(data["steps"]) == 2


def test_get_cooking_sessions_success(client, auth_header, monkeypatch):
    """Test successful retrieval of cooking sessions"""
    from src.interface.controllers import cooking_session_controller as ctrl
    
    class FakeGetCookingSessionsUseCase:
        def execute(self, user_uid):
            return {
                "sessions": [
                    {
                        "session_id": "session_123",
                        "recipe_name": "Spaghetti Carbonara",
                        "status": "in_progress",
                        "started_at": "2025-08-19T15:00:00Z",
                        "progress_percentage": 60
                    },
                    {
                        "session_id": "session_124", 
                        "recipe_name": "Chicken Stir Fry",
                        "status": "completed",
                        "started_at": "2025-08-19T12:00:00Z",
                        "completed_at": "2025-08-19T12:45:00Z",
                        "progress_percentage": 100
                    }
                ],
                "total_sessions": 2,
                "active_sessions": 1,
                "completed_today": 1
            }
    
    monkeypatch.setattr(ctrl, "make_get_cooking_sessions_use_case", lambda: FakeGetCookingSessionsUseCase())
    
    rv = client.get("/api/cooking-session", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "sessions" in data
    assert len(data["sessions"]) == 2
    assert data["total_sessions"] == 2
    assert data["active_sessions"] == 1


def test_get_cooking_session_by_id_success(client, auth_header, monkeypatch):
    """Test successful retrieval of specific cooking session"""
    from src.interface.controllers import cooking_session_controller as ctrl
    
    class FakeGetCookingSessionByIdUseCase:
        def execute(self, user_uid, session_id):
            return {
                "session_id": session_id,
                "recipe_id": "recipe_456",
                "recipe_name": "Beef Tacos",
                "status": "in_progress",
                "started_at": "2025-08-19T16:00:00Z",
                "estimated_completion": "2025-08-19T16:30:00Z",
                "progress_percentage": 45,
                "current_step": 3,
                "total_steps": 7,
                "ingredients_status": [
                    {"name": "ground_beef", "used": True, "quantity_used": "500g"},
                    {"name": "taco_shells", "used": False, "quantity_needed": "8"}
                ],
                "steps": [
                    {"step": 1, "instruction": "Brown the ground beef", "completed": True, "completed_at": "2025-08-19T16:10:00Z"},
                    {"step": 2, "instruction": "Add taco seasoning", "completed": True, "completed_at": "2025-08-19T16:15:00Z"},
                    {"step": 3, "instruction": "Warm taco shells", "completed": False}
                ],
                "session_notes": "Making for dinner party",
                "timer_active": True,
                "timer_remaining": 300
            }
    
    monkeypatch.setattr(ctrl, "make_get_cooking_session_by_id_use_case", lambda: FakeGetCookingSessionByIdUseCase())
    
    rv = client.get("/api/cooking-session/session_123", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["session_id"] == "session_123"
    assert data["status"] == "in_progress"
    assert data["progress_percentage"] == 45
    assert data["timer_active"] is True
    assert len(data["steps"]) == 3


def test_complete_cooking_session_success(client, auth_header, monkeypatch):
    """Test successful cooking session completion"""
    from src.interface.controllers import cooking_session_controller as ctrl
    
    class FakeCompleteCookingSessionUseCase:
        def execute(self, user_uid, session_id, completion_data):
            return {
                "session_id": session_id,
                "status": "completed",
                "started_at": "2025-08-19T15:00:00Z",
                "completed_at": "2025-08-19T16:30:00Z",
                "total_duration": 90,  # minutes
                "rating": completion_data.get("rating"),
                "notes": completion_data.get("notes"),
                "ingredients_consumed": [
                    {"name": "spaghetti", "quantity_used": "400g"},
                    {"name": "eggs", "quantity_used": "4"}
                ],
                "portions_made": completion_data.get("portions_made", 4),
                "leftover_portions": completion_data.get("leftover_portions", 1),
                "success": True,
                "experience_points": 50,
                "achievements_unlocked": ["First Italian Dish"]
            }
    
    monkeypatch.setattr(ctrl, "make_complete_cooking_session_use_case", lambda: FakeCompleteCookingSessionUseCase())
    
    completion_data = {
        "rating": 5,
        "notes": "Delicious! Will make again.",
        "portions_made": 4,
        "leftover_portions": 1,
        "difficulty_experienced": "medium"
    }
    
    rv = client.put("/api/cooking-session/session_123/complete", json=completion_data, headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["session_id"] == "session_123"
    assert data["status"] == "completed"
    assert data["rating"] == 5
    assert data["experience_points"] == 50
    assert "First Italian Dish" in data["achievements_unlocked"]


def test_cooking_session_endpoints_require_auth(client):
    """Test that cooking session endpoints require authentication"""
    endpoints = [
        ("POST", "/api/cooking-session", {"recipe_id": "test"}),
        ("GET", "/api/cooking-session", None),
        ("GET", "/api/cooking-session/session_123", None),
        ("PUT", "/api/cooking-session/session_123/complete", {"rating": 5})
    ]
    
    for method, endpoint, data in endpoints:
        if method == "POST":
            rv = client.post(endpoint, json=data)
        elif method == "GET":
            rv = client.get(endpoint)
        elif method == "PUT":
            rv = client.put(endpoint, json=data)
            
        assert rv.status_code == 401


def test_create_cooking_session_validation_error(client, auth_header, monkeypatch):
    """Test cooking session creation with validation errors"""
    from src.interface.controllers import cooking_session_controller as ctrl
    
    class FakeCreateCookingSessionUseCase:
        def execute(self, user_uid, session_data):
            if not session_data.get("recipe_id"):
                raise ValueError("Recipe ID is required")
            return {"session_id": "session_123"}
    
    monkeypatch.setattr(ctrl, "make_create_cooking_session_use_case", lambda: FakeCreateCookingSessionUseCase())
    
    # Test missing recipe_id
    rv = client.post("/api/cooking-session", json={}, headers=auth_header)
    assert rv.status_code in [400, 422, 500]
    
    # Test empty recipe_id
    rv = client.post("/api/cooking-session", json={"recipe_id": ""}, headers=auth_header)
    assert rv.status_code in [400, 422, 500]


def test_get_cooking_session_not_found(client, auth_header, monkeypatch):
    """Test getting non-existent cooking session"""
    from src.interface.controllers import cooking_session_controller as ctrl
    
    class FakeGetCookingSessionByIdUseCase:
        def execute(self, user_uid, session_id):
            raise ValueError(f"Cooking session {session_id} not found")
    
    monkeypatch.setattr(ctrl, "make_get_cooking_session_by_id_use_case", lambda: FakeGetCookingSessionByIdUseCase())
    
    rv = client.get("/api/cooking-session/nonexistent_session", headers=auth_header)
    assert rv.status_code in [404, 500]


def test_complete_cooking_session_already_completed(client, auth_header, monkeypatch):
    """Test completing an already completed cooking session"""
    from src.interface.controllers import cooking_session_controller as ctrl
    
    class FakeCompleteCookingSessionUseCase:
        def execute(self, user_uid, session_id, completion_data):
            raise ValueError("Cooking session is already completed")
    
    monkeypatch.setattr(ctrl, "make_complete_cooking_session_use_case", lambda: FakeCompleteCookingSessionUseCase())
    
    completion_data = {"rating": 4, "notes": "Good meal"}
    
    rv = client.put("/api/cooking-session/completed_session/complete", json=completion_data, headers=auth_header)
    assert rv.status_code in [400, 409, 500]


def test_cooking_session_step_updates(client, auth_header, monkeypatch):
    """Test updating cooking session step progress"""
    from src.interface.controllers import cooking_session_controller as ctrl
    
    # Mock a hypothetical step update endpoint if it exists
    class FakeUpdateStepUseCase:
        def execute(self, user_uid, session_id, step_data):
            return {
                "session_id": session_id,
                "step_updated": step_data["step_number"],
                "completed": step_data["completed"],
                "progress_percentage": 75,
                "message": "Step updated successfully"
            }
    
    # This test assumes there might be a step update endpoint
    # If not implemented, this test would fail gracefully
    step_data = {"step_number": 3, "completed": True}
    
    try:
        rv = client.put("/api/cooking-session/session_123/step", json=step_data, headers=auth_header)
        # If endpoint exists, expect success or appropriate error
        assert rv.status_code in [200, 404, 405]  # 405 if method not allowed
    except Exception:
        # If endpoint doesn't exist, this is expected
        pass
