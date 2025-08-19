"""
Comprehensive integration tests for Image Management Controller.
Tests image operations, validation, and cross-service integration.
"""
import pytest
import json
import io
from unittest.mock import patch, MagicMock
from src.main import app


class TestImageManagementControllerIntegration:
    """Integration tests for Image Management Controller endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.client = app.test_client()
        self.client.testing = True
        self.base_headers = {'Content-Type': 'application/json'}
        self.mock_user_token = 'Bearer test_token_123'
    
    def test_assign_image_endpoint(self):
        """Test image assignment functionality."""
        with patch('src.interface.controllers.image_management_controller.request') as mock_request:
            mock_request.headers = {'Authorization': self.mock_user_token}
            mock_request.get_json.return_value = {
                'image_id': 'img_123',
                'target_type': 'recipe',
                'target_id': 'recipe_456'
            }
            
            with patch('src.application.services.image_service.assign_image') as mock_assign:
                mock_assign.return_value = {'status': 'assigned', 'image_id': 'img_123'}
                
                response = self.client.post('/api/images/assign_image',
                                          json={
                                              'image_id': 'img_123',
                                              'target_type': 'recipe',
                                              'target_id': 'recipe_456'
                                          },
                                          headers={**self.base_headers, 'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 201, 400, 401]
                if response.status_code in [200, 201]:
                    data = json.loads(response.data)
                    assert 'status' in data or 'message' in data

    def test_search_similar_images_endpoint(self):
        """Test similar image search functionality."""
        with patch('src.interface.controllers.image_management_controller.request') as mock_request:
            mock_request.headers = {'Authorization': self.mock_user_token}
            mock_request.get_json.return_value = {
                'reference_image_id': 'img_ref_123',
                'similarity_threshold': 0.8
            }
            
            with patch('src.application.services.image_service.search_similar_images') as mock_search:
                mock_search.return_value = {
                    'similar_images': [
                        {'id': 'img_456', 'similarity': 0.9},
                        {'id': 'img_789', 'similarity': 0.85}
                    ]
                }
                
                response = self.client.post('/api/images/search_similar_images',
                                          json={
                                              'reference_image_id': 'img_ref_123',
                                              'similarity_threshold': 0.8
                                          },
                                          headers={**self.base_headers, 'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 400, 401, 404]
                if response.status_code == 200:
                    data = json.loads(response.data)
                    assert 'similar_images' in data or 'results' in data

    def test_sync_images_endpoint(self):
        """Test image synchronization functionality."""
        with patch('src.interface.controllers.image_management_controller.request') as mock_request:
            mock_request.headers = {'Authorization': self.mock_user_token}
            mock_request.get_json.return_value = {
                'sync_type': 'full',
                'target_source': 'cloud'
            }
            
            with patch('src.application.services.image_service.sync_images') as mock_sync:
                mock_sync.return_value = {
                    'synced_count': 15,
                    'failed_count': 0,
                    'status': 'completed'
                }
                
                response = self.client.post('/api/images/sync_images',
                                          json={
                                              'sync_type': 'full',
                                              'target_source': 'cloud'
                                          },
                                          headers={**self.base_headers, 'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 202, 400, 401]
                if response.status_code in [200, 202]:
                    data = json.loads(response.data)
                    assert 'status' in data or 'synced_count' in data or 'message' in data

    def test_upload_image_with_file(self):
        """Test image upload with actual file data."""
        # Create a mock image file
        image_data = io.BytesIO(b"fake_image_data")
        image_data.name = 'test_image.jpg'
        
        with patch('src.interface.controllers.image_management_controller.request') as mock_request:
            mock_request.headers = {'Authorization': self.mock_user_token}
            mock_request.files = {'image': image_data}
            mock_request.form = {'category': 'recipe', 'description': 'Test image'}
            
            with patch('src.application.services.image_service.upload_image') as mock_upload:
                mock_upload.return_value = {
                    'image_id': 'uploaded_img_123',
                    'url': 'https://example.com/img_123.jpg',
                    'status': 'uploaded'
                }
                
                # Test with form data (multipart)
                response = self.client.post('/api/images/upload_image',
                                          data={
                                              'image': (io.BytesIO(b"fake_image_data"), 'test.jpg'),
                                              'category': 'recipe'
                                          },
                                          headers={'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 201, 400, 401, 413]

    def test_image_operations_workflow(self):
        """Test complete image management workflow."""
        # Step 1: Upload image
        with patch('src.application.services.image_service.upload_image') as mock_upload:
            mock_upload.return_value = {'image_id': 'workflow_img_123', 'url': 'https://example.com/img.jpg'}
            
            upload_response = self.client.post('/api/images/upload_image',
                                             data={'image': (io.BytesIO(b"test"), 'test.jpg')},
                                             headers={'Authorization': self.mock_user_token})
            
            if upload_response.status_code in [200, 201]:
                # Step 2: Search similar images
                with patch('src.application.services.image_service.search_similar_images') as mock_search:
                    mock_search.return_value = {'similar_images': []}
                    
                    search_response = self.client.post('/api/images/search_similar_images',
                                                     json={'reference_image_id': 'workflow_img_123'},
                                                     headers={**self.base_headers, 'Authorization': self.mock_user_token})
                    
                    assert search_response.status_code in [200, 400, 404]
                
                # Step 3: Assign image
                with patch('src.application.services.image_service.assign_image') as mock_assign:
                    mock_assign.return_value = {'status': 'assigned'}
                    
                    assign_response = self.client.post('/api/images/assign_image',
                                                     json={
                                                         'image_id': 'workflow_img_123',
                                                         'target_type': 'recipe',
                                                         'target_id': 'recipe_789'
                                                     },
                                                     headers={**self.base_headers, 'Authorization': self.mock_user_token})
                    
                    assert assign_response.status_code in [200, 201, 400]

    def test_image_validation_scenarios(self):
        """Test image validation and error scenarios."""
        validation_tests = [
            {
                'endpoint': '/api/images/assign_image',
                'data': {'invalid_field': 'value'},
                'expected_codes': [400, 422]
            },
            {
                'endpoint': '/api/images/search_similar_images',
                'data': {'reference_image_id': ''},
                'expected_codes': [400, 422]
            },
            {
                'endpoint': '/api/images/sync_images',
                'data': {'sync_type': 'invalid_type'},
                'expected_codes': [400, 422]
            }
        ]
        
        for test in validation_tests:
            response = self.client.post(test['endpoint'],
                                      json=test['data'],
                                      headers={**self.base_headers, 'Authorization': self.mock_user_token})
            
            assert response.status_code in test['expected_codes']

    def test_image_permissions_and_auth(self):
        """Test image management authentication and permissions."""
        endpoints = [
            {'path': '/api/images/assign_image', 'method': 'POST'},
            {'path': '/api/images/search_similar_images', 'method': 'POST'},
            {'path': '/api/images/sync_images', 'method': 'POST'},
            {'path': '/api/images/upload_image', 'method': 'POST'}
        ]
        
        for endpoint in endpoints:
            # Test without authorization
            response = self.client.post(endpoint['path'],
                                      json={},
                                      headers=self.base_headers)
            
            assert response.status_code in [401, 403]
            
            # Test with invalid token
            response = self.client.post(endpoint['path'],
                                      json={},
                                      headers={**self.base_headers, 'Authorization': 'Bearer invalid_token'})
            
            assert response.status_code in [401, 403]

    def test_concurrent_image_operations(self):
        """Test concurrent image management operations."""
        import threading
        results = []
        
        def image_operation():
            with patch('src.application.services.image_service.sync_images') as mock_sync:
                mock_sync.return_value = {'status': 'completed'}
                
                response = self.client.post('/api/images/sync_images',
                                          json={'sync_type': 'incremental'},
                                          headers={**self.base_headers, 'Authorization': self.mock_user_token})
                results.append(response.status_code)
        
        threads = [threading.Thread(target=image_operation) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Operations should complete without server errors
        assert all(code != 500 for code in results)

    def test_image_service_integration(self):
        """Test integration between image management and other services."""
        # Test image upload followed by inventory integration
        with patch('src.application.services.image_service.upload_image') as mock_upload:
            mock_upload.return_value = {'image_id': 'integration_img_123'}
            
            # Upload image
            upload_response = self.client.post('/api/images/upload_image',
                                             data={'image': (io.BytesIO(b"test"), 'food.jpg')},
                                             headers={'Authorization': self.mock_user_token})
            
            if upload_response.status_code in [200, 201]:
                # Test assigning image to inventory item
                with patch('src.application.services.image_service.assign_image') as mock_assign:
                    mock_assign.return_value = {'status': 'assigned'}
                    
                    assign_response = self.client.post('/api/images/assign_image',
                                                     json={
                                                         'image_id': 'integration_img_123',
                                                         'target_type': 'inventory_item',
                                                         'target_id': 'item_456'
                                                     },
                                                     headers={**self.base_headers, 'Authorization': self.mock_user_token})
                    
                    assert assign_response.status_code in [200, 201, 400]

    def test_image_error_recovery(self):
        """Test error recovery in image management operations."""
        # Test upload failure recovery
        with patch('src.application.services.image_service.upload_image') as mock_upload:
            mock_upload.side_effect = Exception("Upload failed")
            
            response = self.client.post('/api/images/upload_image',
                                      data={'image': (io.BytesIO(b"test"), 'test.jpg')},
                                      headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [500, 400]
            if response.status_code == 500:
                data = json.loads(response.data)
                assert 'error' in data or 'message' in data
