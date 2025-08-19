from flask import Flask
from flask_jwt_extended import create_access_token


class _StubGetInventoryUC:
    def execute(self, user_uid: str):
        return {
            "user_uid": user_uid,
            "ingredients": {},
            "foods": [],
            "summary": {"total_ingredient_types": 0}
        }


class _StubAddIngredientsUC:
    def execute(self, user_uid: str, ingredients_data):
        return None


def test_get_inventory_ok(monkeypatch, app: Flask, client):
    # Monkeypatch factory to return stub use case
    monkeypatch.setattr(
        "src.application.factories.inventory_usecase_factory.make_get_inventory_content_use_case",
        lambda db: _StubGetInventoryUC(),
        raising=True,
    )

    with app.app_context():
        token = create_access_token(identity="u1")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/inventory", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["user_uid"] == "u1"
    assert "ingredients" in data and "foods" in data


def test_add_ingredients_ok(monkeypatch, app: Flask, client):
    monkeypatch.setattr(
        "src.application.factories.inventory_usecase_factory.make_add_ingredients_to_inventory_use_case",
        lambda db: _StubAddIngredientsUC(),
        raising=True,
    )

    with app.app_context():
        token = create_access_token(identity="u1")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {
        "ingredients": [
            {
                "name": "Tomates cherry",
                "quantity": 500,
                "type_unit": "gr",
                "storage_type": "refrigerador",
                "tips": "Mantener refrigerados",
                "image_path": "https://x/y.jpg",
                "expiration_date": "2025-12-31T00:00:00Z"
            }
        ]
    }

    resp = client.post("/api/inventory/ingredients", headers=headers, json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["message"]

