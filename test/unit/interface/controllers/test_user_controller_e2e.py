from typing import Any
from flask import Flask
from flask_jwt_extended import create_access_token


class _StubFirestoreService:
    def __init__(self, profile: dict[str, Any] | None):
        self._profile = profile

    def get_profile(self, uid: str) -> dict | None:
        return self._profile

    def sync_with_mysql(self, uid: str, mysql_profile_repo):
        # no-op in tests
        return True


class _StubProfileRepo:
    pass


def test_get_user_profile_ok(monkeypatch, app: Flask, client):
    # Monkeypatch factories to return stubs instead of real services
    monkeypatch.setattr(
        "src.application.factories.auth_usecase_factory.make_firestore_profile_service",
        lambda: _StubFirestoreService({
            "uid": "test-user-uid",
            "displayName": "Tester",
            "email": "tester@example.com",
            "initialPreferencesCompleted": True
        }),
        raising=True,
    )
    monkeypatch.setattr(
        "src.application.factories.auth_usecase_factory.make_profile_repository",
        lambda: _StubProfileRepo(),
        raising=True,
    )

    # Create JWT and call endpoint
    with app.app_context():
        token = create_access_token(identity="test-user-uid")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/user/profile", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["uid"] == "test-user-uid"
    assert data["displayName"] == "Tester"


def test_get_user_profile_not_found(monkeypatch, app: Flask, client):
    # Return None profile
    monkeypatch.setattr(
        "src.application.factories.auth_usecase_factory.make_firestore_profile_service",
        lambda: _StubFirestoreService(None),
        raising=True,
    )
    monkeypatch.setattr(
        "src.application.factories.auth_usecase_factory.make_profile_repository",
        lambda: _StubProfileRepo(),
        raising=True,
    )

    with app.app_context():
        token = create_access_token(identity="test-user-uid")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/user/profile", headers=headers)
    assert resp.status_code == 404
    data = resp.get_json()
    assert data.get("error") == "Profile not found"

