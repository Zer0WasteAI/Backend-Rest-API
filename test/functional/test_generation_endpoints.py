"""
Functional tests for Generation endpoints
Tests end-to-end image generation status flows
"""
import pytest


def test_get_generation_status_success(client, auth_header, monkeypatch):
    """Test successful generation status retrieval"""
    from src.interface.controllers import generation_controller as ctrl
    
    class FakeGetGenerationStatusUseCase:
        def execute(self, user_uid):
            return {
                "generation_tasks": [
                    {
                        "task_id": "gen_123",
                        "type": "recipe_image",
                        "status": "completed",
                        "progress": 100,
                        "created_at": "2025-08-19T14:00:00Z",
                        "completed_at": "2025-08-19T14:05:00Z",
                        "result_url": "https://storage.googleapis.com/generated/recipe_image_123.jpg",
                        "recipe_name": "Chocolate Cake"
                    },
                    {
                        "task_id": "gen_124",
                        "type": "ingredient_visualization", 
                        "status": "processing",
                        "progress": 65,
                        "created_at": "2025-08-19T15:00:00Z",
                        "estimated_completion": "2025-08-19T15:08:00Z",
                        "ingredient_name": "Fresh Basil"
                    },
                    {
                        "task_id": "gen_125",
                        "type": "cooking_step",
                        "status": "queued",
                        "progress": 0,
                        "created_at": "2025-08-19T15:30:00Z",
                        "recipe_step": "Sautéing onions until golden"
                    }
                ],
                "total_tasks": 3,
                "completed_tasks": 1,
                "active_tasks": 1,
                "queued_tasks": 1,
                "credits_remaining": 47,
                "monthly_quota_used": 153,
                "monthly_quota_limit": 500
            }
    
    monkeypatch.setattr(ctrl, "make_get_generation_status_use_case", lambda: FakeGetGenerationStatusUseCase())
    
    rv = client.get("/api/generation/status", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "generation_tasks" in data
    assert len(data["generation_tasks"]) == 3
    assert data["total_tasks"] == 3
    assert data["completed_tasks"] == 1
    assert data["credits_remaining"] == 47
    
    # Check different task statuses
    completed_task = next(t for t in data["generation_tasks"] if t["status"] == "completed")
    assert completed_task["progress"] == 100
    assert "result_url" in completed_task
    
    processing_task = next(t for t in data["generation_tasks"] if t["status"] == "processing")
    assert processing_task["progress"] == 65
    assert "estimated_completion" in processing_task


def test_get_generation_images_success(client, auth_header, monkeypatch):
    """Test successful generation images gallery retrieval"""
    from src.interface.controllers import generation_controller as ctrl
    
    class FakeGetGenerationImagesUseCase:
        def execute(self, user_uid, page=1, limit=20, filter_type=None):
            return {
                "images": [
                    {
                        "image_id": "img_gen_001",
                        "task_id": "gen_123",
                        "type": "recipe_image",
                        "url": "https://storage.googleapis.com/generated/recipe_image_123.jpg",
                        "thumbnail_url": "https://storage.googleapis.com/thumbs/recipe_image_123.jpg",
                        "prompt": "Delicious chocolate cake with strawberries",
                        "created_at": "2025-08-19T14:05:00Z",
                        "recipe_name": "Chocolate Strawberry Cake",
                        "dimensions": "1024x1024",
                        "file_size": "2.1MB",
                        "model_version": "DALL-E 3",
                        "generation_time": 8.2
                    },
                    {
                        "image_id": "img_gen_002", 
                        "task_id": "gen_124",
                        "type": "ingredient_visualization",
                        "url": "https://storage.googleapis.com/generated/basil_visual_124.jpg",
                        "thumbnail_url": "https://storage.googleapis.com/thumbs/basil_visual_124.jpg", 
                        "prompt": "Fresh basil leaves on white background, professional food photography",
                        "created_at": "2025-08-19T15:08:00Z",
                        "ingredient_name": "Fresh Basil",
                        "dimensions": "512x512",
                        "file_size": "856KB",
                        "model_version": "Stable Diffusion XL",
                        "generation_time": 4.7
                    }
                ],
                "pagination": {
                    "current_page": 1,
                    "total_pages": 3,
                    "total_images": 45,
                    "per_page": 20,
                    "has_next": True,
                    "has_previous": False
                },
                "filters": {
                    "type": filter_type,
                    "available_types": ["recipe_image", "ingredient_visualization", "cooking_step", "meal_planner"]
                }
            }
    
    monkeypatch.setattr(ctrl, "make_get_generation_images_use_case", lambda: FakeGetGenerationImagesUseCase())
    
    rv = client.get("/api/generation/images", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "images" in data
    assert "pagination" in data
    assert len(data["images"]) == 2
    assert data["pagination"]["total_images"] == 45
    assert data["pagination"]["current_page"] == 1
    
    # Check image details
    recipe_image = next(img for img in data["images"] if img["type"] == "recipe_image")
    assert recipe_image["recipe_name"] == "Chocolate Strawberry Cake"
    assert recipe_image["dimensions"] == "1024x1024"
    assert "generation_time" in recipe_image
    
    ingredient_image = next(img for img in data["images"] if img["type"] == "ingredient_visualization")
    assert ingredient_image["ingredient_name"] == "Fresh Basil"
    assert ingredient_image["model_version"] == "Stable Diffusion XL"


def test_get_generation_status_empty_response(client, auth_header, monkeypatch):
    """Test generation status when no tasks exist"""
    from src.interface.controllers import generation_controller as ctrl
    
    class FakeGetGenerationStatusUseCase:
        def execute(self, user_uid):
            return {
                "generation_tasks": [],
                "total_tasks": 0,
                "completed_tasks": 0,
                "active_tasks": 0,
                "queued_tasks": 0,
                "credits_remaining": 100,
                "monthly_quota_used": 0,
                "monthly_quota_limit": 500
            }
    
    monkeypatch.setattr(ctrl, "make_get_generation_status_use_case", lambda: FakeGetGenerationStatusUseCase())
    
    rv = client.get("/api/generation/status", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["generation_tasks"] == []
    assert data["total_tasks"] == 0
    assert data["credits_remaining"] == 100


def test_get_generation_images_with_filters(client, auth_header, monkeypatch):
    """Test generation images with type filter"""
    from src.interface.controllers import generation_controller as ctrl
    
    class FakeGetGenerationImagesUseCase:
        def execute(self, user_uid, page=1, limit=20, filter_type=None):
            # Simulate filtering
            filtered_images = []
            if filter_type == "recipe_image":
                filtered_images = [
                    {
                        "image_id": "img_gen_001",
                        "type": "recipe_image",
                        "recipe_name": "Pasta Marinara",
                        "url": "https://storage.googleapis.com/generated/pasta_001.jpg"
                    }
                ]
            
            return {
                "images": filtered_images,
                "pagination": {
                    "current_page": 1,
                    "total_pages": 1,
                    "total_images": len(filtered_images),
                    "per_page": 20
                },
                "filters": {
                    "type": filter_type,
                    "available_types": ["recipe_image", "ingredient_visualization", "cooking_step"]
                }
            }
    
    monkeypatch.setattr(ctrl, "make_get_generation_images_use_case", lambda: FakeGetGenerationImagesUseCase())
    
    # Test with recipe_image filter
    rv = client.get("/api/generation/images?type=recipe_image", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert len(data["images"]) == 1
    assert data["images"][0]["type"] == "recipe_image"
    assert data["filters"]["type"] == "recipe_image"


def test_get_generation_images_pagination(client, auth_header, monkeypatch):
    """Test generation images with pagination parameters"""
    from src.interface.controllers import generation_controller as ctrl
    
    class FakeGetGenerationImagesUseCase:
        def execute(self, user_uid, page=1, limit=20, filter_type=None):
            # Simulate pagination
            return {
                "images": [
                    {"image_id": f"img_gen_{i}", "type": "recipe_image", "recipe_name": f"Recipe {i}"}
                    for i in range(1, 11)  # 10 images for page 2
                ],
                "pagination": {
                    "current_page": page,
                    "total_pages": 5,
                    "total_images": 50,
                    "per_page": limit,
                    "has_next": page < 5,
                    "has_previous": page > 1
                }
            }
    
    monkeypatch.setattr(ctrl, "make_get_generation_images_use_case", lambda: FakeGetGenerationImagesUseCase())
    
    # Test page 2 with 10 items per page
    rv = client.get("/api/generation/images?page=2&limit=10", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["pagination"]["current_page"] == 2
    assert data["pagination"]["per_page"] == 10
    assert data["pagination"]["has_previous"] is True
    assert data["pagination"]["has_next"] is True
    assert len(data["images"]) == 10


def test_generation_endpoints_require_auth(client):
    """Test that generation endpoints require authentication"""
    endpoints = [
        "/api/generation/status",
        "/api/generation/images"
    ]
    
    for endpoint in endpoints:
        rv = client.get(endpoint)
        assert rv.status_code == 401


def test_generation_status_error_handling(client, auth_header, monkeypatch):
    """Test generation status error handling"""
    from src.interface.controllers import generation_controller as ctrl
    
    class FakeGetGenerationStatusUseCase:
        def execute(self, user_uid):
            raise Exception("Generation service unavailable")
    
    monkeypatch.setattr(ctrl, "make_get_generation_status_use_case", lambda: FakeGetGenerationStatusUseCase())
    
    rv = client.get("/api/generation/status", headers=auth_header)
    assert rv.status_code == 500


def test_generation_images_error_handling(client, auth_header, monkeypatch):
    """Test generation images error handling"""
    from src.interface.controllers import generation_controller as ctrl
    
    class FakeGetGenerationImagesUseCase:
        def execute(self, user_uid, page=1, limit=20, filter_type=None):
            if page > 100:  # Invalid page number
                raise ValueError("Page number out of range")
            raise Exception("Image service unavailable")
    
    monkeypatch.setattr(ctrl, "make_get_generation_images_use_case", lambda: FakeGetGenerationImagesUseCase())
    
    rv = client.get("/api/generation/images", headers=auth_header)
    assert rv.status_code == 500
    
    # Test invalid page number
    rv = client.get("/api/generation/images?page=999", headers=auth_header)
    assert rv.status_code in [400, 422, 500]


def test_generation_quota_limits(client, auth_header, monkeypatch):
    """Test generation quota and credit limits"""
    from src.interface.controllers import generation_controller as ctrl
    
    class FakeGetGenerationStatusUseCase:
        def execute(self, user_uid):
            return {
                "generation_tasks": [],
                "total_tasks": 0,
                "completed_tasks": 0,
                "active_tasks": 0,
                "queued_tasks": 0,
                "credits_remaining": 0,  # No credits left
                "monthly_quota_used": 500,  # Quota exhausted
                "monthly_quota_limit": 500,
                "quota_reset_date": "2025-09-01T00:00:00Z",
                "messages": ["Monthly quota exhausted", "Credits depleted"]
            }
    
    monkeypatch.setattr(ctrl, "make_get_generation_status_use_case", lambda: FakeGetGenerationStatusUseCase())
    
    rv = client.get("/api/generation/status", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["credits_remaining"] == 0
    assert data["monthly_quota_used"] == data["monthly_quota_limit"]
    assert "quota_reset_date" in data
