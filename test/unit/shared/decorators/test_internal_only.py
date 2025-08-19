import pytest
from flask import Flask

from src.shared.decorators.internal_only import internal_only


def test_internal_only_unauthorized(app: Flask, client):
    app.config["INTERNAL_SECRET_KEY"] = "expected-secret"

    @internal_only
    def _protected():
        return {"ok": True}, 200

    # Mount a temporary route using the decorator to test end-to-end
    app.add_url_rule("/_internal_test", "_internal_test", _protected, methods=["GET"])

    # Missing header -> forbidden
    resp = client.get("/_internal_test")
    assert resp.status_code == 403
    data = resp.get_json()
    assert data["error"] == "No autorizado"


def test_internal_only_authorized(app: Flask, client):
    app.config["INTERNAL_SECRET_KEY"] = "expected-secret"

    @internal_only
    def _protected_ok():
        return {"ok": True}, 200

    app.add_url_rule("/_internal_ok", "_internal_ok", _protected_ok, methods=["GET"])

    resp = client.get("/_internal_ok", headers={"X-Internal-Secret": "expected-secret"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True

