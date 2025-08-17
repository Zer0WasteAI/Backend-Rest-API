"""
Unit tests for Auth Service
Tests authentication service abstract interface and implementations
"""
import pytest
from unittest.mock import Mock

from src.domain.services.auth_service import AuthService


class ConcreteAuthService(AuthService):
    """Concrete implementation for testing"""
    
    def __init__(self, mock_token_creator=None, mock_token_decoder=None):
        self.mock_token_creator = mock_token_creator or Mock()
        self.mock_token_decoder = mock_token_decoder or Mock()
    
    def create_tokens(self, identity: str) -> dict:
        """Implementation for testing"""
        return self.mock_token_creator(identity)
    
    def decode_token(self, token: str) -> dict:
        """Implementation for testing"""
        return self.mock_token_decoder(token)


class TestAuthService:
    """Test suite for Auth Service"""
    
    @pytest.fixture
    def mock_token_creator(self):
        """Mock token creator function"""
        mock = Mock()
        mock.return_value = {
            "access_token": "jwt_access_token_123",
            "refresh_token": "jwt_refresh_token_456",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        return mock
    
    @pytest.fixture
    def mock_token_decoder(self):
        """Mock token decoder function"""
        mock = Mock()
        mock.return_value = {
            "sub": "user_123",
            "iat": 1642678800,
            "exp": 1642682400,
            "scope": "read write"
        }
        return mock
    
    @pytest.fixture
    def auth_service(self, mock_token_creator, mock_token_decoder):
        """Create concrete auth service for testing"""
        return ConcreteAuthService(mock_token_creator, mock_token_decoder)

    def test_create_tokens_success(self, auth_service, mock_token_creator):
        """Test successful token creation"""
        # Act
        result = auth_service.create_tokens("user_123")
        
        # Assert
        assert result["access_token"] == "jwt_access_token_123"
        assert result["refresh_token"] == "jwt_refresh_token_456"
        assert result["expires_in"] == 3600
        assert result["token_type"] == "Bearer"
        mock_token_creator.assert_called_once_with("user_123")

    def test_decode_token_success(self, auth_service, mock_token_decoder):
        """Test successful token decoding"""
        # Act
        result = auth_service.decode_token("jwt_token_123")
        
        # Assert
        assert result["sub"] == "user_123"
        assert result["iat"] == 1642678800
        assert result["exp"] == 1642682400
        assert result["scope"] == "read write"
        mock_token_decoder.assert_called_once_with("jwt_token_123")

    def test_create_tokens_with_different_identity(self, auth_service, mock_token_creator):
        """Test token creation with different identity"""
        # Arrange
        mock_token_creator.return_value = {
            "access_token": "jwt_access_token_456",
            "refresh_token": "jwt_refresh_token_789"
        }
        
        # Act
        result = auth_service.create_tokens("user_456")
        
        # Assert
        assert result["access_token"] == "jwt_access_token_456"
        assert result["refresh_token"] == "jwt_refresh_token_789"
        mock_token_creator.assert_called_once_with("user_456")

    def test_decode_token_with_different_token(self, auth_service, mock_token_decoder):
        """Test token decoding with different token"""
        # Arrange
        mock_token_decoder.return_value = {
            "sub": "user_456",
            "iat": 1642679000,
            "exp": 1642682600
        }
        
        # Act
        result = auth_service.decode_token("jwt_token_456")
        
        # Assert
        assert result["sub"] == "user_456"
        assert result["iat"] == 1642679000
        assert result["exp"] == 1642682600
        mock_token_decoder.assert_called_once_with("jwt_token_456")

    def test_create_tokens_error_propagation(self, mock_token_decoder):
        """Test that token creation errors are propagated"""
        # Arrange
        error_token_creator = Mock()
        error_token_creator.side_effect = Exception("Token creation failed")
        auth_service = ConcreteAuthService(error_token_creator, mock_token_decoder)
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            auth_service.create_tokens("user_123")
        
        assert str(exc_info.value) == "Token creation failed"

    def test_decode_token_error_propagation(self, mock_token_creator):
        """Test that token decoding errors are propagated"""
        # Arrange
        error_token_decoder = Mock()
        error_token_decoder.side_effect = Exception("Invalid token")
        auth_service = ConcreteAuthService(mock_token_creator, error_token_decoder)
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            auth_service.decode_token("invalid_token")
        
        assert str(exc_info.value) == "Invalid token"

    def test_abstract_methods_exist(self):
        """Test that abstract methods are defined"""
        # Assert
        assert hasattr(AuthService, 'create_tokens')
        assert hasattr(AuthService, 'decode_token')
        assert AuthService.create_tokens.__isabstractmethod__
        assert AuthService.decode_token.__isabstractmethod__

    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated directly"""
        # Act & Assert
        with pytest.raises(TypeError):
            AuthService()

    def test_create_tokens_empty_identity(self, auth_service, mock_token_creator):
        """Test token creation with empty identity"""
        # Act
        auth_service.create_tokens("")
        
        # Assert
        mock_token_creator.assert_called_once_with("")

    def test_decode_token_empty_token(self, auth_service, mock_token_decoder):
        """Test token decoding with empty token"""
        # Act
        auth_service.decode_token("")
        
        # Assert
        mock_token_decoder.assert_called_once_with("")

    def test_create_tokens_none_identity(self, auth_service, mock_token_creator):
        """Test token creation with None identity"""
        # Act
        auth_service.create_tokens(None)
        
        # Assert
        mock_token_creator.assert_called_once_with(None)

    def test_decode_token_none_token(self, auth_service, mock_token_decoder):
        """Test token decoding with None token"""
        # Act
        auth_service.decode_token(None)
        
        # Assert
        mock_token_decoder.assert_called_once_with(None)

    def test_multiple_token_creation_calls(self, auth_service, mock_token_creator):
        """Test multiple calls to create_tokens"""
        # Act
        auth_service.create_tokens("user_1")
        auth_service.create_tokens("user_2")
        auth_service.create_tokens("user_3")
        
        # Assert
        assert mock_token_creator.call_count == 3
        mock_token_creator.assert_any_call("user_1")
        mock_token_creator.assert_any_call("user_2")
        mock_token_creator.assert_any_call("user_3")

    def test_multiple_token_decoding_calls(self, auth_service, mock_token_decoder):
        """Test multiple calls to decode_token"""
        # Act
        auth_service.decode_token("token_1")
        auth_service.decode_token("token_2")
        auth_service.decode_token("token_3")
        
        # Assert
        assert mock_token_decoder.call_count == 3
        mock_token_decoder.assert_any_call("token_1")
        mock_token_decoder.assert_any_call("token_2")
        mock_token_decoder.assert_any_call("token_3")