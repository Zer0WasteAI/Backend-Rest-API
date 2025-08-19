"""
Functional tests for Inventory endpoints
Tests end-to-end inventory management flows
"""
import pytest


def test_get_inventory_complete_success(client, auth_header, monkeypatch):
    """Test getting complete inventory"""
    from src.interface.controllers import inventory_controller as ctrl
    
    class FakeGetInventoryUseCase:
        def execute(self, user_uid):
            return {
                "ingredients": [
                    {"name": "tomato", "quantity": 5, "unit": "pieces", "expiry_date": "2025-08-25"},
                    {"name": "onion", "quantity": 2, "unit": "pieces", "expiry_date": "2025-08-30"}
                ],
                "foods": [
                    {"name": "pasta", "quantity": 1, "unit": "kg", "expiry_date": "2025-09-01"}
                ]
            }
    
    monkeypatch.setattr(ctrl, "make_get_inventory_complete_use_case", lambda: FakeGetInventoryUseCase())
    
    rv = client.get("/api/inventory/complete", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "ingredients" in data
    assert "foods" in data
    assert len(data["ingredients"]) == 2
    assert len(data["foods"]) == 1


def test_add_ingredients_success(client, auth_header, monkeypatch):
    """Test adding ingredients to inventory"""
    from src.interface.controllers import inventory_controller as ctrl
    
    class FakeAddIngredientsUseCase:
        def execute(self, user_uid, ingredients_data):
            return {
                "added_ingredients": len(ingredients_data["ingredients"]),
                "message": "Ingredients added successfully"
            }
    
    monkeypatch.setattr(ctrl, "make_add_ingredients_use_case", lambda: FakeAddIngredientsUseCase())
    
    rv = client.post(
        "/api/inventory/add-ingredients",
        json={
            "ingredients": [
                {"name": "carrot", "quantity": 3, "unit": "pieces", "expiry_date": "2025-08-28"},
                {"name": "potato", "quantity": 1, "unit": "kg", "expiry_date": "2025-09-05"}
            ]
        },
        headers=auth_header
    )
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["added_ingredients"] == 2


def test_update_ingredient_success(client, auth_header, monkeypatch):
    """Test updating an ingredient"""
    from src.interface.controllers import inventory_controller as ctrl
    
    class FakeUpdateUseCase:
        def execute(self, user_uid, ingredient_id, update_data):
            return {
                "ingredient_id": ingredient_id,
                "updated_fields": list(update_data.keys()),
                "message": "Ingredient updated successfully"
            }
    
    monkeypatch.setattr(ctrl, "make_update_ingredient_use_case", lambda: FakeUpdateUseCase())
    
    rv = client.put(
        "/api/inventory/ingredient/123",
        json={"quantity": 10, "unit": "pieces"},
        headers=auth_header
    )
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["ingredient_id"] == "123"
    assert "updated_fields" in data


def test_delete_ingredient_success(client, auth_header, monkeypatch):
    """Test deleting an ingredient"""
    from src.interface.controllers import inventory_controller as ctrl
    
    class FakeDeleteUseCase:
        def execute(self, user_uid, ingredient_id):
            return {
                "ingredient_id": ingredient_id,
                "message": "Ingredient deleted successfully"
            }
    
    monkeypatch.setattr(ctrl, "make_delete_ingredient_use_case", lambda: FakeDeleteUseCase())
    
    rv = client.delete("/api/inventory/ingredient/123", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["ingredient_id"] == "123"


def test_get_expiring_items_success(client, auth_header, monkeypatch):
    """Test getting expiring items"""
    from src.interface.controllers import inventory_controller as ctrl
    
    class FakeExpiringUseCase:
        def execute(self, user_uid, days_ahead=7):
            return {
                "expiring_soon": [
                    {"name": "milk", "quantity": 1, "unit": "liter", "expiry_date": "2025-08-21"},
                    {"name": "bread", "quantity": 1, "unit": "loaf", "expiry_date": "2025-08-22"}
                ],
                "days_ahead": days_ahead
            }
    
    monkeypatch.setattr(ctrl, "make_get_expiring_items_use_case", lambda: FakeExpiringUseCase())
    
    rv = client.get("/api/inventory/expiring-items", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "expiring_soon" in data
    assert len(data["expiring_soon"]) == 2


def test_upload_inventory_image_success(client, auth_header, monkeypatch):
    """Test uploading inventory image"""
    from src.interface.controllers import inventory_controller as ctrl
    from io import BytesIO
    
    class FakeUploadUseCase:
        def execute(self, user_uid, file, description):
            return {
                "image_url": "https://storage.googleapis.com/bucket/inventory/image123.jpg",
                "description": description,
                "message": "Image uploaded successfully"
            }
    
    monkeypatch.setattr(ctrl, "make_upload_inventory_image_use_case", lambda: FakeUploadUseCase())
    
    # Create fake image file
    fake_image = BytesIO(b"fake image data")
    fake_image.name = "inventory_photo.jpg"
    
    rv = client.post(
        "/api/inventory/upload-image",
        data={
            "file": (fake_image, "inventory_photo.jpg"),
            "description": "pantry_overview"
        },
        headers=auth_header,
        content_type="multipart/form-data"
    )
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "image_url" in data


def test_add_ingredients_from_recognition_success(client, auth_header, monkeypatch):
    """Test adding ingredients from AI recognition"""
    from src.interface.controllers import inventory_controller as ctrl
    
    class FakeRecognitionUseCase:
        def execute(self, user_uid, recognition_data):
            return {
                "added_ingredients": 3,
                "recognized_items": ["tomato", "onion", "garlic"],
                "message": "Ingredients added from recognition"
            }
    
    monkeypatch.setattr(ctrl, "make_add_ingredients_from_recognition_use_case", lambda: FakeRecognitionUseCase())
    
    rv = client.post(
        "/api/inventory/add-from-recognition",
        json={
            "recognition_results": [
                {"name": "tomato", "confidence": 0.95},
                {"name": "onion", "confidence": 0.87},
                {"name": "garlic", "confidence": 0.82}
            ]
        },
        headers=auth_header
    )
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["added_ingredients"] == 3
    assert len(data["recognized_items"]) == 3


def test_reserve_batch_success(client, auth_header, monkeypatch):
    """Test reserving a batch of ingredients"""
    from src.interface.controllers import inventory_controller as ctrl
    
    class FakeReserveBatchUseCase:
        def execute(self, user_uid, ingredient_ids, recipe_id):
            return {
                "reserved_items": len(ingredient_ids),
                "recipe_id": recipe_id,
                "message": "Batch reserved successfully"
            }
    
    monkeypatch.setattr(ctrl, "make_reserve_batch_use_case", lambda: FakeReserveBatchUseCase())
    
    rv = client.post(
        "/api/inventory/batch/reserve",
        json={
            "ingredient_ids": ["ing1", "ing2", "ing3"],
            "recipe_id": "recipe123"
        },
        headers=auth_header
    )
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["reserved_items"] == 3


def test_inventory_endpoints_require_auth(client):
    """Test that inventory endpoints require authentication"""
    endpoints = [
        ("GET", "/api/inventory/complete"),
        ("POST", "/api/inventory/add-ingredients"),
        ("PUT", "/api/inventory/ingredient/123"),
        ("DELETE", "/api/inventory/ingredient/123"),
        ("GET", "/api/inventory/expiring-items")
    ]
    
    for method, endpoint in endpoints:
        if method == "GET":
            rv = client.get(endpoint)
        elif method == "POST":
            rv = client.post(endpoint, json={})
        elif method == "PUT":
            rv = client.put(endpoint, json={})
        elif method == "DELETE":
            rv = client.delete(endpoint)
        
        assert rv.status_code == 401


def test_inventory_validation_errors(client, auth_header):
    """Test inventory endpoint validation"""
    # Test add ingredients with invalid data
    rv = client.post(
        "/api/inventory/add-ingredients",
        json={"ingredients": []},  # Empty ingredients list
        headers=auth_header
    )
    assert rv.status_code in [400, 422]
    
    # Test update ingredient with invalid data
    rv = client.put(
        "/api/inventory/ingredient/123",
        json={},  # Empty update data
        headers=auth_header
    )
    assert rv.status_code in [400, 422]
