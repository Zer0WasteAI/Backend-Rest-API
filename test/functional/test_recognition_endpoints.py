"""
Functional tests for Recognition endpoints
Tests end-to-end AI recognition flows
"""
import pytest
from io import BytesIO


def test_recognize_ingredients_success(client, auth_header, monkeypatch):
    """Test successful ingredient recognition"""
    from src.interface.controllers import recognition_controller as ctrl
    
    class FakeRecognitionUseCase:
        def execute(self, user_uid, image_file):
            return {
                "recognized_ingredients": [
                    {"name": "tomato", "confidence": 0.95, "quantity_estimate": 3},
                    {"name": "onion", "confidence": 0.87, "quantity_estimate": 2},
                    {"name": "garlic", "confidence": 0.82, "quantity_estimate": 1}
                ],
                "processing_time": 1.2,
                "message": "Recognition completed successfully"
            }
    
    monkeypatch.setattr(ctrl, "make_recognize_ingredients_use_case", lambda: FakeRecognitionUseCase())
    
    # Create fake image file
    fake_image = BytesIO(b"fake image data")
    fake_image.name = "ingredients.jpg"
    
    rv = client.post(
        "/api/recognition/ingredients",
        data={"file": (fake_image, "ingredients.jpg")},
        headers=auth_header,
        content_type="multipart/form-data"
    )
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "recognized_ingredients" in data
    assert len(data["recognized_ingredients"]) == 3
    assert data["recognized_ingredients"][0]["name"] == "tomato"


def test_recognize_ingredients_complete_success(client, auth_header, monkeypatch):
    """Test complete ingredient recognition with metadata"""
    from src.interface.controllers import recognition_controller as ctrl
    
    class FakeCompleteRecognitionUseCase:
        def execute(self, user_uid, image_file, include_metadata=True):
            return {
                "recognized_ingredients": [
                    {
                        "name": "apple", 
                        "confidence": 0.93,
                        "quantity_estimate": 5,
                        "estimated_expiry_days": 7,
                        "nutritional_info": {"calories": 52, "fiber": 2.4}
                    }
                ],
                "image_metadata": {
                    "dimensions": "1024x768",
                    "file_size": "2.1MB",
                    "format": "JPEG"
                },
                "processing_details": {
                    "model_version": "v2.1",
                    "processing_time": 2.3,
                    "confidence_threshold": 0.8
                }
            }
    
    monkeypatch.setattr(ctrl, "make_recognize_ingredients_complete_use_case", lambda: FakeCompleteRecognitionUseCase())
    
    fake_image = BytesIO(b"fake image data")
    fake_image.name = "complete_recognition.jpg"
    
    rv = client.post(
        "/api/recognition/ingredients/complete",
        data={"file": (fake_image, "complete_recognition.jpg")},
        headers=auth_header,
        content_type="multipart/form-data"
    )
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "recognized_ingredients" in data
    assert "image_metadata" in data
    assert "processing_details" in data


def test_recognize_foods_success(client, auth_header, monkeypatch):
    """Test successful food recognition"""
    from src.interface.controllers import recognition_controller as ctrl
    
    class FakeFoodRecognitionUseCase:
        def execute(self, user_uid, image_file):
            return {
                "recognized_foods": [
                    {"name": "pizza", "confidence": 0.92, "cuisine_type": "Italian"},
                    {"name": "salad", "confidence": 0.88, "cuisine_type": "Mediterranean"}
                ],
                "processing_time": 1.8
            }
    
    monkeypatch.setattr(ctrl, "make_recognize_foods_use_case", lambda: FakeFoodRecognitionUseCase())
    
    fake_image = BytesIO(b"fake food image")
    fake_image.name = "food_photo.jpg"
    
    rv = client.post(
        "/api/recognition/foods",
        data={"file": (fake_image, "food_photo.jpg")},
        headers=auth_header,
        content_type="multipart/form-data"
    )
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "recognized_foods" in data
    assert len(data["recognized_foods"]) == 2


def test_recognize_batch_success(client, auth_header, monkeypatch):
    """Test batch recognition of multiple images"""
    from src.interface.controllers import recognition_controller as ctrl
    
    class FakeBatchRecognitionUseCase:
        def execute(self, user_uid, image_files):
            return {
                "batch_results": [
                    {
                        "filename": "image1.jpg",
                        "recognized_items": [{"name": "banana", "confidence": 0.94}]
                    },
                    {
                        "filename": "image2.jpg", 
                        "recognized_items": [{"name": "orange", "confidence": 0.89}]
                    }
                ],
                "total_processed": 2,
                "total_items_found": 2
            }
    
    monkeypatch.setattr(ctrl, "make_recognize_batch_use_case", lambda: FakeBatchRecognitionUseCase())
    
    # Create multiple fake images
    fake_image1 = BytesIO(b"fake image 1")
    fake_image1.name = "image1.jpg"
    fake_image2 = BytesIO(b"fake image 2")
    fake_image2.name = "image2.jpg"
    
    rv = client.post(
        "/api/recognition/batch",
        data={
            "files": [
                (fake_image1, "image1.jpg"),
                (fake_image2, "image2.jpg")
            ]
        },
        headers=auth_header,
        content_type="multipart/form-data"
    )
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "batch_results" in data
    assert data["total_processed"] == 2


def test_recognize_ingredients_async_success(client, auth_header, monkeypatch):
    """Test asynchronous ingredient recognition"""
    from src.interface.controllers import recognition_controller as ctrl
    
    class FakeAsyncRecognitionUseCase:
        def execute(self, user_uid, image_file):
            return {
                "task_id": "async_task_123",
                "status": "processing",
                "estimated_completion": "2025-08-19T15:30:00Z",
                "message": "Recognition task started"
            }
    
    monkeypatch.setattr(ctrl, "make_recognize_ingredients_async_use_case", lambda: FakeAsyncRecognitionUseCase())
    
    fake_image = BytesIO(b"fake async image")
    fake_image.name = "async_recognition.jpg"
    
    rv = client.post(
        "/api/recognition/ingredients/async",
        data={"file": (fake_image, "async_recognition.jpg")},
        headers=auth_header,
        content_type="multipart/form-data"
    )
    
    assert rv.status_code == 202  # Accepted for processing
    data = rv.get_json()
    assert "task_id" in data
    assert data["status"] == "processing"


def test_get_recognition_status_success(client, auth_header, monkeypatch):
    """Test getting recognition task status"""
    from src.interface.controllers import recognition_controller as ctrl
    
    class FakeStatusUseCase:
        def execute(self, user_uid, task_id):
            return {
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "result": {
                    "recognized_ingredients": [
                        {"name": "lettuce", "confidence": 0.91}
                    ]
                },
                "completed_at": "2025-08-19T15:35:00Z"
            }
    
    monkeypatch.setattr(ctrl, "make_get_recognition_status_use_case", lambda: FakeStatusUseCase())
    
    rv = client.get("/api/recognition/status/async_task_123", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["task_id"] == "async_task_123"
    assert data["status"] == "completed"
    assert "result" in data


def test_get_images_status_success(client, auth_header, monkeypatch):
    """Test getting image processing status"""
    from src.interface.controllers import recognition_controller as ctrl
    
    class FakeImagesStatusUseCase:
        def execute(self, user_uid):
            return {
                "processing_images": [
                    {"image_id": "img_001", "status": "processing", "progress": 75},
                    {"image_id": "img_002", "status": "queued", "progress": 0}
                ],
                "completed_today": 5,
                "queue_length": 2
            }
    
    monkeypatch.setattr(ctrl, "make_get_images_status_use_case", lambda: FakeImagesStatusUseCase())
    
    rv = client.get("/api/recognition/images/status", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "processing_images" in data
    assert data["completed_today"] == 5


def test_get_recognition_images_success(client, auth_header, monkeypatch):
    """Test getting recognition images gallery"""
    from src.interface.controllers import recognition_controller as ctrl
    
    class FakeRecognitionImagesUseCase:
        def execute(self, user_uid, limit=10):
            return {
                "images": [
                    {
                        "image_id": "img_001",
                        "thumbnail_url": "https://storage.googleapis.com/thumbs/img_001.jpg",
                        "full_url": "https://storage.googleapis.com/images/img_001.jpg",
                        "recognition_results": [{"name": "carrot", "confidence": 0.93}],
                        "created_at": "2025-08-19T14:00:00Z"
                    }
                ],
                "total_images": 15,
                "page_size": 10
            }
    
    monkeypatch.setattr(ctrl, "make_get_recognition_images_use_case", lambda: FakeRecognitionImagesUseCase())
    
    rv = client.get("/api/recognition/images", headers=auth_header)
    
    assert rv.status_code == 200
    data = rv.get_json()
    assert "images" in data
    assert len(data["images"]) == 1
    assert data["total_images"] == 15


def test_recognition_endpoints_require_auth(client):
    """Test that recognition endpoints require authentication"""
    fake_image = BytesIO(b"fake image")
    fake_image.name = "test.jpg"
    
    endpoints = [
        ("POST", "/api/recognition/ingredients"),
        ("POST", "/api/recognition/ingredients/complete"),
        ("POST", "/api/recognition/foods"),
        ("POST", "/api/recognition/batch"),
        ("POST", "/api/recognition/ingredients/async"),
        ("GET", "/api/recognition/status/task123"),
        ("GET", "/api/recognition/images/status"),
        ("GET", "/api/recognition/images")
    ]
    
    for method, endpoint in endpoints:
        if method == "POST" and "/recognition/" in endpoint and endpoint != "/api/recognition/status/task123":
            rv = client.post(
                endpoint,
                data={"file": (fake_image, "test.jpg")},
                content_type="multipart/form-data"
            )
        elif method == "GET":
            rv = client.get(endpoint)
        
        assert rv.status_code == 401


def test_recognition_file_validation(client, auth_header):
    """Test recognition endpoint file validation"""
    # Test missing file
    rv = client.post(
        "/api/recognition/ingredients",
        data={},
        headers=auth_header,
        content_type="multipart/form-data"
    )
    assert rv.status_code in [400, 422]
    
    # Test invalid file type
    fake_text_file = BytesIO(b"not an image")
    fake_text_file.name = "document.txt"
    
    rv = client.post(
        "/api/recognition/ingredients",
        data={"file": (fake_text_file, "document.txt")},
        headers=auth_header,
        content_type="multipart/form-data"
    )
    assert rv.status_code in [400, 422]
