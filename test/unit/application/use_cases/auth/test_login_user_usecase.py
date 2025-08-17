"""
Unit tests for Login User Use Case
Tests login functionality with different authentication providers
"""
import pytest
from unittest.mock import Mock, patch

from src.application.use_cases.auth.login_user_usecase import LoginUserUseCase


class TestLoginUserUseCase:
    """Test suite for Login User Use Case"""
    
    @pytest.fixture
    def mock_email_use_case(self):
        """Mock email login use case"""
        return Mock()
    
    @pytest.fixture
    def mock_google_use_case(self):
        """Mock Google OAuth use case"""
        return Mock()
    
    @pytest.fixture
    def mock_facebook_use_case(self):
        """Mock Facebook OAuth use case"""
        return Mock()
    
    @pytest.fixture
    def mock_apple_use_case(self):
        """Mock Apple OAuth use case"""
        return Mock()
    
    @pytest.fixture
    def login_use_case(self, mock_email_use_case, mock_google_use_case, 
                      mock_facebook_use_case, mock_apple_use_case):
        """Create login use case with mocked dependencies"""
        return LoginUserUseCase(
            email_use_case=mock_email_use_case,
            google_use_case=mock_google_use_case,
            facebook_use_case=mock_facebook_use_case,
            apple_use_case=mock_apple_use_case
        )

    def test_email_login_success(self, login_use_case, mock_email_use_case):
        """Test successful email login"""
        # Arrange
        mock_email_use_case.execute.return_value = {
            "user_id": "user_123",
            "access_token": "jwt_token_123",
            "refresh_token": "refresh_123"
        }
        
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        # Act
        result = login_use_case.execute("email", login_data)
        
        # Assert
        assert result["user_id"] == "user_123"
        assert "access_token" in result
        mock_email_use_case.execute.assert_called_once_with(
            "test@example.com", 
            "password123"
        )

    def test_google_login_success(self, login_use_case, mock_google_use_case):
        """Test successful Google OAuth login"""
        # Arrange
        mock_google_use_case.execute.return_value = {
            "user_id": "google_user_456",
            "access_token": "google_jwt_456",
            "provider": "google"
        }
        
        login_data = {"code": "google_auth_code_123"}
        
        # Act
        result = login_use_case.execute("google", login_data)
        
        # Assert
        assert result["user_id"] == "google_user_456"
        assert result["provider"] == "google"
        mock_google_use_case.execute.assert_called_once_with("google_auth_code_123")

    def test_facebook_login_success(self, login_use_case, mock_facebook_use_case):
        """Test successful Facebook OAuth login"""
        # Arrange
        mock_facebook_use_case.execute.return_value = {
            "user_id": "fb_user_789",
            "access_token": "fb_jwt_789",
            "provider": "facebook"
        }
        
        login_data = {"code": "facebook_auth_code_456"}
        
        # Act
        result = login_use_case.execute("facebook", login_data)
        
        # Assert
        assert result["user_id"] == "fb_user_789"
        assert result["provider"] == "facebook"
        mock_facebook_use_case.execute.assert_called_once_with("facebook_auth_code_456")

    def test_apple_login_success(self, login_use_case, mock_apple_use_case):
        """Test successful Apple OAuth login"""
        # Arrange
        mock_apple_use_case.execute.return_value = {
            "user_id": "apple_user_101",
            "access_token": "apple_jwt_101",
            "provider": "apple"
        }
        
        login_data = {"code": "apple_auth_code_789"}
        
        # Act
        result = login_use_case.execute("apple", login_data)
        
        # Assert
        assert result["user_id"] == "apple_user_101"
        assert result["provider"] == "apple"
        mock_apple_use_case.execute.assert_called_once_with("apple_auth_code_789")

    def test_unsupported_login_type_raises_exception(self, login_use_case):
        """Test unsupported login type raises exception"""
        # Arrange
        login_data = {"some": "data"}
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            login_use_case.execute("unsupported_type", login_data)
        
        assert str(exc_info.value) == "Login type not supported"

    def test_email_login_missing_email_raises_key_error(self, login_use_case):
        """Test email login with missing email raises KeyError"""
        # Arrange
        login_data = {"password": "password123"}  # Missing email
        
        # Act & Assert
        with pytest.raises(KeyError):
            login_use_case.execute("email", login_data)

    def test_email_login_missing_password_raises_key_error(self, login_use_case):
        """Test email login with missing password raises KeyError"""
        # Arrange
        login_data = {"email": "test@example.com"}  # Missing password
        
        # Act & Assert
        with pytest.raises(KeyError):
            login_use_case.execute("email", login_data)

    def test_oauth_login_missing_code_raises_key_error(self, login_use_case):
        """Test OAuth login with missing code raises KeyError"""
        # Arrange
        login_data = {}  # Missing code
        
        # Act & Assert
        with pytest.raises(KeyError):
            login_use_case.execute("google", login_data)

    def test_email_use_case_exception_propagates(self, login_use_case, mock_email_use_case):
        """Test email use case exception propagates"""
        # Arrange
        mock_email_use_case.execute.side_effect = Exception("Invalid credentials")
        login_data = {"email": "test@example.com", "password": "wrong_password"}
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            login_use_case.execute("email", login_data)
        
        assert str(exc_info.value) == "Invalid credentials"

    def test_google_use_case_exception_propagates(self, login_use_case, mock_google_use_case):
        """Test Google use case exception propagates"""
        # Arrange
        mock_google_use_case.execute.side_effect = Exception("Invalid Google auth code")
        login_data = {"code": "invalid_code"}
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            login_use_case.execute("google", login_data)
        
        assert str(exc_info.value) == "Invalid Google auth code"

    def test_all_login_types_call_correct_use_cases(self, login_use_case, 
                                                   mock_email_use_case, mock_google_use_case,
                                                   mock_facebook_use_case, mock_apple_use_case):
        """Test that each login type calls the correct underlying use case"""
        # Test email
        login_use_case.execute("email", {"email": "test@example.com", "password": "pass"})
        mock_email_use_case.execute.assert_called_once()
        
        # Test Google
        login_use_case.execute("google", {"code": "google_code"})
        mock_google_use_case.execute.assert_called_once()
        
        # Test Facebook
        login_use_case.execute("facebook", {"code": "fb_code"})
        mock_facebook_use_case.execute.assert_called_once()
        
        # Test Apple
        login_use_case.execute("apple", {"code": "apple_code"})
        mock_apple_use_case.execute.assert_called_once()

    def test_case_sensitivity_of_login_types(self, login_use_case):
        """Test that login types are case sensitive"""
        # Arrange
        login_data = {"email": "test@example.com", "password": "pass"}
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            login_use_case.execute("EMAIL", login_data)  # Uppercase
        
        assert str(exc_info.value) == "Login type not supported"