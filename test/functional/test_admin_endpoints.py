def test_admin_cleanup_tokens_requires_internal_secret(client):
    rv = client.post("/api/admin/cleanup-tokens")
    assert rv.status_code == 403


def test_admin_cleanup_tokens_ok_with_secret(client, monkeypatch):
    from src.interface.controllers import admin_controller as ctrl

    class FakeRepo:
        def cleanup_expired_tokens(self):
            return {"blacklist_cleaned": 3, "tracking_cleaned": 2}

    monkeypatch.setattr(ctrl, "TokenSecurityRepository", lambda: FakeRepo())

    rv = client.post(
        "/api/admin/cleanup-tokens",
        headers={"X-Internal-Secret": client.application.config.get("INTERNAL_SECRET_KEY", "")}
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data.get("cleaned", {}).get("blacklist_cleaned") == 3

