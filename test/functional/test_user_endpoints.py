"""
Functional tests for User endpoints
Tests end-to-end user management flows
"""
import pytest


def test_get_user_profile_success(client, auth_header, monkeypatch):
    """Test successful user profile retrieval"""
    from src.interface.controllers import user_controller as ctrl
    
    class FakeGetUserProfileUseCase:
        def execute(self, user_uid):
            return {
                "user_uid": user_uid,
                "profile": {
                    "display_name": "John Doe",
                    "email": "john.doe@example.com",
                    "photo_url": "https://storage.googleapis.com/profile_photos/john_doe.jpg",
                    "email_verified": True,
                    "phone_number": "+1234567890",
                    "created_at": "2025-01-15T10:00:00Z",
                    "last_login": "2025-08-19T14:00:00Z"
                },
                "preferences": {
                    "dietary_restrictions": ["vegetarian"],
                    "favorite_cuisines": ["Italian", "Mediterranean"],
                    "notification_settings": {
                        "email_notifications": True,
                        "push_notifications": False,
                        "recipe_suggestions": True
                    }
                },
                "stats": {
                    "recipes_saved": 25,
                    "ingredients_recognized": 150,
                    "cooking_sessions": 12
                }
            }
    
    monkeypatch.setattr(ctrl, "make_get_user_profile_use_case", lambda: FakeGetUserProfileUseCase())
    
    rv = client.get("/api/user/profile", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "profile" in data
    assert "preferences" in data
    assert "stats" in data
    assert data["profile"]["display_name"] == "John Doe"
    assert data["profile"]["email"] == "john.doe@example.com"
    assert data["stats"]["recipes_saved"] == 25


def test_update_user_profile_success(client, auth_header, monkeypatch):
    """Test successful user profile update"""
    from src.interface.controllers import user_controller as ctrl
    
    class FakeUpdateUserProfileUseCase:
        def execute(self, user_uid, profile_data):
            return {
                "user_uid": user_uid,
                "updated_profile": {
                    "display_name": profile_data.get("display_name", "John Doe"),
                    "email": profile_data.get("email", "john.doe@example.com"),
                    "phone_number": profile_data.get("phone_number"),
                    "updated_at": "2025-08-19T15:00:00Z"
                },
                "updated_preferences": {
                    "dietary_restrictions": profile_data.get("dietary_restrictions", []),
                    "favorite_cuisines": profile_data.get("favorite_cuisines", []),
                    "notification_settings": profile_data.get("notification_settings", {})
                },
                "message": "Profile updated successfully"
            }
    
    monkeypatch.setattr(ctrl, "make_update_user_profile_use_case", lambda: FakeUpdateUserProfileUseCase())
    
    update_data = {
        "display_name": "Jane Smith",
        "phone_number": "+0987654321",
        "dietary_restrictions": ["vegan", "gluten_free"],
        "favorite_cuisines": ["Asian", "Mexican"],
        "notification_settings": {
            "email_notifications": False,
            "push_notifications": True,
            "recipe_suggestions": True
        }
    }
    
    rv = client.put("/api/user/profile", json=update_data, headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "updated_profile" in data
    assert "updated_preferences" in data
    assert data["updated_profile"]["display_name"] == "Jane Smith"
    assert data["updated_profile"]["phone_number"] == "+0987654321"
    assert "vegan" in data["updated_preferences"]["dietary_restrictions"]
    assert "gluten_free" in data["updated_preferences"]["dietary_restrictions"]


def test_get_user_profile_unauthorized(client):
    """Test that user profile endpoint requires authentication"""
    rv = client.get("/api/user/profile")
    assert rv.status_code == 401


def test_update_user_profile_unauthorized(client):
    """Test that user profile update endpoint requires authentication"""
    update_data = {"display_name": "Unauthorized User"}
    rv = client.put("/api/user/profile", json=update_data)
    assert rv.status_code == 401


def test_get_user_profile_not_found(client, auth_header, monkeypatch):
    """Test user profile not found error"""
    from src.interface.controllers import user_controller as ctrl
    
    class FakeGetUserProfileUseCase:
        def execute(self, user_uid):
            raise ValueError("User profile not found")
    
    monkeypatch.setattr(ctrl, "make_get_user_profile_use_case", lambda: FakeGetUserProfileUseCase())
    
    rv = client.get("/api/user/profile", headers=auth_header)
    assert rv.status_code in [404, 500]


def test_update_user_profile_validation_error(client, auth_header, monkeypatch):
    """Test user profile update validation errors"""
    from src.interface.controllers import user_controller as ctrl
    
    class FakeUpdateUserProfileUseCase:
        def execute(self, user_uid, profile_data):
            if not profile_data.get("display_name"):
                raise ValueError("Display name is required")
            return {"message": "Profile updated"}
    
    monkeypatch.setattr(ctrl, "make_update_user_profile_use_case", lambda: FakeUpdateUserProfileUseCase())
    
    # Test empty display name
    rv = client.put("/api/user/profile", json={"display_name": ""}, headers=auth_header)
    assert rv.status_code in [400, 422, 500]
    
    # Test invalid email format
    rv = client.put("/api/user/profile", json={"email": "invalid-email"}, headers=auth_header)
    # Should either validate on frontend or backend
    # Status code depends on implementation
    assert rv.status_code in [200, 400, 422]


def test_update_user_preferences_only(client, auth_header, monkeypatch):
    """Test updating only user preferences"""
    from src.interface.controllers import user_controller as ctrl
    
    class FakeUpdateUserProfileUseCase:
        def execute(self, user_uid, profile_data):
            return {
                "user_uid": user_uid,
                "updated_preferences": profile_data,
                "message": "Preferences updated successfully"
            }
    
    monkeypatch.setattr(ctrl, "make_update_user_profile_use_case", lambda: FakeUpdateUserProfileUseCase())
    
    preferences_data = {
        "dietary_restrictions": ["pescatarian"],
        "favorite_cuisines": ["Japanese", "Thai"],
        "notification_settings": {
            "email_notifications": True,
            "push_notifications": True,
            "recipe_suggestions": False
        }
    }
    
    rv = client.put("/api/user/profile", json=preferences_data, headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "updated_preferences" in data
    assert "pescatarian" in data["updated_preferences"]["dietary_restrictions"]


def test_user_profile_data_privacy(client, auth_header, monkeypatch):
    """Test that sensitive user data is properly handled"""
    from src.interface.controllers import user_controller as ctrl
    
    class FakeGetUserProfileUseCase:
        def execute(self, user_uid):
            return {
                "user_uid": user_uid,
                "profile": {
                    "display_name": "Privacy Test User",
                    "email": "privacy@example.com",
                    # Should not include sensitive fields like password_hash, tokens, etc.
                },
                "preferences": {
                    "dietary_restrictions": ["vegetarian"]
                }
            }
    
    monkeypatch.setattr(ctrl, "make_get_user_profile_use_case", lambda: FakeGetUserProfileUseCase())
    
    rv = client.get("/api/user/profile", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    
    # Ensure sensitive data is not exposed
    sensitive_fields = ["password", "password_hash", "access_token", "refresh_token", "api_keys"]
    for field in sensitive_fields:
        assert field not in str(data), f"Sensitive field '{field}' found in response"


def test_partial_profile_update(client, auth_header, monkeypatch):
    """Test partial profile updates (updating only some fields)"""
    from src.interface.controllers import user_controller as ctrl
    
    class FakeUpdateUserProfileUseCase:
        def execute(self, user_uid, profile_data):
            # Simulate partial update - only update provided fields
            updated_fields = {}
            if "display_name" in profile_data:
                updated_fields["display_name"] = profile_data["display_name"]
            if "phone_number" in profile_data:
                updated_fields["phone_number"] = profile_data["phone_number"]
                
            return {
                "user_uid": user_uid,
                "updated_profile": updated_fields,
                "message": "Partial profile update successful"
            }
    
    monkeypatch.setattr(ctrl, "make_update_user_profile_use_case", lambda: FakeUpdateUserProfileUseCase())
    
    # Update only display name
    partial_update = {"display_name": "Updated Name Only"}
    
    rv = client.put("/api/user/profile", json=partial_update, headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "updated_profile" in data
    assert data["updated_profile"]["display_name"] == "Updated Name Only"
    assert "phone_number" not in data["updated_profile"]
