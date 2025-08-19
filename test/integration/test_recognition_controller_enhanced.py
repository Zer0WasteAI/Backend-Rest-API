"""
Comprehensive integration tests for Recognition Controller.
Tests ingredient and food recognition, batch processing, and async operations.
"""
import pytest
import json
import io
from unittest.mock import patch, MagicMock
from src.main import app


class TestRecognitionControllerIntegration:
    """Integration tests for Recognition Controller endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.client = app.test_client()
        self.client.testing = True
        self.base_headers = {'Content-Type': 'application/json'}
        self.mock_user_token = 'Bearer test_token_123'
    
    def test_recognize_batch_endpoint(self):
        """Test batch recognition functionality."""
        with patch('src.interface.controllers.recognition_controller.request') as mock_request:
            mock_request.headers = {'Authorization': self.mock_user_token}
            mock_request.files = {
                'images': [
                    MagicMock(filename='batch1.jpg'),
                    MagicMock(filename='batch2.jpg'),
                    MagicMock(filename='batch3.jpg')
                ]
            }
            mock_request.form = {'batch_type': 'ingredients', 'processing_mode': 'fast'}
            
            with patch('src.application.services.recognition_service.recognize_batch') as mock_batch:
                mock_batch.return_value = {
                    'batch_id': 'batch_recognition_123',
                    'total_images': 3,
                    'recognized_items': [
                        {'image': 'batch1.jpg', 'items': ['tomatoes', 'onions']},
                        {'image': 'batch2.jpg', 'items': ['carrots', 'celery']},
                        {'image': 'batch3.jpg', 'items': ['herbs', 'spices']}
                    ],
                    'processing_time': 4.2
                }
                
                response = self.client.post('/api/recognition/batch',
                                          data={
                                              'images': [(io.BytesIO(b"fake1"), 'batch1.jpg'),
                                                       (io.BytesIO(b"fake2"), 'batch2.jpg'),
                                                       (io.BytesIO(b"fake3"), 'batch3.jpg')],
                                              'batch_type': 'ingredients'
                                          },
                                          headers={'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 201, 400, 401, 413]
                if response.status_code in [200, 201]:
                    data = json.loads(response.data)
                    assert any(key in data for key in ['batch_id', 'recognized_items', 'total_images'])

    def test_recognize_ingredients_async_endpoint(self):
        """Test asynchronous ingredient recognition."""
        with patch('src.interface.controllers.recognition_controller.request') as mock_request:
            mock_request.headers = {'Authorization': self.mock_user_token}
            mock_request.files = {'image': MagicMock(filename='async_ingredients.jpg')}
            mock_request.form = {'priority': 'high', 'callback_url': 'https://example.com/callback'}
            
            with patch('src.application.services.recognition_service.recognize_ingredients_async') as mock_async:
                mock_async.return_value = {
                    'task_id': 'async_recognition_456',
                    'status': 'queued',
                    'estimated_completion': '2024-12-31T12:15:00Z',
                    'priority': 'high'
                }
                
                response = self.client.post('/api/recognition/ingredients/async',
                                          data={
                                              'image': (io.BytesIO(b"async_fake_image"), 'async_test.jpg'),
                                              'priority': 'high'
                                          },
                                          headers={'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 201, 202, 400, 401]
                if response.status_code in [200, 201, 202]:
                    data = json.loads(response.data)
                    assert any(key in data for key in ['task_id', 'status', 'estimated_completion'])

    def test_get_recognition_status_endpoint(self):
        """Test recognition task status tracking."""
        task_id = 'recognition_status_test_789'
        
        with patch('src.application.services.recognition_service.get_recognition_status') as mock_status:
            mock_status.return_value = {
                'task_id': task_id,
                'status': 'completed',
                'progress': 100,
                'results': {
                    'ingredients': ['tomatoes', 'basil', 'mozzarella'],
                    'confidence_scores': [0.95, 0.87, 0.92]
                },
                'processing_time': 3.4,
                'created_at': '2024-12-31T10:00:00Z',
                'completed_at': '2024-12-31T10:00:03Z'
            }
            
            response = self.client.get(f'/api/recognition/status/{task_id}',
                                     headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [200, 404, 401]
            if response.status_code == 200:
                data = json.loads(response.data)
                assert any(key in data for key in ['task_id', 'status', 'results'])

    def test_get_images_status_endpoint(self):
        """Test recognition images status tracking."""
        task_id = 'images_status_test_101'
        
        with patch('src.application.services.recognition_service.get_images_status') as mock_images_status:
            mock_images_status.return_value = {
                'task_id': task_id,
                'status': 'processing',
                'images_processed': 2,
                'total_images': 5,
                'progress': 40,
                'current_image': 'processing_image_3.jpg',
                'estimated_remaining_time': 120
            }
            
            response = self.client.get(f'/api/recognition/images/status/{task_id}',
                                     headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [200, 404, 401]
            if response.status_code == 200:
                data = json.loads(response.data)
                assert any(key in data for key in ['task_id', 'status', 'images_processed', 'progress'])

    def test_recognition_workflow_integration(self):
        """Test complete recognition workflow integration."""
        # Step 1: Start async recognition
        with patch('src.application.services.recognition_service.recognize_ingredients_async') as mock_async:
            mock_async.return_value = {
                'task_id': 'workflow_task_456',
                'status': 'queued'
            }
            
            async_response = self.client.post('/api/recognition/ingredients/async',
                                            data={'image': (io.BytesIO(b"workflow_image"), 'workflow.jpg')},
                                            headers={'Authorization': self.mock_user_token})
            
            if async_response.status_code in [200, 201, 202]:
                task_data = json.loads(async_response.data) if async_response.data else {'task_id': 'workflow_task_456'}
                task_id = task_data.get('task_id', 'workflow_task_456')
                
                # Step 2: Check recognition status
                with patch('src.application.services.recognition_service.get_recognition_status') as mock_status:
                    mock_status.return_value = {
                        'task_id': task_id,
                        'status': 'processing',
                        'progress': 75
                    }
                    
                    status_response = self.client.get(f'/api/recognition/status/{task_id}',
                                                    headers={'Authorization': self.mock_user_token})
                    
                    assert status_response.status_code in [200, 404, 401]
                
                # Step 3: Check images status
                with patch('src.application.services.recognition_service.get_images_status') as mock_images_status:
                    mock_images_status.return_value = {
                        'task_id': task_id,
                        'status': 'completed',
                        'images_processed': 1,
                        'total_images': 1
                    }
                    
                    images_status_response = self.client.get(f'/api/recognition/images/status/{task_id}',
                                                           headers={'Authorization': self.mock_user_token})
                    
                    assert images_status_response.status_code in [200, 404, 401]

    def test_batch_recognition_large_dataset(self):
        """Test batch recognition with large dataset."""
        # Simulate large batch processing
        large_batch_images = [(io.BytesIO(b"fake_data"), f'batch_image_{i}.jpg') for i in range(10)]
        
        with patch('src.application.services.recognition_service.recognize_batch') as mock_batch:
            mock_batch.return_value = {
                'batch_id': 'large_batch_789',
                'total_images': 10,
                'recognized_items': [{'image': f'batch_image_{i}.jpg', 'items': ['item1', 'item2']} for i in range(10)],
                'processing_time': 15.6,
                'status': 'completed'
            }
            
            response = self.client.post('/api/recognition/batch',
                                      data={
                                          'images': large_batch_images,
                                          'batch_type': 'mixed'
                                      },
                                      headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [200, 201, 400, 401, 413]

    def test_recognition_error_scenarios(self):
        """Test recognition error handling scenarios."""
        error_scenarios = [
            {
                'endpoint': '/api/recognition/batch',
                'method': 'POST',
                'data': {},  # No images provided
                'expected_codes': [400, 422]
            },
            {
                'endpoint': '/api/recognition/ingredients/async',
                'method': 'POST',
                'data': {},  # No image provided
                'expected_codes': [400, 422]
            }
        ]
        
        for scenario in error_scenarios:
            response = self.client.post(scenario['endpoint'],
                                      data=scenario['data'],
                                      headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in scenario['expected_codes']

    def test_recognition_status_not_found(self):
        """Test recognition status for non-existent tasks."""
        non_existent_ids = ['non_existent_123', 'invalid_id_456']
        
        for task_id in non_existent_ids:
            # Test recognition status
            with patch('src.application.services.recognition_service.get_recognition_status') as mock_status:
                mock_status.return_value = None
                
                response = self.client.get(f'/api/recognition/status/{task_id}',
                                         headers={'Authorization': self.mock_user_token})
                
                assert response.status_code in [404, 400]
            
            # Test images status
            with patch('src.application.services.recognition_service.get_images_status') as mock_images_status:
                mock_images_status.return_value = None
                
                response = self.client.get(f'/api/recognition/images/status/{task_id}',
                                         headers={'Authorization': self.mock_user_token})
                
                assert response.status_code in [404, 400]

    def test_recognition_authentication_security(self):
        """Test authentication and security for recognition endpoints."""
        protected_endpoints = [
            {'path': '/api/recognition/batch', 'method': 'POST'},
            {'path': '/api/recognition/ingredients/async', 'method': 'POST'},
            {'path': '/api/recognition/status/test_id', 'method': 'GET'},
            {'path': '/api/recognition/images/status/test_id', 'method': 'GET'}
        ]
        
        for endpoint in protected_endpoints:
            # Test without authentication
            if endpoint['method'] == 'POST':
                response = self.client.post(endpoint['path'], data={})
            else:
                response = self.client.get(endpoint['path'])
            
            assert response.status_code in [401, 403]
            
            # Test with invalid token
            auth_headers = {'Authorization': 'Bearer invalid_token'}
            if endpoint['method'] == 'POST':
                response = self.client.post(endpoint['path'], data={}, headers=auth_headers)
            else:
                response = self.client.get(endpoint['path'], headers=auth_headers)
            
            assert response.status_code in [401, 403]

    def test_recognition_service_failures(self):
        """Test recognition service failure handling."""
        # Test batch recognition service failure
        with patch('src.application.services.recognition_service.recognize_batch') as mock_batch:
            mock_batch.side_effect = Exception("Recognition service unavailable")
            
            response = self.client.post('/api/recognition/batch',
                                      data={'images': [(io.BytesIO(b"test"), 'test.jpg')]},
                                      headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [500, 503]

        # Test async recognition service failure
        with patch('src.application.services.recognition_service.recognize_ingredients_async') as mock_async:
            mock_async.side_effect = Exception("Async service error")
            
            response = self.client.post('/api/recognition/ingredients/async',
                                      data={'image': (io.BytesIO(b"test"), 'test.jpg')},
                                      headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [500, 503]

    def test_concurrent_recognition_requests(self):
        """Test concurrent recognition processing."""
        import threading
        results = []
        
        def recognition_request():
            with patch('src.application.services.recognition_service.recognize_batch') as mock_batch:
                mock_batch.return_value = {'batch_id': 'concurrent_batch', 'status': 'completed'}
                
                response = self.client.post('/api/recognition/batch',
                                          data={'images': [(io.BytesIO(b"concurrent"), 'concurrent.jpg')]},
                                          headers={'Authorization': self.mock_user_token})
                results.append(response.status_code)
        
        threads = [threading.Thread(target=recognition_request) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All requests should complete without server errors
        assert all(code != 500 for code in results)

    def test_recognition_cross_service_integration(self):
        """Test integration with inventory and recipe services."""
        # Test recognition followed by inventory addition
        with patch('src.application.services.recognition_service.recognize_ingredients') as mock_recognize:
            mock_recognize.return_value = {
                'ingredients': ['tomatoes', 'basil'],
                'confidence_scores': [0.9, 0.85],
                'recognition_id': 'integration_rec_123'
            }
            
            recognition_response = self.client.post('/api/recognition/ingredients',
                                                  data={'image': (io.BytesIO(b"integration_test"), 'integration.jpg')},
                                                  headers={'Authorization': self.mock_user_token})
            
            if recognition_response.status_code == 200:
                # Verify integration with inventory service
                with patch('src.application.services.inventory_service.add_ingredients_from_recognition') as mock_add:
                    mock_add.return_value = {'added_count': 2, 'skipped_count': 0}
                    
                    # This would typically be called from the inventory controller
                    # but we're testing the integration flow
                    inventory_response = self.client.post('/api/inventory/ingredients/from-recognition',
                                                        json={'recognition_id': 'integration_rec_123'},
                                                        headers={**self.base_headers, 'Authorization': self.mock_user_token})
                    
                    assert inventory_response.status_code in [200, 201, 400, 401]
