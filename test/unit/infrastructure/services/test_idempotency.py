import pytest
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.infrastructure.services.idempotency_service import IdempotencyService
from src.infrastructure.db.models.idempotency_key_orm import IdempotencyKeyORM


class TestIdempotencyService:
    """Test suite for idempotency service"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock()
        self.mock_session = Mock()
        self.mock_db.session = self.mock_session
        
        self.service = IdempotencyService(self.mock_db)
        self.user_uid = "test_user_123"
        self.idempotency_key = str(uuid.uuid4())
        self.endpoint = "cooking_session_start"

    def test_check_idempotency_key_not_found(self):
        """Test idempotency check when key doesn't exist"""
        # Arrange
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        
        request_body = {"recipe_uid": "test_recipe", "servings": 2}
        
        # Act
        result = self.service.check_idempotency(
            idempotency_key=self.idempotency_key,
            user_uid=self.user_uid,
            endpoint=self.endpoint,
            request_body=request_body
        )
        
        # Assert
        assert result is None
        self.mock_session.query.assert_called_once()

    def test_check_idempotency_key_found_valid(self):
        """Test idempotency check when valid key is found"""
        # Arrange
        request_body = {"recipe_uid": "test_recipe", "servings": 2}
        request_hash = self.service._hash_request(request_body)
        
        existing_record = IdempotencyKeyORM(
            idempotency_key=self.idempotency_key,
            user_uid=self.user_uid,
            endpoint=self.endpoint,
            request_hash=request_hash,
            response_status="201",
            response_body='{"session_id": "test_session"}',
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = existing_record
        
        # Act
        result = self.service.check_idempotency(
            idempotency_key=self.idempotency_key,
            user_uid=self.user_uid,
            endpoint=self.endpoint,
            request_body=request_body
        )
        
        # Assert
        assert result is not None
        status_code, response_body = result
        assert status_code == "201"
        assert response_body == '{"session_id": "test_session"}'

    def test_check_idempotency_key_expired(self):
        """Test idempotency check when key has expired"""
        # Arrange
        request_body = {"recipe_uid": "test_recipe", "servings": 2}
        
        expired_record = IdempotencyKeyORM(
            idempotency_key=self.idempotency_key,
            user_uid=self.user_uid,
            endpoint=self.endpoint,
            request_hash=self.service._hash_request(request_body),
            response_status="201",
            response_body='{"session_id": "test_session"}',
            expires_at=datetime.utcnow() - timedelta(hours=1)  # Expired
        )
        
        # The filter should exclude expired records, so return None
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = self.service.check_idempotency(
            idempotency_key=self.idempotency_key,
            user_uid=self.user_uid,
            endpoint=self.endpoint,
            request_body=request_body
        )
        
        # Assert
        assert result is None

    def test_store_response_success(self):
        """Test successful response storage"""
        # Arrange
        request_body = {"recipe_uid": "test_recipe", "servings": 2}
        response_body = '{"session_id": "new_session", "status": "running"}'
        
        # Act
        self.service.store_response(
            idempotency_key=self.idempotency_key,
            user_uid=self.user_uid,
            endpoint=self.endpoint,
            request_body=request_body,
            status_code="201",
            response_body=response_body
        )
        
        # Assert
        self.mock_session.query.assert_called()  # Called for deletion
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()

    def test_store_response_deletes_existing(self):
        """Test that storing response deletes any existing key first"""
        # Arrange
        request_body = {"recipe_uid": "test_recipe", "servings": 2}
        response_body = '{"session_id": "new_session"}'
        
        # Mock the delete query
        delete_query = Mock()
        self.mock_session.query.return_value.filter.return_value = delete_query
        
        # Act
        self.service.store_response(
            idempotency_key=self.idempotency_key,
            user_uid=self.user_uid,
            endpoint=self.endpoint,
            request_body=request_body,
            status_code="201",
            response_body=response_body
        )
        
        # Assert
        delete_query.delete.assert_called_once()

    def test_cleanup_expired_keys(self):
        """Test cleanup of expired idempotency keys"""
        # Arrange
        delete_query = Mock()
        delete_query.delete.return_value = 5  # 5 keys deleted
        self.mock_session.query.return_value.filter.return_value = delete_query
        
        # Act
        deleted_count = self.service.cleanup_expired_keys()
        
        # Assert
        assert deleted_count == 5
        delete_query.delete.assert_called_once()
        self.mock_session.commit.assert_called_once()

    def test_hash_request_consistent(self):
        """Test that request hashing is consistent"""
        # Arrange
        request_body = {
            "recipe_uid": "test_recipe",
            "servings": 2,
            "level": "intermediate"
        }
        
        # Act
        hash1 = self.service._hash_request(request_body)
        hash2 = self.service._hash_request(request_body)
        
        # Assert
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 produces 64-character hex strings

    def test_hash_request_different_for_different_bodies(self):
        """Test that different request bodies produce different hashes"""
        # Arrange
        request_body1 = {"recipe_uid": "test_recipe", "servings": 2}
        request_body2 = {"recipe_uid": "test_recipe", "servings": 3}
        
        # Act
        hash1 = self.service._hash_request(request_body1)
        hash2 = self.service._hash_request(request_body2)
        
        # Assert
        assert hash1 != hash2

    def test_hash_request_order_independent(self):
        """Test that key order doesn't affect hash"""
        # Arrange
        request_body1 = {"servings": 2, "recipe_uid": "test_recipe"}
        request_body2 = {"recipe_uid": "test_recipe", "servings": 2}
        
        # Act
        hash1 = self.service._hash_request(request_body1)
        hash2 = self.service._hash_request(request_body2)
        
        # Assert
        assert hash1 == hash2

    def test_check_idempotency_different_request_hash(self):
        """Test idempotency check with same key but different request body"""
        # Arrange
        original_body = {"recipe_uid": "test_recipe", "servings": 2}
        different_body = {"recipe_uid": "test_recipe", "servings": 3}
        
        existing_record = IdempotencyKeyORM(
            idempotency_key=self.idempotency_key,
            user_uid=self.user_uid,
            endpoint=self.endpoint,
            request_hash=self.service._hash_request(original_body),
            response_status="201",
            response_body='{"session_id": "test_session"}',
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        # Mock should return None because hash doesn't match
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = self.service.check_idempotency(
            idempotency_key=self.idempotency_key,
            user_uid=self.user_uid,
            endpoint=self.endpoint,
            request_body=different_body  # Different body
        )
        
        # Assert
        assert result is None

    def test_custom_ttl(self):
        """Test custom TTL for idempotency keys"""
        # Arrange
        request_body = {"recipe_uid": "test_recipe", "servings": 2}
        custom_ttl = 12  # 12 hours
        
        # Act
        self.service.store_response(
            idempotency_key=self.idempotency_key,
            user_uid=self.user_uid,
            endpoint=self.endpoint,
            request_body=request_body,
            status_code="201",
            response_body='{"result": "success"}',
            ttl_hours=custom_ttl
        )
        
        # Assert
        # Check that add was called with a record having the correct expires_at
        add_call = self.mock_session.add.call_args[0][0]
        expected_expiry = datetime.utcnow() + timedelta(hours=custom_ttl)
        actual_expiry = add_call.expires_at
        
        # Allow for small time differences (within 1 minute)
        time_diff = abs((expected_expiry - actual_expiry).total_seconds())
        assert time_diff < 60


class TestIdempotencyIntegration:
    """Integration tests for idempotency functionality"""

    def test_idempotency_with_cooking_session_workflow(self):
        """Test idempotency in the context of cooking session creation"""
        # This would test the full integration of idempotency
        # with actual cooking session endpoints
        # For now, this is a placeholder for future implementation
        pass

    def test_concurrent_requests_with_same_key(self):
        """Test handling of concurrent requests with same idempotency key"""
        # This would test race conditions and concurrent access
        # For now, this is a placeholder for future implementation
        pass


if __name__ == "__main__":
    pytest.main([__file__])