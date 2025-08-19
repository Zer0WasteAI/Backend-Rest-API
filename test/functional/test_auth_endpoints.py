"""
Functional tests for Authentication endpoints
Tests end-to-end authentication flows
"""
import pytest


def test_firebase_signin_success(client, monkeypatch):
    """Test successful Firebase authentication"""
    from src.interface.controllers import auth_controller as ctrl
    
    class FakeAuthUseCase:
        def execute(self, firebase_token):
            return {
                "access_token": "fake_jwt_token",
                "user": {
                    "uid": "test-user-123",
                    "email": "test@example.com",
                    "display_name": "Test User"
                }
            }
    
    monkeypatch.setattr(ctrl, "make_firebase_authentication_use_case", lambda: FakeAuthUseCase())
    
    rv = client.post(
        "/api/auth/firebase-signin",
        json={"firebase_token": "valid_firebase_token"}
    )
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["uid"] == "test-user-123"


def test_firebase_signin_invalid_token(client, monkeypatch):
    """Test Firebase authentication with invalid token"""
    from src.interface.controllers import auth_controller as ctrl
    
    class FakeAuthUseCase:
        def execute(self, firebase_token):
            from src.shared.exceptions.custom import InvalidCredentialsException
            raise InvalidCredentialsException("Invalid Firebase token")
    
    monkeypatch.setattr(ctrl, "make_firebase_authentication_use_case", lambda: FakeAuthUseCase())
    
    rv = client.post(
        "/api/auth/firebase-signin",
        json={"firebase_token": "invalid_token"}
    )
    
    assert rv.status_code == 401


def test_guest_login_success(client, monkeypatch):
    """Test successful guest login"""
    from src.interface.controllers import auth_controller as ctrl
    
    class FakeGuestUseCase:
        def execute(self):
            return {
                "access_token": "guest_jwt_token",
                "user": {
                    "uid": "guest-user-456",
                    "email": None,
                    "display_name": "Guest User",
                    "is_guest": True
                }
            }
    
    monkeypatch.setattr(ctrl, "make_guest_authentication_use_case", lambda: FakeGuestUseCase())
    
    rv = client.post("/api/auth/guest-login")
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["is_guest"] is True


def test_refresh_token_success(client, monkeypatch):
    """Test successful token refresh"""
    from src.interface.controllers import auth_controller as ctrl
    
    class FakeRefreshUseCase:
        def execute(self, refresh_token):
            return {
                "access_token": "new_jwt_token",
                "refresh_token": "new_refresh_token"
            }
    
    monkeypatch.setattr(ctrl, "make_refresh_token_use_case", lambda: FakeRefreshUseCase())
    
    rv = client.post(
        "/api/auth/refresh-token",
        json={"refresh_token": "valid_refresh_token"}
    )
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_logout_success(client, auth_header, monkeypatch):
    """Test successful logout"""
    from src.interface.controllers import auth_controller as ctrl
    
    class FakeLogoutUseCase:
        def execute(self, user_uid, access_token):
            return {"message": "Successfully logged out"}
    
    monkeypatch.setattr(ctrl, "make_logout_use_case", lambda: FakeLogoutUseCase())
    
    rv = client.post("/api/auth/logout", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "message" in data


def test_firebase_debug_endpoint(client, monkeypatch):
    """Test Firebase debug endpoint for development"""
    from src.interface.controllers import auth_controller as ctrl
    
    class FakeDebugUseCase:
        def execute(self):
            return {
                "firebase_config_status": "configured",
                "credentials_status": "valid"
            }
    
    monkeypatch.setattr(ctrl, "make_firebase_debug_use_case", lambda: FakeDebugUseCase())
    
    rv = client.get("/api/auth/firebase-debug")
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "firebase_config_status" in data


def test_auth_endpoints_require_proper_format(client):
    """Test that auth endpoints validate request format"""
    # Test missing firebase_token
    rv = client.post("/api/auth/firebase-signin", json={})
    assert rv.status_code == 400
    
    # Test missing refresh_token
    rv = client.post("/api/auth/refresh-token", json={})
    assert rv.status_code == 400


def test_protected_endpoints_require_auth(client):
    """Test that protected endpoints require authentication"""
    rv = client.post("/api/auth/logout")  # No auth header
    assert rv.status_code == 401
