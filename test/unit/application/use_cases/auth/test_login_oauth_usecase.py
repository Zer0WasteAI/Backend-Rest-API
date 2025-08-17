"""
Unit tests for Login OAuth Use Case
Tests OAuth login functionality
"""
import pytest
from unittest.mock import Mock

from src.application.use_cases.auth.login_oauth_usecase import LoginOAuthUseCase


class TestLoginOAuthUseCase:
    """Test suite for Login OAuth Use Case"""

    @pytest.fixture
    def mock_oauth_service(self):
        """Mock OAuth service"""
        return Mock()

    @pytest.fixture
    def mock_user_repository(self):
        """Mock user repository"""
        return Mock()

    @pytest.fixture
    def mock_auth_service(self):
        """Mock authentication service"""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_oauth_service, mock_user_repository, mock_auth_service):
        """Create use case with mocked dependencies"""
        return LoginOAuthUseCase(
            oauth_service=mock_oauth_service,
            user_repository=mock_user_repository,
            auth_service=mock_auth_service
        )

    @pytest.fixture
    def oauth_user_data(self):
        """Sample OAuth user data"""
        return {
            "id": "google_123456",
            "email": "test@example.com",
            "name": "Test User",
            "picture": "https://example.com/avatar.jpg",
            "verified_email": True
        }

    @pytest.fixture
    def mock_user(self):
        """Mock user object"""
        user = Mock()
        user.uid = "user_123"
        user.email = "test@example.com"
        user.is_active = True
        return user

    def test_oauth_login_existing_user_success(self, use_case, mock_oauth_service, 
                                             mock_user_repository, mock_auth_service, 
                                             oauth_user_data, mock_user):
        """Test successful OAuth login with existing user"""
        # Arrange
        mock_oauth_service.verify_token.return_value = oauth_user_data
        mock_user_repository.find_by_email.return_value = mock_user
        mock_auth_service.create_tokens.return_value = {
            "access_token": "jwt_access_token_123",
            "refresh_token": "jwt_refresh_token_456",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        
        # Act
        result = use_case.execute(
            provider="google",
            oauth_token="oauth_token_123"
        )
        
        # Assert
        assert result["user_id"] == "user_123"
        assert result["access_token"] == "jwt_access_token_123"
        assert result["refresh_token"] == "jwt_refresh_token_456"
        assert result["expires_in"] == 3600
        assert result["token_type"] == "Bearer"
        
        mock_oauth_service.verify_token.assert_called_once_with("google", "oauth_token_123")
        mock_user_repository.find_by_email.assert_called_once_with("test@example.com")
        mock_auth_service.create_tokens.assert_called_once_with("user_123")

    def test_oauth_login_new_user_registration(self, use_case, mock_oauth_service, 
                                             mock_user_repository, mock_auth_service, 
                                             oauth_user_data):
        """Test OAuth login with new user registration"""
        # Arrange
        mock_oauth_service.verify_token.return_value = oauth_user_data
        mock_user_repository.find_by_email.return_value = None  # New user
        
        new_user = Mock()
        new_user.uid = "new_user_123"
        mock_user_repository.create_oauth_user.return_value = new_user
        
        mock_auth_service.create_tokens.return_value = {
            "access_token": "jwt_access_token_456",
            "refresh_token": "jwt_refresh_token_789",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        
        # Act
        result = use_case.execute(
            provider="google",
            oauth_token="oauth_token_123"
        )
        
        # Assert
        assert result["user_id"] == "new_user_123"
        assert result["access_token"] == "jwt_access_token_456"
        
        mock_user_repository.create_oauth_user.assert_called_once_with(
            email="test@example.com",
            name="Test User",
            provider="google",
            provider_id="google_123456",
            avatar_url="https://example.com/avatar.jpg"
        )

    def test_oauth_login_invalid_token(self, use_case, mock_oauth_service):
        """Test OAuth login with invalid token"""
        # Arrange
        mock_oauth_service.verify_token.side_effect = Exception("Invalid OAuth token")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                provider="google",
                oauth_token="invalid_token"
            )
        
        assert str(exc_info.value) == "Invalid OAuth token"

    def test_oauth_login_unsupported_provider(self, use_case, mock_oauth_service):
        """Test OAuth login with unsupported provider"""
        # Arrange
        mock_oauth_service.verify_token.side_effect = Exception("Unsupported OAuth provider")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                provider="unsupported_provider",
                oauth_token="oauth_token_123"
            )
        
        assert str(exc_info.value) == "Unsupported OAuth provider"

    def test_oauth_login_inactive_user(self, use_case, mock_oauth_service, mock_user_repository, 
                                     oauth_user_data, mock_user):
        """Test OAuth login with inactive user"""
        # Arrange
        mock_oauth_service.verify_token.return_value = oauth_user_data
        mock_user.is_active = False
        mock_user_repository.find_by_email.return_value = mock_user
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                provider="google",
                oauth_token="oauth_token_123"
            )
        
        assert "User account is inactive" in str(exc_info.value)

    def test_oauth_login_unverified_email(self, use_case, mock_oauth_service, oauth_user_data):
        """Test OAuth login with unverified email"""
        # Arrange
        oauth_user_data["verified_email"] = False
        mock_oauth_service.verify_token.return_value = oauth_user_data
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                provider="google",
                oauth_token="oauth_token_123"
            )
        
        assert "Email not verified" in str(exc_info.value)

    def test_oauth_login_empty_provider(self, use_case):
        """Test OAuth login with empty provider"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                provider="",
                oauth_token="oauth_token_123"
            )
        
        assert "Provider cannot be empty" in str(exc_info.value)

    def test_oauth_login_empty_token(self, use_case):
        """Test OAuth login with empty token"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                provider="google",
                oauth_token=""
            )
        
        assert "OAuth token cannot be empty" in str(exc_info.value)

    def test_oauth_login_missing_email_in_response(self, use_case, mock_oauth_service, oauth_user_data):
        """Test OAuth login when email is missing from OAuth response"""
        # Arrange
        del oauth_user_data["email"]
        mock_oauth_service.verify_token.return_value = oauth_user_data
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                provider="google",
                oauth_token="oauth_token_123"
            )
        
        assert "Email not provided by OAuth provider" in str(exc_info.value)

    def test_oauth_login_user_creation_failure(self, use_case, mock_oauth_service, 
                                             mock_user_repository, oauth_user_data):
        """Test OAuth login when user creation fails"""
        # Arrange
        mock_oauth_service.verify_token.return_value = oauth_user_data
        mock_user_repository.find_by_email.return_value = None
        mock_user_repository.create_oauth_user.side_effect = Exception("User creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                provider="google",
                oauth_token="oauth_token_123"
            )
        
        assert str(exc_info.value) == "User creation failed"

    def test_oauth_login_token_creation_failure(self, use_case, mock_oauth_service, 
                                              mock_user_repository, mock_auth_service, 
                                              oauth_user_data, mock_user):
        """Test OAuth login when token creation fails"""
        # Arrange
        mock_oauth_service.verify_token.return_value = oauth_user_data
        mock_user_repository.find_by_email.return_value = mock_user
        mock_auth_service.create_tokens.side_effect = Exception("Token creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                provider="google",
                oauth_token="oauth_token_123"
            )
        
        assert str(exc_info.value) == "Token creation failed"

    def test_oauth_login_different_providers(self, use_case, mock_oauth_service, 
                                           mock_user_repository, mock_auth_service, 
                                           oauth_user_data, mock_user):
        """Test OAuth login with different providers"""
        # Arrange
        mock_oauth_service.verify_token.return_value = oauth_user_data
        mock_user_repository.find_by_email.return_value = mock_user
        mock_auth_service.create_tokens.return_value = {
            "access_token": "token",
            "refresh_token": "refresh",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        
        providers = ["google", "facebook", "github"]
        
        for provider in providers:
            # Act
            result = use_case.execute(
                provider=provider,
                oauth_token="oauth_token_123"
            )
            
            # Assert
            assert result["user_id"] == "user_123"
            mock_oauth_service.verify_token.assert_called_with(provider, "oauth_token_123")