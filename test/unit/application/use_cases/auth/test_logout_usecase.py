"""
Unit tests for Logout Use Case
Tests user logout functionality
"""
import pytest
from unittest.mock import Mock

from src.application.use_cases.auth.logout_usecase import LogoutUseCase


class TestLogoutUseCase:
    """Test suite for Logout Use Case"""

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
        return LogoutUseCase(
            auth_service=mock_auth_service,
            user_repository=mock_user_repository
        )

    def test_logout_success(self, use_case, mock_auth_service, mock_user_repository):
        """Test successful logout"""
        # Arrange
        mock_auth_service.invalidate_token.return_value = True
        mock_user_repository.update_last_logout.return_value = True
        
        # Act
        result = use_case.execute(
            user_uid="user_123",
            token="jwt_token_123"
        )
        
        # Assert
        assert result["ok"] is True
        assert result["message"] == "Logout successful"
        
        mock_auth_service.invalidate_token.assert_called_once_with("jwt_token_123")
        mock_user_repository.update_last_logout.assert_called_once_with("user_123")

    def test_logout_invalid_token(self, use_case, mock_auth_service, mock_user_repository):
        """Test logout with invalid token"""
        # Arrange
        mock_auth_service.invalidate_token.side_effect = Exception("Invalid token")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                user_uid="user_123",
                token="invalid_token"
            )
        
        assert str(exc_info.value) == "Invalid token"
        mock_user_repository.update_last_logout.assert_not_called()

    def test_logout_user_not_found(self, use_case, mock_auth_service, mock_user_repository):
        """Test logout when user not found"""
        # Arrange
        mock_auth_service.invalidate_token.return_value = True
        mock_user_repository.update_last_logout.side_effect = Exception("User not found")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                user_uid="nonexistent_user",
                token="jwt_token_123"
            )
        
        assert str(exc_info.value) == "User not found"

    def test_logout_empty_user_uid(self, use_case, mock_auth_service):
        """Test logout with empty user UID"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                user_uid="",
                token="jwt_token_123"
            )
        
        assert "User UID cannot be empty" in str(exc_info.value)

    def test_logout_empty_token(self, use_case):
        """Test logout with empty token"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                user_uid="user_123",
                token=""
            )
        
        assert "Token cannot be empty" in str(exc_info.value)

    def test_logout_none_parameters(self, use_case):
        """Test logout with None parameters"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                user_uid=None,
                token=None
            )
        
        assert "User UID cannot be None" in str(exc_info.value)

    def test_logout_auth_service_error_propagation(self, use_case, mock_auth_service):
        """Test that auth service errors are propagated"""
        # Arrange
        mock_auth_service.invalidate_token.side_effect = Exception("Auth service unavailable")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                user_uid="user_123",
                token="jwt_token_123"
            )
        
        assert str(exc_info.value) == "Auth service unavailable"

    def test_logout_repository_error_propagation(self, use_case, mock_auth_service, mock_user_repository):
        """Test that repository errors are propagated"""
        # Arrange
        mock_auth_service.invalidate_token.return_value = True
        mock_user_repository.update_last_logout.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                user_uid="user_123",
                token="jwt_token_123"
            )
        
        assert str(exc_info.value) == "Database connection error"

    def test_logout_with_different_user_types(self, use_case, mock_auth_service, mock_user_repository):
        """Test logout with different user types"""
        # Arrange
        mock_auth_service.invalidate_token.return_value = True
        mock_user_repository.update_last_logout.return_value = True
        
        user_types = ["regular_user", "admin_user", "premium_user"]
        
        for user_type in user_types:
            # Act
            result = use_case.execute(
                user_uid=f"{user_type}_123",
                token="jwt_token_123"
            )
            
            # Assert
            assert result["ok"] is True
            assert result["message"] == "Logout successful"

    def test_logout_concurrent_calls(self, use_case, mock_auth_service, mock_user_repository):
        """Test multiple logout calls for same user"""
        # Arrange
        mock_auth_service.invalidate_token.return_value = True
        mock_user_repository.update_last_logout.return_value = True
        
        # Act
        result1 = use_case.execute("user_123", "token_1")
        result2 = use_case.execute("user_123", "token_2")
        
        # Assert
        assert result1["ok"] is True
        assert result2["ok"] is True
        assert mock_auth_service.invalidate_token.call_count == 2
        assert mock_user_repository.update_last_logout.call_count == 2