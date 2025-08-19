"""
Unit tests for Idempotency Service
Tests idempotency key management and response caching
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from src.infrastructure.services.idempotency_service import IdempotencyService


class TestIdempotencyService:
    """Test suite for Idempotency Service"""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def idempotency_service(self, mock_session):
        """Create idempotency service with mocked session"""
        return IdempotencyService()
    
    def test_check_idempotency_new_key(self, idempotency_service, mock_session):
        """Test check_idempotency with a new key"""
        # Arrange
        with patch('src.infrastructure.services.idempotency_service.get_db_session') as mock_get_session:
            mock_get_session.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None
            
            # Act
            result = idempotency_service.check_idempotency(
                "test-key", 
                "test-user", 
                "/test/endpoint"
            )
            
            # Assert
            assert result is None  # No cached response for new key
            mock_session.query.assert_called_once()

    def test_check_idempotency_existing_key(self, idempotency_service, mock_session):
        """Test check_idempotency with existing key"""
        # Arrange
        mock_cached_response = Mock()
        mock_cached_response.response_data = '{"cached": true}'
        mock_cached_response.status_code = 200
        mock_cached_response.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        with patch('src.infrastructure.services.idempotency_service.get_db_session') as mock_get_session:
            mock_get_session.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = mock_cached_response
            
            # Act
            result = idempotency_service.check_idempotency(
                "existing-key", 
                "test-user", 
                "/test/endpoint"
            )
            
            # Assert
            assert result is not None
            assert result["response_data"] == '{"cached": true}'
            assert result["status_code"] == 200

    def test_check_idempotency_expired_key(self, idempotency_service, mock_session):
        """Test check_idempotency with expired key"""
        # Arrange
        mock_expired_response = Mock()
        mock_expired_response.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
        
        with patch('src.infrastructure.services.idempotency_service.get_db_session') as mock_get_session:
            mock_get_session.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = mock_expired_response
            
            # Act
            result = idempotency_service.check_idempotency(
                "expired-key", 
                "test-user", 
                "/test/endpoint"
            )
            
            # Assert
            assert result is None  # Expired key should return None
            mock_session.delete.assert_called_once_with(mock_expired_response)

    def test_store_response_success(self, idempotency_service, mock_session):
        """Test successful response storage"""
        # Arrange
        with patch('src.infrastructure.services.idempotency_service.get_db_session') as mock_get_session:
            with patch('src.infrastructure.services.idempotency_service.IdempotencyKeyORM') as mock_orm:
                mock_get_session.return_value = mock_session
                mock_instance = Mock()
                mock_orm.return_value = mock_instance
                
                # Act
                idempotency_service.store_response(
                    "test-key",
                    "test-user",
                    "/test/endpoint",
                    '{"result": "success"}',
                    200
                )
                
                # Assert
                mock_orm.assert_called_once()
                mock_session.add.assert_called_once_with(mock_instance)
                mock_session.commit.assert_called_once()

    def test_store_response_error_handling(self, idempotency_service, mock_session):
        """Test error handling in store_response"""
        # Arrange
        with patch('src.infrastructure.services.idempotency_service.get_db_session') as mock_get_session:
            mock_get_session.return_value = mock_session
            mock_session.add.side_effect = Exception("Database error")
            
            # Act & Assert
            with pytest.raises(Exception):
                idempotency_service.store_response(
                    "test-key",
                    "test-user", 
                    "/test/endpoint",
                    '{"result": "success"}',
                    200
                )
            
            mock_session.rollback.assert_called_once()

    def test_cleanup_expired_keys_success(self, idempotency_service, mock_session):
        """Test successful cleanup of expired keys"""
        # Arrange
        with patch('src.infrastructure.services.idempotency_service.get_db_session') as mock_get_session:
            with patch('src.infrastructure.services.idempotency_service.IdempotencyKeyORM') as mock_orm:
                mock_get_session.return_value = mock_session
                mock_query = Mock()
                mock_query.delete.return_value = 5  # 5 expired keys deleted
                mock_orm.query.return_value.filter.return_value = mock_query
                
                # Act
                result = idempotency_service.cleanup_expired_keys()
                
                # Assert
                assert result == 5
                mock_session.commit.assert_called_once()

    def test_cleanup_expired_keys_error_handling(self, idempotency_service, mock_session):
        """Test error handling in cleanup_expired_keys"""
        # Arrange
        with patch('src.infrastructure.services.idempotency_service.get_db_session') as mock_get_session:
            mock_get_session.return_value = mock_session
            mock_session.commit.side_effect = Exception("Database error")
            
            # Act & Assert
            result = idempotency_service.cleanup_expired_keys()
            
            assert result == 0  # Should return 0 on error
            mock_session.rollback.assert_called_once()

    def test_check_idempotency_invalid_parameters(self, idempotency_service):
        """Test check_idempotency with invalid parameters"""
        # Act & Assert
        with pytest.raises((ValueError, TypeError)):
            idempotency_service.check_idempotency(None, "user", "endpoint")
        
        with pytest.raises((ValueError, TypeError)):
            idempotency_service.check_idempotency("key", None, "endpoint")
        
        with pytest.raises((ValueError, TypeError)):
            idempotency_service.check_idempotency("key", "user", None)

    def test_store_response_invalid_parameters(self, idempotency_service):
        """Test store_response with invalid parameters"""
        # Act & Assert
        with pytest.raises((ValueError, TypeError)):
            idempotency_service.store_response(None, "user", "endpoint", "data", 200)
        
        with pytest.raises((ValueError, TypeError)):
            idempotency_service.store_response("key", None, "endpoint", "data", 200)
            
        with pytest.raises((ValueError, TypeError)):
            idempotency_service.store_response("key", "user", None, "data", 200)

    @patch('src.infrastructure.services.idempotency_service.get_db_session')
    def test_database_connection_handling(self, mock_get_session, idempotency_service):
        """Test proper database connection handling"""
        # Arrange
        mock_session = Mock()
        mock_get_session.return_value = mock_session
        
        # Act
        idempotency_service.check_idempotency("key", "user", "endpoint")
        
        # Assert
        mock_get_session.assert_called_once()
        assert mock_session.close.called  # Session should be closed

    def test_service_initialization(self):
        """Test service can be initialized properly"""
        # Act
        service = IdempotencyService()
        
        # Assert
        assert service is not None
        assert hasattr(service, 'check_idempotency')
        assert hasattr(service, 'store_response')
        assert hasattr(service, 'cleanup_expired_keys')

    def test_concurrent_access_handling(self, idempotency_service, mock_session):
        """Test handling of concurrent access to same key"""
        # This is a basic test for race conditions
        with patch('src.infrastructure.services.idempotency_service.get_db_session') as mock_get_session:
            mock_get_session.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None
            
            # Act - simulate multiple concurrent calls
            result1 = idempotency_service.check_idempotency("key", "user1", "endpoint")
            result2 = idempotency_service.check_idempotency("key", "user2", "endpoint")
            
            # Assert
            assert result1 is None
            assert result2 is None
            assert mock_session.query.call_count == 2
