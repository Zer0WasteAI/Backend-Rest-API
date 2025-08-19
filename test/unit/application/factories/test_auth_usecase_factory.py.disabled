"""
Unit tests for Auth Use Case Factory
Tests factory functions for authentication-related use cases
"""
import pytest
from unittest.mock import Mock, patch

from src.application.factories.auth_usecase_factory import (
    make_login_user_use_case,
    make_register_user_use_case,
    make_validate_token_use_case,
    make_google_oauth_use_case,
    make_refresh_token_use_case
)


class TestAuthUseCaseFactory:
    """Test suite for Auth Use Case Factory"""

    @patch('src.application.factories.auth_usecase_factory.make_user_repository')
    @patch('src.application.factories.auth_usecase_factory.make_login_by_email_use_case')
    @patch('src.application.factories.auth_usecase_factory.make_login_by_username_use_case')
    def test_make_login_user_use_case(self, mock_username_use_case, mock_email_use_case, mock_user_repo):
        """Test login user use case factory"""
        # Arrange
        mock_user_repo.return_value = Mock()
        mock_email_use_case.return_value = Mock()
        mock_username_use_case.return_value = Mock()
        
        # Act
        result = make_login_user_use_case()
        
        # Assert
        assert result is not None
        mock_user_repo.assert_called_once()
        mock_email_use_case.assert_called_once()
        mock_username_use_case.assert_called_once()

    @patch('src.application.factories.auth_usecase_factory.make_user_repository')
    @patch('src.application.factories.auth_usecase_factory.make_auth_service')
    def test_make_register_user_use_case(self, mock_auth_service, mock_user_repo):
        """Test register user use case factory"""
        # Arrange
        mock_user_repo.return_value = Mock()
        mock_auth_service.return_value = Mock()
        
        # Act
        result = make_register_user_use_case()
        
        # Assert
        assert result is not None
        mock_user_repo.assert_called_once()
        mock_auth_service.assert_called_once()

    @patch('src.application.factories.auth_usecase_factory.make_auth_service')
    def test_make_validate_token_use_case(self, mock_auth_service):
        """Test validate token use case factory"""
        # Arrange
        mock_auth_service.return_value = Mock()
        
        # Act
        result = make_validate_token_use_case()
        
        # Assert
        assert result is not None
        mock_auth_service.assert_called_once()

    @patch('src.application.factories.auth_usecase_factory.make_user_repository')
    @patch('src.application.factories.auth_usecase_factory.make_oauth_service')
    @patch('src.application.factories.auth_usecase_factory.make_auth_service')
    def test_make_google_oauth_use_case(self, mock_auth_service, mock_oauth_service, mock_user_repo):
        """Test Google OAuth use case factory"""
        # Arrange
        mock_user_repo.return_value = Mock()
        mock_oauth_service.return_value = Mock()
        mock_auth_service.return_value = Mock()
        
        # Act
        result = make_google_oauth_use_case()
        
        # Assert
        assert result is not None
        mock_user_repo.assert_called_once()
        mock_oauth_service.assert_called_once()
        mock_auth_service.assert_called_once()

    @patch('src.application.factories.auth_usecase_factory.make_auth_service')
    def test_make_refresh_token_use_case(self, mock_auth_service):
        """Test refresh token use case factory"""
        # Arrange
        mock_auth_service.return_value = Mock()
        
        # Act
        result = make_refresh_token_use_case()
        
        # Assert
        assert result is not None
        mock_auth_service.assert_called_once()

    def test_factory_functions_exist(self):
        """Test that all factory functions are defined"""
        assert callable(make_login_user_use_case)
        assert callable(make_register_user_use_case)
        assert callable(make_validate_token_use_case)
        assert callable(make_google_oauth_use_case)
        assert callable(make_refresh_token_use_case)

    @patch('src.application.factories.auth_usecase_factory.make_user_repository')
    @patch('src.application.factories.auth_usecase_factory.make_login_by_email_use_case')
    @patch('src.application.factories.auth_usecase_factory.make_login_by_username_use_case')
    def test_make_login_user_use_case_error_handling(self, mock_username_use_case, mock_email_use_case, mock_user_repo):
        """Test login user use case factory error handling"""
        # Arrange
        mock_user_repo.side_effect = Exception("Repository creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_login_user_use_case()
        
        assert str(exc_info.value) == "Repository creation failed"

    @patch('src.application.factories.auth_usecase_factory.make_user_repository')
    @patch('src.application.factories.auth_usecase_factory.make_auth_service')
    def test_make_register_user_use_case_error_handling(self, mock_auth_service, mock_user_repo):
        """Test register user use case factory error handling"""
        # Arrange
        mock_auth_service.side_effect = Exception("Auth service creation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            make_register_user_use_case()
        
        assert str(exc_info.value) == "Auth service creation failed"