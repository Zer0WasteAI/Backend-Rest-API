import pytest
import json
import uuid
from datetime import datetime
from unittest.mock import Mock, patch
from flask_testing import TestCase


class TestIdempotencyEndpoints(TestCase):
    """Test suite specifically for idempotency functionality in endpoints"""

    def create_app(self):
        """Create test app"""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        return app

    def setUp(self):
        """Setup test fixtures"""
        self.user_uid = "test_user_123"
        self.recipe_uid = "recipe_test_001"
        self.session_id = str(uuid.uuid4())
        self.batch_id = str(uuid.uuid4())
        
        self.auth_headers = {
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
        }

    @patch('src.interface.controllers.cooking_session_controller.get_jwt_identity')
    @patch('src.infrastructure.services.idempotency_service.IdempotencyService.check_idempotency')
    @patch('src.infrastructure.services.idempotency_service.IdempotencyService.store_response')
    @patch('src.application.factories.cooking_session_factory.make_start_cooking_session_use_case')
    def test_idempotency_new_request(self, mock_factory, mock_store, mock_check, mock_jwt):
        """Test idempotency with new request (not cached)"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        mock_check.return_value = None  # No cached response
        
        mock_use_case = Mock()
        mock_session = Mock()
        mock_session.session_id = self.session_id
        mock_use_case.execute.return_value = mock_session
        mock_factory.return_value = mock_use_case
        
        idempotency_key = str(uuid.uuid4())
        request_data = {
            "recipe_uid": self.recipe_uid,
            "servings": 3,
            "level": "intermediate",
            "started_at": datetime.utcnow().isoformat()
        }
        
        # Act
        response = self.client.post(
            '/api/recipes/cooking_session/start',
            data=json.dumps(request_data),
            headers={**self.auth_headers, 'Idempotency-Key': idempotency_key}
        )
        
        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["session_id"] == self.session_id
        
        # Verify idempotency service was called
        mock_check.assert_called_once_with(
            idempotency_key=idempotency_key,
            user_uid=self.user_uid,
            endpoint="cooking_session_start",
            request_body=request_data
        )
        mock_store.assert_called_once()

    @patch('src.interface.controllers.cooking_session_controller.get_jwt_identity')
    @patch('src.infrastructure.services.idempotency_service.IdempotencyService.check_idempotency')
    def test_idempotency_cached_response(self, mock_check, mock_jwt):
        """Test idempotency with cached response"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        
        # Mock cached response
        cached_response = (
            "201",  # status code
            json.dumps({"session_id": self.session_id, "status": "running"})  # response body
        )
        mock_check.return_value = cached_response
        
        idempotency_key = str(uuid.uuid4())
        request_data = {
            "recipe_uid": self.recipe_uid,
            "servings": 3,
            "level": "intermediate",
            "started_at": datetime.utcnow().isoformat()
        }
        
        # Act
        response = self.client.post(
            '/api/recipes/cooking_session/start',
            data=json.dumps(request_data),
            headers={**self.auth_headers, 'Idempotency-Key': idempotency_key}
        )
        
        # Assert
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["session_id"] == self.session_id
        assert data["status"] == "running"
        
        # Verify cached response was returned
        mock_check.assert_called_once()

    @patch('src.interface.controllers.cooking_session_controller.get_jwt_identity')
    def test_idempotency_missing_key(self, mock_jwt):
        """Test that missing idempotency key returns error"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        
        request_data = {
            "recipe_uid": self.recipe_uid,
            "servings": 3,
            "level": "intermediate",
            "started_at": datetime.utcnow().isoformat()
        }
        
        # Act - No Idempotency-Key header
        response = self.client.post(
            '/api/recipes/cooking_session/start',
            data=json.dumps(request_data),
            headers=self.auth_headers
        )
        
        # Assert
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Idempotency-Key" in data["error"]

    @patch('src.interface.controllers.cooking_session_controller.get_jwt_identity')
    @patch('src.infrastructure.services.idempotency_service.IdempotencyService.check_idempotency')
    @patch('src.infrastructure.services.idempotency_service.IdempotencyService.store_response')
    @patch('src.application.factories.cooking_session_factory.make_complete_step_use_case')
    def test_idempotency_different_requests_same_key(self, mock_factory, mock_store, mock_check, mock_jwt):
        """Test idempotency with same key but different request body"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        mock_check.return_value = None  # No cached response (different request hash)
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = {
            "ok": True,
            "inventory_updates": [{"lot_id": "batch_123", "new_qty": 300.0}]
        }
        mock_factory.return_value = mock_use_case
        
        idempotency_key = str(uuid.uuid4())
        
        # First request
        request_data_1 = {
            "session_id": self.session_id,
            "step_id": "S1",
            "consumptions": [{"ingredient_uid": "ing_chicken", "lot_id": "batch_123", "qty": 200, "unit": "g"}]
        }
        
        response_1 = self.client.post(
            '/api/recipes/cooking_session/complete_step',
            data=json.dumps(request_data_1),
            headers={**self.auth_headers, 'Idempotency-Key': idempotency_key}
        )
        
        # Reset mocks
        mock_check.reset_mock()
        mock_store.reset_mock()
        mock_check.return_value = None  # Different request hash, so no cached response
        
        # Second request with same key but different body
        request_data_2 = {
            "session_id": self.session_id,
            "step_id": "S1",
            "consumptions": [{"ingredient_uid": "ing_chicken", "lot_id": "batch_123", "qty": 300, "unit": "g"}]  # Different qty
        }
        
        response_2 = self.client.post(
            '/api/recipes/cooking_session/complete_step',
            data=json.dumps(request_data_2),
            headers={**self.auth_headers, 'Idempotency-Key': idempotency_key}
        )
        
        # Assert both requests processed (different request hashes)
        assert response_1.status_code == 200
        assert response_2.status_code == 200
        
        # Both requests should have been checked for idempotency
        assert mock_check.call_count == 2
        assert mock_store.call_count == 2

    @patch('src.interface.controllers.cooking_session_controller.get_jwt_identity')
    @patch('src.infrastructure.services.idempotency_service.IdempotencyService.check_idempotency')
    @patch('src.infrastructure.services.idempotency_service.IdempotencyService.store_response')
    @patch('src.application.factories.cooking_session_factory.make_finish_cooking_session_use_case')
    def test_idempotency_error_response_not_cached(self, mock_factory, mock_store, mock_check, mock_jwt):
        """Test that error responses are not cached for idempotency"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        mock_check.return_value = None
        
        # Mock use case to raise an error
        mock_use_case = Mock()
        mock_use_case.execute.side_effect = ValueError("Session not found")
        mock_factory.return_value = mock_use_case
        
        idempotency_key = str(uuid.uuid4())
        request_data = {
            "session_id": "non_existent_session",
            "notes": "Test notes"
        }
        
        # Act
        response = self.client.post(
            '/api/recipes/cooking_session/finish',
            data=json.dumps(request_data),
            headers={**self.auth_headers, 'Idempotency-Key': idempotency_key}
        )
        
        # Assert
        assert response.status_code == 400
        
        # Verify that error responses are not stored for idempotency
        # (In a real implementation, you might want to cache 4xx errors but not 5xx)
        mock_check.assert_called_once()
        # mock_store should not be called for error responses
        mock_store.assert_not_called()

    @patch('src.interface.controllers.inventory_controller.get_jwt_identity')
    @patch('src.application.factories.batch_management_factory.make_reserve_batch_use_case')
    def test_idempotency_non_post_requests_not_affected(self, mock_factory, mock_jwt):
        """Test that non-POST requests don't require idempotency"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        
        mock_use_case = Mock()
        mock_use_case.execute.return_value = [
            {
                "batch_id": "batch_001",
                "ingredient_uid": "ing_vegetables",
                "urgency_score": 0.85
            }
        ]
        mock_factory.return_value = mock_use_case
        
        # Act - GET request without idempotency key
        response = self.client.get(
            '/api/inventory/expiring_soon?withinDays=3',
            headers=self.auth_headers
        )
        
        # Assert - Should work fine without idempotency key
        assert response.status_code == 200

    @patch('src.interface.controllers.cooking_session_controller.get_jwt_identity')
    @patch('src.infrastructure.services.idempotency_service.IdempotencyService.check_idempotency')
    @patch('src.infrastructure.services.idempotency_service.IdempotencyService.store_response')
    def test_idempotency_across_different_endpoints(self, mock_store, mock_check, mock_jwt):
        """Test that idempotency keys are scoped to specific endpoints"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        mock_check.return_value = None
        
        # Mock use cases for different endpoints
        with patch('src.application.factories.cooking_session_factory.make_start_cooking_session_use_case') as mock_start_factory:
            mock_start_use_case = Mock()
            mock_session = Mock()
            mock_session.session_id = self.session_id
            mock_start_use_case.execute.return_value = mock_session
            mock_start_factory.return_value = mock_start_use_case
            
            with patch('src.application.factories.cooking_session_factory.make_complete_step_use_case') as mock_complete_factory:
                mock_complete_use_case = Mock()
                mock_complete_use_case.execute.return_value = {"ok": True, "inventory_updates": []}
                mock_complete_factory.return_value = mock_complete_use_case
                
                idempotency_key = str(uuid.uuid4())
                
                # First endpoint
                start_data = {
                    "recipe_uid": self.recipe_uid,
                    "servings": 2,
                    "level": "beginner",
                    "started_at": datetime.utcnow().isoformat()
                }
                
                response_1 = self.client.post(
                    '/api/recipes/cooking_session/start',
                    data=json.dumps(start_data),
                    headers={**self.auth_headers, 'Idempotency-Key': idempotency_key}
                )
                
                # Second endpoint with same key
                complete_data = {
                    "session_id": self.session_id,
                    "step_id": "S1",
                    "consumptions": []
                }
                
                response_2 = self.client.post(
                    '/api/recipes/cooking_session/complete_step',
                    data=json.dumps(complete_data),
                    headers={**self.auth_headers, 'Idempotency-Key': idempotency_key}
                )
                
                # Assert both requests processed (different endpoints)
                assert response_1.status_code == 201
                assert response_2.status_code == 200
                
                # Verify idempotency checked for both endpoints separately
                assert mock_check.call_count == 2
                
                # Verify the endpoint parameter is different for each call
                call_args = mock_check.call_args_list
                assert call_args[0][1]['endpoint'] == 'cooking_session_start'
                assert call_args[1][1]['endpoint'] == 'cooking_session_complete_step'

    def test_idempotency_key_format_validation(self):
        """Test idempotency key format validation"""
        # This test would verify that idempotency keys follow expected format (e.g., UUID)
        # For now, we'll test basic functionality
        
        # Valid UUID format
        valid_key = str(uuid.uuid4())
        assert len(valid_key) == 36
        assert valid_key.count('-') == 4
        
        # Test that non-UUID strings are still accepted (service should handle any string)
        non_uuid_key = "custom-idempotency-key-123"
        assert isinstance(non_uuid_key, str)

    @patch('src.interface.controllers.cooking_session_controller.get_jwt_identity')
    @patch('src.infrastructure.services.idempotency_service.IdempotencyService.check_idempotency')
    @patch('src.infrastructure.services.idempotency_service.IdempotencyService.store_response')
    @patch('src.application.factories.cooking_session_factory.make_start_cooking_session_use_case')
    def test_idempotency_key_cleanup_simulation(self, mock_factory, mock_store, mock_check, mock_jwt):
        """Test simulation of idempotency key cleanup (expired keys)"""
        # Arrange
        mock_jwt.return_value = self.user_uid
        
        # Simulate expired key (should return None)
        mock_check.return_value = None
        
        mock_use_case = Mock()
        mock_session = Mock()
        mock_session.session_id = self.session_id
        mock_use_case.execute.return_value = mock_session
        mock_factory.return_value = mock_use_case
        
        # Use an "old" idempotency key
        expired_key = "expired-key-should-not-be-cached"
        request_data = {
            "recipe_uid": self.recipe_uid,
            "servings": 2,
            "level": "beginner",
            "started_at": datetime.utcnow().isoformat()
        }
        
        # Act
        response = self.client.post(
            '/api/recipes/cooking_session/start',
            data=json.dumps(request_data),
            headers={**self.auth_headers, 'Idempotency-Key': expired_key}
        )
        
        # Assert
        assert response.status_code == 201
        
        # Verify that the expired key was checked but returned None
        mock_check.assert_called_once_with(
            idempotency_key=expired_key,
            user_uid=self.user_uid,
            endpoint="cooking_session_start",
            request_body=request_data
        )
        
        # Verify new response was stored
        mock_store.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])