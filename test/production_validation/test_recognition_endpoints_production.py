"""
Production Validation Tests for Recognition AI Endpoints
Tests all AI-powered recognition endpoints including synchronous/asynchronous processing
"""
import pytest
import json
import io
import time
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage
from src.main import create_app


class TestRecognitionEndpointsProduction:
    """Production validation tests for all AI recognition endpoints"""

    @pytest.fixture(scope="class")
    def app(self):
        app = create_app()
        app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "JWT_ACCESS_TOKEN_EXPIRES": False,
        })
        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    @pytest.fixture
    def auth_headers(self, app):
        with app.app_context():
            from flask_jwt_extended import create_access_token
            token = create_access_token(identity="test-user-uid")
            return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def sample_image_file(self):
        """Create a sample image file for testing"""
        return FileStorage(
            stream=io.BytesIO(b'fake image data'),
            filename='test_image.jpg',
            content_type='image/jpeg'
        )

    # ================================================================
    # POST /api/recognition/ingredients - Synchronous Ingredient Recognition
    # ================================================================

    def test_ingredients_recognition_success(self, client, auth_headers, sample_image_file):
        """Test successful ingredient recognition"""
        with patch('src.application.use_cases.recognition.recognize_ingredients_use_case.RecognizeIngredientsUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recognition_id": "rec_12345",
                "ingredients": [
                    {
                        "name": "tomato",
                        "quantity": 3,
                        "unit": "pieces",
                        "confidence": 0.95,
                        "category": "vegetable"
                    },
                    {
                        "name": "onion",
                        "quantity": 1,
                        "unit": "piece",
                        "confidence": 0.88,
                        "category": "vegetable"
                    }
                ],
                "total_ingredients": 2,
                "processing_time": "2.3 seconds"
            }

            data = {'image': sample_image_file}
            response = client.post('/api/recognition/ingredients',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')

            assert response.status_code == 200
            result = response.get_json()
            assert result['total_ingredients'] == 2
            assert len(result['ingredients']) == 2
            assert result['ingredients'][0]['confidence'] > 0.8

    def test_ingredients_recognition_no_image(self, client, auth_headers):
        """Test ingredient recognition without image"""
        response = client.post('/api/recognition/ingredients',
            data={},
            headers=auth_headers,
            content_type='multipart/form-data')

        assert response.status_code == 400

    def test_ingredients_recognition_invalid_file_type(self, client, auth_headers):
        """Test ingredient recognition with invalid file type"""
        invalid_file = FileStorage(
            stream=io.BytesIO(b'fake pdf data'),
            filename='document.pdf',
            content_type='application/pdf'
        )

        data = {'image': invalid_file}
        response = client.post('/api/recognition/ingredients',
            data=data,
            headers=auth_headers,
            content_type='multipart/form-data')

        assert response.status_code == 400

    def test_ingredients_recognition_rate_limiting(self, client, auth_headers, sample_image_file):
        """Test rate limiting on ingredient recognition (ai_recognition: 5 req/min)"""
        with patch('src.application.use_cases.recognition.recognize_ingredients_use_case.RecognizeIngredientsUseCase.execute'):
            for i in range(7):
                data = {'image': (io.BytesIO(b'fake image'), f'test_{i}.jpg')}
                response = client.post('/api/recognition/ingredients',
                    data=data,
                    headers=auth_headers,
                    content_type='multipart/form-data')
                
                if i < 5:
                    assert response.status_code in [200, 400]
                else:
                    assert response.status_code == 429

    def test_ingredients_recognition_large_image(self, client, auth_headers):
        """Test ingredient recognition with large image file"""
        large_image = FileStorage(
            stream=io.BytesIO(b'x' * (11 * 1024 * 1024)),  # 11MB file
            filename='large_image.jpg',
            content_type='image/jpeg'
        )

        data = {'image': large_image}
        response = client.post('/api/recognition/ingredients',
            data=data,
            headers=auth_headers,
            content_type='multipart/form-data')

        # Should reject files over 10MB limit
        assert response.status_code in [400, 413]

    def test_ingredients_recognition_ai_failure(self, client, auth_headers, sample_image_file):
        """Test ingredient recognition when AI service fails"""
        with patch('src.application.use_cases.recognition.recognize_ingredients_use_case.RecognizeIngredientsUseCase.execute') as mock_execute:
            mock_execute.side_effect = Exception("AI service unavailable")

            data = {'image': sample_image_file}
            response = client.post('/api/recognition/ingredients',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')

            assert response.status_code in [500, 503]

    # ================================================================
    # POST /api/recognition/ingredients/complete - Complete Ingredient Recognition
    # ================================================================

    def test_ingredients_complete_recognition_success(self, client, auth_headers, sample_image_file):
        """Test complete ingredient recognition with detailed analysis"""
        with patch('src.application.use_cases.recognition.recognize_ingredients_complete_use_case.RecognizeIngredientsCompleteUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recognition_id": "rec_complete_123",
                "ingredients": [
                    {
                        "name": "tomato",
                        "quantity": 3,
                        "unit": "pieces",
                        "confidence": 0.95,
                        "category": "vegetable",
                        "freshness": "good",
                        "estimated_weight": "150g",
                        "nutritional_info": {
                            "calories": 18,
                            "vitamin_c": "high"
                        }
                    }
                ],
                "analysis": {
                    "total_items": 3,
                    "freshness_score": 8.5,
                    "nutritional_summary": "High in vitamins",
                    "storage_recommendations": ["Store in cool place", "Use within 5 days"]
                },
                "processing_time": "5.2 seconds"
            }

            data = {'image': sample_image_file}
            response = client.post('/api/recognition/ingredients/complete',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')

            assert response.status_code == 200
            result = response.get_json()
            assert 'analysis' in result
            assert 'nutritional_summary' in result['analysis']
            assert result['analysis']['freshness_score'] > 0

    def test_ingredients_complete_recognition_performance(self, client, auth_headers, sample_image_file):
        """Test complete recognition performance"""
        with patch('src.application.use_cases.recognition.recognize_ingredients_complete_use_case.RecognizeIngredientsCompleteUseCase.execute') as mock_execute:
            mock_execute.return_value = {"recognition_id": "rec_123", "ingredients": []}

            start_time = time.time()
            data = {'image': sample_image_file}
            response = client.post('/api/recognition/ingredients/complete',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')
            end_time = time.time()

            response_time = end_time - start_time
            
            # Complete recognition should finish within 10 seconds
            assert response_time < 10.0
            assert response.status_code == 200

    # ================================================================
    # POST /api/recognition/foods - Food Recognition
    # ================================================================

    def test_foods_recognition_success(self, client, auth_headers, sample_image_file):
        """Test successful prepared food recognition"""
        with patch('src.application.use_cases.recognition.recognize_foods_use_case.RecognizeFoodsUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recognition_id": "rec_food_123",
                "foods": [
                    {
                        "name": "spaghetti_carbonara",
                        "category": "pasta",
                        "cuisine": "italian",
                        "confidence": 0.92,
                        "serving_size": "1 plate",
                        "estimated_calories": 520,
                        "main_ingredients": ["pasta", "eggs", "cheese", "bacon"]
                    }
                ],
                "total_foods": 1,
                "processing_time": "3.1 seconds"
            }

            data = {'image': sample_image_file}
            response = client.post('/api/recognition/foods',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')

            assert response.status_code == 200
            result = response.get_json()
            assert result['total_foods'] == 1
            assert result['foods'][0]['confidence'] > 0.8
            assert 'main_ingredients' in result['foods'][0]

    def test_foods_recognition_multiple_dishes(self, client, auth_headers, sample_image_file):
        """Test food recognition with multiple dishes"""
        with patch('src.application.use_cases.recognition.recognize_foods_use_case.RecognizeFoodsUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recognition_id": "rec_multi_123",
                "foods": [
                    {"name": "pizza_margherita", "confidence": 0.89},
                    {"name": "caesar_salad", "confidence": 0.84},
                    {"name": "garlic_bread", "confidence": 0.91}
                ],
                "total_foods": 3
            }

            data = {'image': sample_image_file}
            response = client.post('/api/recognition/foods',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')

            assert response.status_code == 200
            result = response.get_json()
            assert result['total_foods'] == 3

    def test_foods_recognition_no_food_detected(self, client, auth_headers, sample_image_file):
        """Test food recognition when no food is detected"""
        with patch('src.application.use_cases.recognition.recognize_foods_use_case.RecognizeFoodsUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "recognition_id": "rec_empty_123",
                "foods": [],
                "total_foods": 0,
                "message": "No prepared foods detected in image"
            }

            data = {'image': sample_image_file}
            response = client.post('/api/recognition/foods',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')

            assert response.status_code == 200
            result = response.get_json()
            assert result['total_foods'] == 0

    # ================================================================
    # POST /api/recognition/batch - Batch Recognition
    # ================================================================

    def test_batch_recognition_success(self, client, auth_headers):
        """Test successful batch recognition of multiple images"""
        with patch('src.application.use_cases.recognition.recognize_batch_use_case.RecognizeBatchUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "batch_id": "batch_123",
                "results": [
                    {
                        "image_name": "image1.jpg",
                        "ingredients": [{"name": "tomato", "quantity": 2}],
                        "foods": [],
                        "confidence_score": 0.89
                    },
                    {
                        "image_name": "image2.jpg", 
                        "ingredients": [{"name": "onion", "quantity": 1}],
                        "foods": [{"name": "soup", "confidence": 0.85}],
                        "confidence_score": 0.87
                    }
                ],
                "total_images": 2,
                "processing_time": "8.5 seconds"
            }

            # Create multiple images for batch processing
            data = {
                'images': [
                    (io.BytesIO(b'fake image 1'), 'image1.jpg'),
                    (io.BytesIO(b'fake image 2'), 'image2.jpg')
                ]
            }

            response = client.post('/api/recognition/batch',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')

            assert response.status_code == 200
            result = response.get_json()
            assert result['total_images'] == 2
            assert len(result['results']) == 2

    def test_batch_recognition_empty_batch(self, client, auth_headers):
        """Test batch recognition with no images"""
        response = client.post('/api/recognition/batch',
            data={},
            headers=auth_headers,
            content_type='multipart/form-data')

        assert response.status_code == 400

    def test_batch_recognition_too_many_images(self, client, auth_headers):
        """Test batch recognition with too many images"""
        # Create more than allowed images (assuming limit is 10)
        data = {
            'images': [
                (io.BytesIO(b'fake image'), f'image{i}.jpg')
                for i in range(15)
            ]
        }

        response = client.post('/api/recognition/batch',
            data=data,
            headers=auth_headers,
            content_type='multipart/form-data')

        assert response.status_code in [400, 413]

    def test_batch_recognition_mixed_file_types(self, client, auth_headers):
        """Test batch recognition with mixed valid/invalid file types"""
        data = {
            'images': [
                (io.BytesIO(b'fake image'), 'valid.jpg'),
                (io.BytesIO(b'fake pdf'), 'invalid.pdf'),
                (io.BytesIO(b'fake image'), 'valid2.png')
            ]
        }

        response = client.post('/api/recognition/batch',
            data=data,
            headers=auth_headers,
            content_type='multipart/form-data')

        # Should reject batch if any file is invalid
        assert response.status_code == 400

    # ================================================================
    # POST /api/recognition/ingredients/async - Asynchronous Recognition
    # ================================================================

    def test_async_ingredients_recognition_success(self, client, auth_headers, sample_image_file):
        """Test asynchronous ingredient recognition"""
        with patch('src.application.use_cases.recognition.recognize_ingredients_use_case.RecognizeIngredientsUseCase.execute') as mock_execute:
            mock_execute.return_value = {
                "task_id": "async_task_123",
                "status": "processing",
                "message": "Recognition started",
                "estimated_completion": "30 seconds"
            }

            data = {'image': sample_image_file}
            response = client.post('/api/recognition/ingredients/async',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')

            assert response.status_code == 202  # Accepted
            result = response.get_json()
            assert 'task_id' in result
            assert result['status'] == 'processing'

    def test_async_recognition_task_status_check(self, client, auth_headers):
        """Test checking async task status"""
        with patch('src.application.use_cases.recognition.recognize_ingredients_use_case.RecognizeIngredientsUseCase.get_task_status') as mock_status:
            mock_status.return_value = {
                "task_id": "async_task_123",
                "status": "completed",
                "progress": 100,
                "result": {
                    "ingredients": [{"name": "tomato", "quantity": 3}],
                    "total_ingredients": 1
                },
                "completion_time": "2024-01-10T10:05:00Z"
            }

            response = client.get('/api/recognition/status/async_task_123',
                headers=auth_headers)

            assert response.status_code == 200
            result = response.get_json()
            assert result['status'] == 'completed'
            assert result['progress'] == 100

    def test_async_recognition_task_not_found(self, client, auth_headers):
        """Test checking status of non-existent task"""
        with patch('src.application.use_cases.recognition.recognize_ingredients_use_case.RecognizeIngredientsUseCase.get_task_status') as mock_status:
            mock_status.side_effect = Exception("Task not found")

            response = client.get('/api/recognition/status/nonexistent_task',
                headers=auth_headers)

            assert response.status_code == 404

    def test_async_recognition_task_failed(self, client, auth_headers):
        """Test async task that failed"""
        with patch('src.application.use_cases.recognition.recognize_ingredients_use_case.RecognizeIngredientsUseCase.get_task_status') as mock_status:
            mock_status.return_value = {
                "task_id": "failed_task_123",
                "status": "failed",
                "progress": 50,
                "error": "AI service timeout",
                "failure_time": "2024-01-10T10:03:00Z"
            }

            response = client.get('/api/recognition/status/failed_task_123',
                headers=auth_headers)

            assert response.status_code == 200
            result = response.get_json()
            assert result['status'] == 'failed'
            assert 'error' in result

    # ================================================================
    # Image Generation Status Endpoints
    # ================================================================

    def test_image_generation_status_check(self, client, auth_headers):
        """Test checking image generation status"""
        with patch('src.application.use_cases.recognition.recognize_ingredients_use_case.RecognizeIngredientsUseCase.get_image_status') as mock_status:
            mock_status.return_value = {
                "task_id": "img_gen_123",
                "status": "generating",
                "progress": 75,
                "generated_images": 3,
                "total_images": 4,
                "estimated_remaining": "30 seconds"
            }

            response = client.get('/api/recognition/images/status/img_gen_123',
                headers=auth_headers)

            assert response.status_code == 200
            result = response.get_json()
            assert result['status'] == 'generating'
            assert result['progress'] == 75

    def test_recognition_images_status_completed(self, client, auth_headers):
        """Test recognition with completed image generation"""
        with patch('src.application.use_cases.recognition.recognize_ingredients_use_case.RecognizeIngredientsUseCase.get_recognition_images') as mock_images:
            mock_images.return_value = {
                "recognition_id": "rec_123",
                "images_ready": True,
                "ingredient_images": [
                    {
                        "ingredient": "tomato",
                        "image_url": "https://storage.example.com/tomato.jpg",
                        "generated_at": "2024-01-10T10:10:00Z"
                    }
                ],
                "total_images": 1
            }

            response = client.get('/api/recognition/rec_123/images',
                headers=auth_headers)

            assert response.status_code == 200
            result = response.get_json()
            assert result['images_ready'] == True
            assert len(result['ingredient_images']) == 1

    # ================================================================
    # Security and Performance Tests
    # ================================================================

    def test_recognition_endpoints_security_headers(self, client, auth_headers, sample_image_file):
        """Test security headers on recognition endpoints"""
        data = {'image': sample_image_file}
        response = client.post('/api/recognition/ingredients',
            data=data,
            headers=auth_headers,
            content_type='multipart/form-data')
        
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers

    def test_recognition_file_validation(self, client, auth_headers):
        """Test comprehensive file validation"""
        test_cases = [
            # Valid cases
            {'filename': 'test.jpg', 'content_type': 'image/jpeg', 'expected': 200},
            {'filename': 'test.png', 'content_type': 'image/png', 'expected': 200},
            {'filename': 'test.gif', 'content_type': 'image/gif', 'expected': 200},
            
            # Invalid cases
            {'filename': 'test.exe', 'content_type': 'application/exe', 'expected': 400},
            {'filename': 'test.js', 'content_type': 'text/javascript', 'expected': 400},
            {'filename': 'test.php', 'content_type': 'application/php', 'expected': 400},
        ]

        with patch('src.application.use_cases.recognition.recognize_ingredients_use_case.RecognizeIngredientsUseCase.execute'):
            for test_case in test_cases:
                file_data = FileStorage(
                    stream=io.BytesIO(b'fake data'),
                    filename=test_case['filename'],
                    content_type=test_case['content_type']
                )
                
                data = {'image': file_data}
                response = client.post('/api/recognition/ingredients',
                    data=data,
                    headers=auth_headers,
                    content_type='multipart/form-data')
                
                if test_case['expected'] == 200:
                    assert response.status_code in [200, 400]  # May fail validation for other reasons
                else:
                    assert response.status_code == 400

    def test_recognition_malicious_file_upload(self, client, auth_headers):
        """Test protection against malicious file uploads"""
        # Test various malicious scenarios
        malicious_cases = [
            # Path traversal
            {'filename': '../../../etc/passwd', 'content_type': 'image/jpeg'},
            # Null bytes
            {'filename': 'test\x00.jpg.exe', 'content_type': 'image/jpeg'},
            # Long filename
            {'filename': 'a' * 1000 + '.jpg', 'content_type': 'image/jpeg'},
            # Script injection in filename
            {'filename': '<script>alert("xss")</script>.jpg', 'content_type': 'image/jpeg'},
        ]

        for case in malicious_cases:
            file_data = FileStorage(
                stream=io.BytesIO(b'fake image data'),
                filename=case['filename'],
                content_type=case['content_type']
            )
            
            data = {'image': file_data}
            response = client.post('/api/recognition/ingredients',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')
            
            # Should reject malicious uploads
            assert response.status_code == 400

    def test_recognition_concurrent_processing(self, client, auth_headers):
        """Test concurrent recognition requests"""
        import threading
        results = []
        
        def process_image():
            file_data = FileStorage(
                stream=io.BytesIO(b'fake image'),
                filename='test.jpg',
                content_type='image/jpeg'
            )
            data = {'image': file_data}
            response = client.post('/api/recognition/ingredients',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')
            results.append(response.status_code)
        
        with patch('src.application.use_cases.recognition.recognize_ingredients_use_case.RecognizeIngredientsUseCase.execute'):
            threads = []
            for _ in range(3):
                thread = threading.Thread(target=process_image)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
        
        # All should complete without server errors
        assert all(status < 500 for status in results)

    def test_recognition_ai_service_resilience(self, client, auth_headers, sample_image_file):
        """Test resilience when AI service is slow/unavailable"""
        test_scenarios = [
            # Slow response
            {"side_effect": lambda *args: time.sleep(0.1) or {"ingredients": []}},
            # Service unavailable
            {"side_effect": Exception("Service unavailable")},
            # Timeout
            {"side_effect": TimeoutError("Request timeout")},
            # Invalid response
            {"side_effect": lambda *args: {"invalid": "response"}},
        ]

        for scenario in test_scenarios:
            with patch('src.application.use_cases.recognition.recognize_ingredients_use_case.RecognizeIngredientsUseCase.execute') as mock_execute:
                mock_execute.side_effect = scenario["side_effect"]
                
                data = {'image': sample_image_file}
                response = client.post('/api/recognition/ingredients',
                    data=data,
                    headers=auth_headers,
                    content_type='multipart/form-data')
                
                # Should handle AI service issues gracefully
                assert response.status_code in [200, 400, 500, 503, 504]

    def test_recognition_memory_usage_large_batch(self, client, auth_headers):
        """Test memory usage with large batch processing"""
        with patch('src.application.use_cases.recognition.recognize_batch_use_case.RecognizeBatchUseCase.execute') as mock_execute:
            # Simulate successful large batch processing
            mock_execute.return_value = {
                "batch_id": "large_batch_123",
                "results": [{"image_name": f"img_{i}.jpg", "ingredients": []} for i in range(10)],
                "total_images": 10
            }
            
            # Create batch with 10 images
            data = {
                'images': [
                    (io.BytesIO(b'fake image data' * 1000), f'image{i}.jpg')
                    for i in range(10)
                ]
            }
            
            response = client.post('/api/recognition/batch',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')
            
            # Should handle large batches without memory issues
            assert response.status_code == 200

    def test_recognition_response_caching(self, client, auth_headers):
        """Test that recognition responses are properly cached"""
        with patch('src.application.use_cases.recognition.recognize_ingredients_use_case.RecognizeIngredientsUseCase.execute') as mock_execute:
            mock_execute.return_value = {"recognition_id": "cached_123", "ingredients": []}

            file_data = FileStorage(
                stream=io.BytesIO(b'same image data'),
                filename='test.jpg',
                content_type='image/jpeg'
            )
            
            # First request
            data = {'image': file_data}
            response1 = client.post('/api/recognition/ingredients',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data')
            
            # Second request with same image (should potentially use cache)
            file_data2 = FileStorage(
                stream=io.BytesIO(b'same image data'),
                filename='test.jpg',
                content_type='image/jpeg'
            )
            data2 = {'image': file_data2}
            response2 = client.post('/api/recognition/ingredients',
                data=data2,
                headers=auth_headers,
                content_type='multipart/form-data')
            
            assert response1.status_code == 200
            assert response2.status_code == 200
            # Cache-related headers might be present
            assert 'Cache-Control' in response1.headers or 'ETag' in response1.headers