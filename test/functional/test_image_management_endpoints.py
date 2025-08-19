"""
Functional tests for Image Management endpoints
Tests end-to-end image management flows
"""
import pytest
from io import BytesIO


def test_assign_image_to_ingredient_success(client, auth_header, monkeypatch):
    """Test successful image assignment to ingredient"""
    from src.interface.controllers import image_management_controller as ctrl
    
    class FakeAssignImageToIngredientUseCase:
        def execute(self, user_uid, assignment_data):
            return {
                "assignment_id": "assign_123",
                "ingredient_id": assignment_data["ingredient_id"],
                "ingredient_name": "Fresh Tomatoes",
                "image_id": assignment_data["image_id"], 
                "image_url": "https://storage.googleapis.com/images/tomatoes_001.jpg",
                "thumbnail_url": "https://storage.googleapis.com/thumbs/tomatoes_001.jpg",
                "assigned_at": "2025-08-19T15:00:00Z",
                "assignment_type": "primary",
                "confidence_score": 0.95,
                "verified": False,
                "tags": ["fresh", "red", "ripe"],
                "metadata": {
                    "color_analysis": {"dominant_color": "red", "brightness": 0.7},
                    "quality_score": 0.92,
                    "image_dimensions": "1024x768"
                }
            }
    
    monkeypatch.setattr(ctrl, "make_assign_image_to_ingredient_use_case", lambda: FakeAssignImageToIngredientUseCase())
    
    assignment_data = {
        "ingredient_id": "ingredient_456",
        "image_id": "image_789",
        "assignment_type": "primary",
        "confidence_score": 0.95,
        "tags": ["fresh", "red", "ripe"]
    }
    
    rv = client.post("/api/images/assign/ingredient", json=assignment_data, headers=auth_header)
    
    assert rv.status_code in [200, 201]
    data = rv.get_json()
    assert "assignment_id" in data
    assert data["ingredient_name"] == "Fresh Tomatoes"
    assert data["confidence_score"] == 0.95
    assert "tags" in data
    assert len(data["tags"]) == 3


def test_assign_image_to_recipe_success(client, auth_header, monkeypatch):
    """Test successful image assignment to recipe"""
    from src.interface.controllers import image_management_controller as ctrl
    
    class FakeAssignImageToRecipeUseCase:
        def execute(self, user_uid, assignment_data):
            return {
                "assignment_id": "assign_124",
                "recipe_id": assignment_data["recipe_id"],
                "recipe_name": "Spaghetti Carbonara",
                "image_id": assignment_data["image_id"],
                "image_url": "https://storage.googleapis.com/images/carbonara_final.jpg",
                "thumbnail_url": "https://storage.googleapis.com/thumbs/carbonara_final.jpg",
                "assigned_at": "2025-08-19T15:30:00Z",
                "assignment_type": assignment_data.get("assignment_type", "finished_dish"),
                "step_number": assignment_data.get("step_number"),
                "tags": ["pasta", "italian", "creamy"],
                "featured": assignment_data.get("featured", False),
                "metadata": {
                    "lighting_quality": 0.88,
                    "composition_score": 0.91,
                    "color_vibrancy": 0.85
                }
            }
    
    monkeypatch.setattr(ctrl, "make_assign_image_to_recipe_use_case", lambda: FakeAssignImageToRecipeUseCase())
    
    assignment_data = {
        "recipe_id": "recipe_456",
        "image_id": "image_790",
        "assignment_type": "finished_dish", 
        "featured": True,
        "tags": ["pasta", "italian", "creamy"]
    }
    
    rv = client.post("/api/images/assign/recipe", json=assignment_data, headers=auth_header)
    
    assert rv.status_code in [200, 201]
    data = rv.get_json()
    assert data["recipe_name"] == "Spaghetti Carbonara"
    assert data["assignment_type"] == "finished_dish"
    assert data["featured"] is True
    assert "metadata" in data


def test_search_images_success(client, auth_header, monkeypatch):
    """Test successful image search"""
    from src.interface.controllers import image_management_controller as ctrl
    
    class FakeSearchImagesUseCase:
        def execute(self, user_uid, search_params):
            return {
                "images": [
                    {
                        "image_id": "image_001",
                        "url": "https://storage.googleapis.com/images/vegetables_001.jpg",
                        "thumbnail_url": "https://storage.googleapis.com/thumbs/vegetables_001.jpg",
                        "filename": "vegetables_mix.jpg",
                        "tags": ["vegetables", "colorful", "fresh"],
                        "uploaded_at": "2025-08-19T10:00:00Z",
                        "file_size": "2.1MB",
                        "dimensions": "1920x1080",
                        "content_type": "image/jpeg",
                        "assignments": [
                            {"type": "ingredient", "name": "Carrots", "confidence": 0.94},
                            {"type": "ingredient", "name": "Bell Peppers", "confidence": 0.89}
                        ]
                    },
                    {
                        "image_id": "image_002",
                        "url": "https://storage.googleapis.com/images/pasta_dish_002.jpg", 
                        "thumbnail_url": "https://storage.googleapis.com/thumbs/pasta_dish_002.jpg",
                        "filename": "pasta_carbonara_final.jpg",
                        "tags": ["pasta", "italian", "finished_dish"],
                        "uploaded_at": "2025-08-19T12:00:00Z",
                        "file_size": "1.8MB",
                        "dimensions": "1024x768",
                        "content_type": "image/jpeg",
                        "assignments": [
                            {"type": "recipe", "name": "Carbonara", "featured": True}
                        ]
                    }
                ],
                "pagination": {
                    "current_page": 1,
                    "total_pages": 3,
                    "total_results": 47,
                    "per_page": 20
                },
                "search_metadata": {
                    "query": search_params.get("query"),
                    "filters_applied": search_params.get("filters", {}),
                    "search_time": 0.15,
                    "suggestions": ["vegetables", "fresh", "colorful"]
                }
            }
    
    monkeypatch.setattr(ctrl, "make_search_images_use_case", lambda: FakeSearchImagesUseCase())
    
    # Test with search query
    search_params = {
        "query": "vegetables fresh",
        "filters": {
            "tags": ["vegetables", "fresh"],
            "content_type": "image/jpeg"
        },
        "page": 1,
        "limit": 20
    }
    
    rv = client.post("/api/images/search", json=search_params, headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "images" in data
    assert len(data["images"]) == 2
    assert "pagination" in data
    assert "search_metadata" in data
    assert data["search_metadata"]["query"] == "vegetables fresh"
    
    # Check image details
    vegetable_image = data["images"][0]
    assert "vegetables" in vegetable_image["tags"]
    assert len(vegetable_image["assignments"]) == 2
    
    pasta_image = data["images"][1]
    assert pasta_image["assignments"][0]["featured"] is True


def test_get_image_assignments_success(client, auth_header, monkeypatch):
    """Test successful retrieval of image assignments"""
    from src.interface.controllers import image_management_controller as ctrl
    
    class FakeGetImageAssignmentsUseCase:
        def execute(self, user_uid, image_id):
            return {
                "image_id": image_id,
                "image_url": "https://storage.googleapis.com/images/mixed_salad.jpg",
                "assignments": [
                    {
                        "assignment_id": "assign_001",
                        "type": "ingredient",
                        "target_id": "ingredient_lettuce",
                        "target_name": "Romaine Lettuce",
                        "confidence_score": 0.96,
                        "assigned_at": "2025-08-19T14:00:00Z",
                        "verified": True,
                        "tags": ["fresh", "green", "leafy"]
                    },
                    {
                        "assignment_id": "assign_002", 
                        "type": "ingredient",
                        "target_id": "ingredient_tomato",
                        "target_name": "Cherry Tomatoes",
                        "confidence_score": 0.91,
                        "assigned_at": "2025-08-19T14:05:00Z",
                        "verified": False,
                        "tags": ["red", "small", "fresh"]
                    },
                    {
                        "assignment_id": "assign_003",
                        "type": "recipe",
                        "target_id": "recipe_caesar_salad", 
                        "target_name": "Caesar Salad",
                        "assignment_type": "ingredient_photo",
                        "assigned_at": "2025-08-19T14:10:00Z",
                        "featured": False
                    }
                ],
                "total_assignments": 3,
                "verified_assignments": 1,
                "unverified_assignments": 2
            }
    
    monkeypatch.setattr(ctrl, "make_get_image_assignments_use_case", lambda: FakeGetImageAssignmentsUseCase())
    
    rv = client.get("/api/images/image_123/assignments", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["image_id"] == "image_123"
    assert "assignments" in data
    assert len(data["assignments"]) == 3
    assert data["total_assignments"] == 3
    assert data["verified_assignments"] == 1
    
    # Check assignment details
    lettuce_assignment = next(a for a in data["assignments"] if a["target_name"] == "Romaine Lettuce")
    assert lettuce_assignment["verified"] is True
    assert lettuce_assignment["confidence_score"] == 0.96


def test_image_management_endpoints_require_auth(client):
    """Test that image management endpoints require authentication"""
    endpoints = [
        ("POST", "/api/images/assign/ingredient", {"ingredient_id": "test", "image_id": "test"}),
        ("POST", "/api/images/assign/recipe", {"recipe_id": "test", "image_id": "test"}),
        ("POST", "/api/images/search", {"query": "test"}),
        ("GET", "/api/images/image_123/assignments", None)
    ]
    
    for method, endpoint, data in endpoints:
        if method == "POST":
            rv = client.post(endpoint, json=data)
        elif method == "GET":
            rv = client.get(endpoint)
            
        assert rv.status_code == 401


def test_assign_image_validation_errors(client, auth_header, monkeypatch):
    """Test image assignment validation errors"""
    from src.interface.controllers import image_management_controller as ctrl
    
    class FakeAssignImageToIngredientUseCase:
        def execute(self, user_uid, assignment_data):
            if not assignment_data.get("ingredient_id"):
                raise ValueError("Ingredient ID is required")
            if not assignment_data.get("image_id"):
                raise ValueError("Image ID is required")
            return {"assignment_id": "test"}
    
    monkeypatch.setattr(ctrl, "make_assign_image_to_ingredient_use_case", lambda: FakeAssignImageToIngredientUseCase())
    
    # Test missing ingredient_id
    rv = client.post("/api/images/assign/ingredient", json={"image_id": "test"}, headers=auth_header)
    assert rv.status_code in [400, 422, 500]
    
    # Test missing image_id  
    rv = client.post("/api/images/assign/ingredient", json={"ingredient_id": "test"}, headers=auth_header)
    assert rv.status_code in [400, 422, 500]


def test_search_images_with_filters(client, auth_header, monkeypatch):
    """Test image search with various filters"""
    from src.interface.controllers import image_management_controller as ctrl
    
    class FakeSearchImagesUseCase:
        def execute(self, user_uid, search_params):
            filters = search_params.get("filters", {})
            # Simulate filtered results
            return {
                "images": [
                    {
                        "image_id": "filtered_001",
                        "tags": filters.get("tags", []),
                        "content_type": filters.get("content_type", "image/jpeg"),
                        "url": "https://storage.googleapis.com/filtered/image.jpg"
                    }
                ],
                "pagination": {"total_results": 1},
                "search_metadata": {
                    "filters_applied": filters,
                    "results_filtered": True
                }
            }
    
    monkeypatch.setattr(ctrl, "make_search_images_use_case", lambda: FakeSearchImagesUseCase())
    
    # Test with multiple filters
    search_params = {
        "query": "italian food",
        "filters": {
            "tags": ["italian", "pasta"],
            "content_type": "image/jpeg",
            "size_range": "medium",
            "date_range": {
                "start": "2025-08-01",
                "end": "2025-08-19"
            }
        }
    }
    
    rv = client.post("/api/images/search", json=search_params, headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["search_metadata"]["results_filtered"] is True
    assert "italian" in data["search_metadata"]["filters_applied"]["tags"]


def test_get_image_assignments_not_found(client, auth_header, monkeypatch):
    """Test getting assignments for non-existent image"""
    from src.interface.controllers import image_management_controller as ctrl
    
    class FakeGetImageAssignmentsUseCase:
        def execute(self, user_uid, image_id):
            raise ValueError(f"Image {image_id} not found")
    
    monkeypatch.setattr(ctrl, "make_get_image_assignments_use_case", lambda: FakeGetImageAssignmentsUseCase())
    
    rv = client.get("/api/images/nonexistent_image/assignments", headers=auth_header)
    assert rv.status_code in [404, 500]


def test_search_images_empty_results(client, auth_header, monkeypatch):
    """Test image search with no results"""
    from src.interface.controllers import image_management_controller as ctrl
    
    class FakeSearchImagesUseCase:
        def execute(self, user_uid, search_params):
            return {
                "images": [],
                "pagination": {
                    "current_page": 1,
                    "total_pages": 0,
                    "total_results": 0,
                    "per_page": 20
                },
                "search_metadata": {
                    "query": search_params.get("query"),
                    "search_time": 0.05,
                    "suggestions": ["try different keywords", "remove filters"]
                }
            }
    
    monkeypatch.setattr(ctrl, "make_search_images_use_case", lambda: FakeSearchImagesUseCase())
    
    search_params = {"query": "nonexistent food item"}
    
    rv = client.post("/api/images/search", json=search_params, headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["images"] == []
    assert data["pagination"]["total_results"] == 0
    assert "suggestions" in data["search_metadata"]
