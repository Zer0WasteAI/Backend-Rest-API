"""
Unit tests for Refresh Token Use Case
Tests token refresh functionality
"""
import pytest
from unittest.mock import Mock

from src.application.use_cases.auth.refresh_token_usecase import RefreshTokenUseCase


class TestRefreshTokenUseCase:
    """Test suite for Refresh Token Use Case"""

    @pytest.fixture
    def mock_auth_service(self):
        """Mock authentication service"""
        return Mock()

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository"""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_auth_service, mock_user_repository):
        """Create use case with mocked dependencies"""
        return RefreshTokenUseCase(
            auth_service=mock_auth_service,
            user_repository=mock_user_repository
        )

    @pytest.fixture
    def mock_user(self):
        """Mock user object"""
        user = Mock()
        user.uid = "user_123"
        user.email = "test@example.com"
        user.is_active = True
        return user

    def test_refresh_token_success(self, use_case, mock_auth_service, mock_user_repository, mock_user):
        """Test successful token refresh"""
        # Arrange
        mock_auth_service.decode_refresh_token.return_value = {
            "sub": "user_123",
            "type": "refresh"
        }
        mock_user_repository.find_by_uid.return_value = mock_user
        mock_auth_service.create_tokens.return_value = {
            "access_token": "new_access_token_123",
            "refresh_token": "new_refresh_token_456",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        
        # Act
        result = use_case.execute(refresh_token="valid_refresh_token")
        
        # Assert
        assert result["access_token"] == "new_access_token_123"
        assert result["refresh_token"] == "new_refresh_token_456"
        assert result["expires_in"] == 3600
        assert result["token_type"] == "Bearer"
        
        mock_auth_service.decode_refresh_token.assert_called_once_with("valid_refresh_token")
        mock_user_repository.find_by_uid.assert_called_once_with("user_123")
        mock_auth_service.create_tokens.assert_called_once_with("user_123")

    def test_refresh_token_invalid_token(self, use_case, mock_auth_service):
        """Test refresh with invalid token"""
        # Arrange
        mock_auth_service.decode_refresh_token.side_effect = Exception("Invalid refresh token")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(refresh_token="invalid_token")
        
        assert str(exc_info.value) == "Invalid refresh token"

    def test_refresh_token_expired_token(self, use_case, mock_auth_service):
        """Test refresh with expired token"""
        # Arrange
        mock_auth_service.decode_refresh_token.side_effect = Exception("Token has expired")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(refresh_token="expired_token")
        
        assert str(exc_info.value) == "Token has expired"

    def test_refresh_token_user_not_found(self, use_case, mock_auth_service, mock_user_repository):
        """Test refresh when user not found"""
        # Arrange
        mock_auth_service.decode_refresh_token.return_value = {
            "sub": "nonexistent_user",
            "type": "refresh"
        }
        mock_user_repository.find_by_uid.return_value = None
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(refresh_token="valid_refresh_token")
        
        assert "User not found" in str(exc_info.value)

    def test_refresh_token_inactive_user(self, use_case, mock_auth_service, mock_user_repository, mock_user):
        """Test refresh for inactive user"""
        # Arrange
        mock_auth_service.decode_refresh_token.return_value = {
            "sub": "user_123",
            "type": "refresh"
        }
        mock_user.is_active = False
        mock_user_repository.find_by_uid.return_value = mock_user
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(refresh_token="valid_refresh_token")
        
        assert "User account is inactive" in str(exc_info.value)

    def test_refresh_token_wrong_token_type(self, use_case, mock_auth_service):
        """Test refresh with wrong token type"""
        # Arrange
        mock_auth_service.decode_refresh_token.return_value = {
            "sub": "user_123",
            "type": "access"  # Wrong type
        }
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(refresh_token="wrong_type_token")
        
        assert "Invalid token type" in str(exc_info.value)

    def test_refresh_token_empty_token(self, use_case):
        """Test refresh with empty token"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(refresh_token="")
        
        assert "Refresh token cannot be empty" in str(exc_info.value)

    def test_refresh_token_none_token(self, use_case):
        """Test refresh with None token"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(refresh_token=None)
        
        assert "Refresh token cannot be None" in str(exc_info.value)

    def test_refresh_token_malformed_payload(self, use_case, mock_auth_service):
        """Test refresh with malformed token payload"""
        # Arrange
        mock_auth_service.decode_refresh_token.return_value = {
            # Missing 'sub' field
            "type": "refresh"
        }
        
        # Act & Assert
        with pytest.raises(KeyError) as exc_info:
            use_case.execute(refresh_token="malformed_token")
        
        assert "sub" in str(exc_info.value)

    def test_refresh_token_auth_service_error_propagation(self, use_case, mock_auth_service, 
                                                        mock_user_repository, mock_user):
        """Test that auth service errors during token creation are propagated"""
        # Arrange
        mock_auth_service.decode_refresh_token.return_value = {
            "sub": "user_123",
            "type": "refresh"
        }
        mock_user_repository.find_by_uid.return_value = mock_user
        mock_auth_service.create_tokens.side_effect = Exception("Token creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(refresh_token="valid_refresh_token")
        
        assert str(exc_info.value) == "Token creation failed"

    def test_refresh_token_repository_error_propagation(self, use_case, mock_auth_service, mock_user_repository):
        """Test that repository errors are propagated"""
        # Arrange
        mock_auth_service.decode_refresh_token.return_value = {
            "sub": "user_123",
            "type": "refresh"
        }
        mock_user_repository.find_by_uid.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(refresh_token="valid_refresh_token")
        
        assert str(exc_info.value) == "Database connection error"

    def test_refresh_token_multiple_calls_same_token(self, use_case, mock_auth_service, 
                                                   mock_user_repository, mock_user):
        """Test multiple refresh calls with same token"""
        # Arrange
        mock_auth_service.decode_refresh_token.return_value = {
            "sub": "user_123",
            "type": "refresh"
        }
        mock_user_repository.find_by_uid.return_value = mock_user
        mock_auth_service.create_tokens.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        
        # Act
        result1 = use_case.execute(refresh_token="same_refresh_token")
        result2 = use_case.execute(refresh_token="same_refresh_token")
        
        # Assert
        assert result1["access_token"] == "new_access_token"
        assert result2["access_token"] == "new_access_token"
        assert mock_auth_service.decode_refresh_token.call_count == 2
        assert mock_auth_service.create_tokens.call_count == 2