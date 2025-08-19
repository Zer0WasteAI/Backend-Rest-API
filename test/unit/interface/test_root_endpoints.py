from flask import Flask


def test_welcome_root(client, app: Flask):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["message"].startswith("¡Bienvenido")
    assert "endpoints" in data


def test_swagger_ui_served(client):
    # Swagger UI is mounted under /docs by swagger_config
    resp = client.get("/docs")
    # Flasgger serves HTML; just assert reachable
    assert resp.status_code in (200, 301, 302)

