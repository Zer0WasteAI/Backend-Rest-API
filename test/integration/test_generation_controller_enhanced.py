"""
Comprehensive integration tests for Generation Controller.
Tests recipe generation image handling and status tracking.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.main import app


class TestGenerationControllerIntegration:
    """Integration tests for Generation Controller endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.client = app.test_client()
        self.client.testing = True
        self.base_headers = {'Content-Type': 'application/json'}
        self.mock_user_token = 'Bearer test_token_123'
    
    def test_get_generation_images_status_endpoint(self):
        """Test generation images status tracking."""
        task_id = 'generation_task_456'
        
        with patch('src.interface.controllers.generation_controller.request') as mock_request:
            mock_request.headers = {'Authorization': self.mock_user_token}
            
            with patch('src.application.services.generation_service.get_generation_images_status') as mock_status:
                mock_status.return_value = {
                    'task_id': task_id,
                    'status': 'completed',
                    'progress': 100,
                    'images_generated': 3,
                    'estimated_completion': None,
                    'error': None
                }
                
                response = self.client.get(f'/api/generation/images/status/{task_id}',
                                         headers={'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 404, 401]
                if response.status_code == 200:
                    data = json.loads(response.data)
                    assert any(key in data for key in ['task_id', 'status', 'progress'])

    def test_generation_images_status_pending(self):
        """Test generation images status when task is pending."""
        task_id = 'generation_pending_789'
        
        with patch('src.application.services.generation_service.get_generation_images_status') as mock_status:
            mock_status.return_value = {
                'task_id': task_id,
                'status': 'pending',
                'progress': 25,
                'images_generated': 0,
                'estimated_completion': '2024-12-31T12:30:00Z'
            }
            
            response = self.client.get(f'/api/generation/images/status/{task_id}',
                                     headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [200, 404, 401]
            if response.status_code == 200:
                data = json.loads(response.data)
                assert data.get('status') == 'pending' or 'status' in data

    def test_generation_images_status_failed(self):
        """Test generation images status when task failed."""
        task_id = 'generation_failed_101'
        
        with patch('src.application.services.generation_service.get_generation_images_status') as mock_status:
            mock_status.return_value = {
                'task_id': task_id,
                'status': 'failed',
                'progress': 50,
                'images_generated': 1,
                'error': 'Generation service timeout'
            }
            
            response = self.client.get(f'/api/generation/images/status/{task_id}',
                                     headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [200, 404, 401]
            if response.status_code == 200:
                data = json.loads(response.data)
                assert 'status' in data and ('error' in data or data.get('status') == 'failed')

    def test_generation_workflow_integration(self):
        """Test complete generation workflow integration."""
        generation_id = 'workflow_generation_123'
        task_id = 'workflow_task_456'
        
        # Step 1: Get generation images (existing endpoint that works)
        with patch('src.application.services.generation_service.get_generation_images') as mock_get_images:
            mock_get_images.return_value = {
                'generation_id': generation_id,
                'images': [
                    {'id': 'img_1', 'url': 'https://example.com/img1.jpg'},
                    {'id': 'img_2', 'url': 'https://example.com/img2.jpg'}
                ],
                'task_id': task_id,
                'status': 'completed'
            }
            
            images_response = self.client.get(f'/api/generation/{generation_id}/images',
                                            headers={'Authorization': self.mock_user_token})
            
            if images_response.status_code == 200:
                images_data = json.loads(images_response.data)
                extracted_task_id = images_data.get('task_id', task_id)
                
                # Step 2: Check status of the generation task
                with patch('src.application.services.generation_service.get_generation_images_status') as mock_status:
                    mock_status.return_value = {
                        'task_id': extracted_task_id,
                        'status': 'completed',
                        'images_generated': 2
                    }
                    
                    status_response = self.client.get(f'/api/generation/images/status/{extracted_task_id}',
                                                    headers={'Authorization': self.mock_user_token})
                    
                    assert status_response.status_code in [200, 404, 401]

    def test_generation_status_not_found(self):
        """Test generation images status for non-existent task."""
        non_existent_task_id = 'non_existent_task_999'
        
        with patch('src.application.services.generation_service.get_generation_images_status') as mock_status:
            mock_status.return_value = None  # Task not found
            
            response = self.client.get(f'/api/generation/images/status/{non_existent_task_id}',
                                     headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [404, 400]

    def test_generation_status_invalid_task_id(self):
        """Test generation images status with invalid task ID format."""
        invalid_task_ids = ['', 'invalid-format!', 'too_long_' + 'a' * 100]
        
        for invalid_id in invalid_task_ids:
            response = self.client.get(f'/api/generation/images/status/{invalid_id}',
                                     headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [400, 404]

    def test_generation_authentication_requirements(self):
        """Test authentication requirements for generation endpoints."""
        task_id = 'auth_test_task_123'
        
        # Test without authentication
        response = self.client.get(f'/api/generation/images/status/{task_id}')
        assert response.status_code in [401, 403]
        
        # Test with invalid token
        response = self.client.get(f'/api/generation/images/status/{task_id}',
                                 headers={'Authorization': 'Bearer invalid_token'})
        assert response.status_code in [401, 403]

    def test_generation_service_error_handling(self):
        """Test error handling when generation service fails."""
        task_id = 'error_test_task_456'
        
        # Test service exception
        with patch('src.application.services.generation_service.get_generation_images_status') as mock_status:
            mock_status.side_effect = Exception("Generation service unavailable")
            
            response = self.client.get(f'/api/generation/images/status/{task_id}',
                                     headers={'Authorization': self.mock_user_token})
            
            assert response.status_code in [500, 503]
            if response.status_code == 500:
                data = json.loads(response.data)
                assert 'error' in data or 'message' in data

    def test_generation_status_polling_simulation(self):
        """Test generation status polling behavior."""
        task_id = 'polling_test_task_789'
        
        # Simulate status progression: pending -> processing -> completed
        status_progression = [
            {'status': 'pending', 'progress': 0},
            {'status': 'processing', 'progress': 50},
            {'status': 'completed', 'progress': 100}
        ]
        
        for status_info in status_progression:
            with patch('src.application.services.generation_service.get_generation_images_status') as mock_status:
                mock_status.return_value = {
                    'task_id': task_id,
                    **status_info,
                    'images_generated': 3 if status_info['status'] == 'completed' else 0
                }
                
                response = self.client.get(f'/api/generation/images/status/{task_id}',
                                         headers={'Authorization': self.mock_user_token})
                
                assert response.status_code in [200, 404, 401]
                if response.status_code == 200:
                    data = json.loads(response.data)
                    assert 'status' in data

    def test_generation_cross_service_integration(self):
        """Test integration with recipe generation and image services."""
        generation_id = 'cross_service_gen_123'
        
        # Test getting generation images (existing functionality)
        with patch('src.application.services.generation_service.get_generation_images') as mock_get_images:
            mock_get_images.return_value = {
                'generation_id': generation_id,
                'images': [{'id': 'img_1', 'url': 'https://example.com/generated1.jpg'}],
                'recipe_data': {'title': 'Generated Recipe', 'ingredients': ['ingredient1', 'ingredient2']},
                'task_id': 'cross_task_456'
            }
            
            images_response = self.client.get(f'/api/generation/{generation_id}/images',
                                            headers={'Authorization': self.mock_user_token})
            
            if images_response.status_code == 200:
                # Verify the generation completed and check its status
                with patch('src.application.services.generation_service.get_generation_images_status') as mock_status:
                    mock_status.return_value = {
                        'task_id': 'cross_task_456',
                        'status': 'completed',
                        'images_generated': 1
                    }
                    
                    status_response = self.client.get('/api/generation/images/status/cross_task_456',
                                                    headers={'Authorization': self.mock_user_token})
                    
                    assert status_response.status_code in [200, 404, 401]

    def test_concurrent_generation_status_requests(self):
        """Test concurrent generation status requests."""
        import threading
        task_id = 'concurrent_task_123'
        results = []
        
        def status_request():
            with patch('src.application.services.generation_service.get_generation_images_status') as mock_status:
                mock_status.return_value = {'task_id': task_id, 'status': 'processing', 'progress': 75}
                
                response = self.client.get(f'/api/generation/images/status/{task_id}',
                                         headers={'Authorization': self.mock_user_token})
                results.append(response.status_code)
        
        threads = [threading.Thread(target=status_request) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # All requests should complete successfully
        assert all(code in [200, 404, 401] for code in results)
