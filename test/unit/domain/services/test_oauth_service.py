"""
Unit tests for OAuthService abstract interface
Tests the contract and behavior expectations for OAuth service implementations
"""
import pytest
from abc import ABCMeta
from unittest.mock import Mock

from src.domain.services.oauth_service import OAuthService


class TestOAuthService:
    """Test suite for OAuthService abstract interface"""
    
    def test_oauth_service_is_abstract(self):
        """Test that OAuthService is an abstract base class"""
        # Act & Assert
        assert OAuthService.__bases__ == (ABCMeta,)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            OAuthService()
    
    def test_get_user_info_is_abstract_method(self):
        """Test that get_user_info is defined as abstract method"""
        # Arrange
        abstract_methods = OAuthService.__abstractmethods__
        
        # Assert
        assert 'get_user_info' in abstract_methods
    
    def test_get_user_info_signature_and_documentation(self):
        """Test get_user_info method signature and documentation"""
        # Arrange
        method = OAuthService.get_user_info
        
        # Assert
        assert hasattr(OAuthService, 'get_user_info')
        assert method.__doc__ is not None
        assert 'Retrieve user information from the OAuth provider' in method.__doc__
        assert ':param code: The authorization code' in method.__doc__
        assert ':return: A dictionary containing user information' in method.__doc__


class ConcreteOAuthService(OAuthService):
    """Concrete implementation for testing purposes"""
    
    def __init__(self):
        self.auth_requests = []
        self.user_database = {
            "valid_code_123": {
                "id": "12345",
                "email": "user@example.com",
                "name": "John Doe",
                "verified": True,
                "provider": "google"
            },
            "valid_code_456": {
                "id": "67890", 
                "email": "jane@example.com",
                "name": "Jane Smith",
                "verified": True,
                "provider": "facebook"
            },
            "expired_code": {
                "error": "expired_token",
                "message": "Authorization code has expired"
            },
            "invalid_code": {
                "error": "invalid_grant", 
                "message": "Invalid authorization code"
            }
        }
    
    def get_user_info(self, code: str) -> dict:
        """Mock implementation for OAuth user info retrieval"""
        # Log the request
        self.auth_requests.append({
            "code": code,
            "timestamp": "2024-01-01T12:00:00Z"
        })
        
        # Simulate different OAuth scenarios
        if code in self.user_database:
            return self.user_database[code]
        elif code == "":
            raise ValueError("Authorization code cannot be empty")
        elif code is None:
            raise ValueError("Authorization code cannot be None")
        else:
            return {
                "error": "invalid_request",
                "message": f"Unknown authorization code: {code}"
            }


class FailingOAuthService(OAuthService):
    """OAuth service that fails for testing error scenarios"""
    
    def get_user_info(self, code: str) -> dict:
        """Implementation that always fails"""
        raise Exception("OAuth service unavailable")


class TestConcreteOAuthService:
    """Test suite for concrete OAuthService implementation"""
    
    @pytest.fixture
    def oauth_service(self):
        """Concrete OAuth service for testing"""
        return ConcreteOAuthService()
    
    def test_concrete_implementation_can_be_instantiated(self, oauth_service):
        """Test that concrete implementation can be created"""
        # Assert
        assert isinstance(oauth_service, OAuthService)
        assert isinstance(oauth_service, ConcreteOAuthService)
        assert len(oauth_service.auth_requests) == 0
    
    def test_get_user_info_with_valid_google_code(self, oauth_service):
        """Test user info retrieval with valid Google OAuth code"""
        # Arrange
        code = "valid_code_123"
        
        # Act
        result = oauth_service.get_user_info(code)
        
        # Assert
        assert isinstance(result, dict)
        assert result["id"] == "12345"
        assert result["email"] == "user@example.com"
        assert result["name"] == "John Doe"
        assert result["verified"] is True
        assert result["provider"] == "google"
        
        # Verify request was logged
        assert len(oauth_service.auth_requests) == 1
        assert oauth_service.auth_requests[0]["code"] == code
    
    def test_get_user_info_with_valid_facebook_code(self, oauth_service):
        """Test user info retrieval with valid Facebook OAuth code"""
        # Arrange
        code = "valid_code_456"
        
        # Act
        result = oauth_service.get_user_info(code)
        
        # Assert
        assert result["id"] == "67890"
        assert result["email"] == "jane@example.com"
        assert result["name"] == "Jane Smith"
        assert result["provider"] == "facebook"
    
    def test_get_user_info_with_expired_code(self, oauth_service):
        """Test user info retrieval with expired authorization code"""
        # Arrange
        code = "expired_code"
        
        # Act
        result = oauth_service.get_user_info(code)
        
        # Assert
        assert "error" in result
        assert result["error"] == "expired_token"
        assert "expired" in result["message"]
    
    def test_get_user_info_with_invalid_code(self, oauth_service):
        """Test user info retrieval with invalid authorization code"""
        # Arrange
        code = "invalid_code"
        
        # Act
        result = oauth_service.get_user_info(code)
        
        # Assert
        assert "error" in result
        assert result["error"] == "invalid_grant"
        assert "Invalid authorization code" in result["message"]
    
    def test_get_user_info_with_unknown_code(self, oauth_service):
        """Test user info retrieval with unknown authorization code"""
        # Arrange
        code = "completely_unknown_code"
        
        # Act
        result = oauth_service.get_user_info(code)
        
        # Assert
        assert "error" in result
        assert result["error"] == "invalid_request"
        assert code in result["message"]
    
    def test_get_user_info_with_empty_code(self, oauth_service):
        """Test user info retrieval with empty authorization code"""
        # Arrange
        code = ""
        
        # Act & Assert
        with pytest.raises(ValueError, match="Authorization code cannot be empty"):
            oauth_service.get_user_info(code)
    
    def test_get_user_info_with_none_code(self, oauth_service):
        """Test user info retrieval with None authorization code"""
        # Arrange
        code = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Authorization code cannot be None"):
            oauth_service.get_user_info(code)
    
    @pytest.mark.parametrize("code,expected_provider", [
        ("valid_code_123", "google"),
        ("valid_code_456", "facebook"),
    ])
    def test_get_user_info_provider_identification(self, oauth_service, code, expected_provider):
        """Parametrized test for different OAuth providers"""
        # Act
        result = oauth_service.get_user_info(code)
        
        # Assert
        assert result["provider"] == expected_provider
        assert "error" not in result
    
    def test_multiple_auth_requests_tracking(self, oauth_service):
        """Test that multiple auth requests are properly tracked"""
        # Arrange
        codes = ["valid_code_123", "valid_code_456", "invalid_code"]
        
        # Act
        results = []
        for code in codes:
            result = oauth_service.get_user_info(code)
            results.append(result)
        
        # Assert
        assert len(oauth_service.auth_requests) == 3
        
        for i, code in enumerate(codes):
            assert oauth_service.auth_requests[i]["code"] == code
        
        # Verify different results for different codes
        assert len(set(str(result) for result in results)) == 3  # All results should be different
    
    def test_user_info_structure_consistency(self, oauth_service):
        """Test that successful user info responses have consistent structure"""
        # Arrange
        valid_codes = ["valid_code_123", "valid_code_456"]
        
        # Act & Assert
        for code in valid_codes:
            result = oauth_service.get_user_info(code)
            
            # Check required fields for successful responses
            assert "id" in result
            assert "email" in result
            assert "name" in result
            assert "verified" in result
            assert "provider" in result
            
            # Check field types
            assert isinstance(result["id"], str)
            assert isinstance(result["email"], str)
            assert isinstance(result["name"], str)
            assert isinstance(result["verified"], bool)
            assert isinstance(result["provider"], str)
            
            # Check email format (basic validation)
            assert "@" in result["email"]
            assert "." in result["email"]
    
    def test_error_response_structure_consistency(self, oauth_service):
        """Test that error responses have consistent structure"""
        # Arrange
        error_codes = ["expired_code", "invalid_code", "unknown_code"]
        
        # Act & Assert
        for code in error_codes:
            result = oauth_service.get_user_info(code)
            
            # Check required fields for error responses
            assert "error" in result
            assert "message" in result
            
            # Check field types
            assert isinstance(result["error"], str)
            assert isinstance(result["message"], str)
            
            # Error code should not be empty
            assert len(result["error"]) > 0
            assert len(result["message"]) > 0


class TestOAuthServiceErrorHandling:
    """Test suite for OAuth service error scenarios"""
    
    @pytest.fixture
    def failing_oauth_service(self):
        """OAuth service that always fails"""
        return FailingOAuthService()
    
    def test_oauth_service_exception_handling(self, failing_oauth_service):
        """Test that OAuth service exceptions are properly raised"""
        # Act & Assert
        with pytest.raises(Exception, match="OAuth service unavailable"):
            failing_oauth_service.get_user_info("any_code")
    
    def test_oauth_service_network_failure_simulation(self, oauth_service):
        """Test OAuth service behavior during network failures"""
        # This test simulates what might happen during network issues
        # In a real implementation, network failures might be handled differently
        
        # Arrange - Using a code that simulates network timeout
        oauth_service.user_database["network_timeout"] = {
            "error": "network_error",
            "message": "Request timeout - please try again"
        }
        
        # Act
        result = oauth_service.get_user_info("network_timeout")
        
        # Assert
        assert result["error"] == "network_error"
        assert "timeout" in result["message"]


class TestOAuthServiceIntegration:
    """Integration-style tests for OAuth service behavior"""
    
    @pytest.fixture
    def oauth_service(self):
        return ConcreteOAuthService()
    
    def test_complete_oauth_flow_simulation(self, oauth_service):
        """Test complete OAuth flow simulation"""
        # Arrange - Simulate a complete OAuth flow
        authorization_code = "valid_code_123"
        
        # Act - Step 1: Exchange code for user info
        user_info = oauth_service.get_user_info(authorization_code)
        
        # Assert - Step 1: Verify user info was retrieved
        assert "id" in user_info
        assert "email" in user_info
        assert user_info["verified"] is True
        
        # Act - Step 2: Simulate using the same code again (should still work in our mock)
        user_info_again = oauth_service.get_user_info(authorization_code)
        
        # Assert - Step 2: Should get the same user info
        assert user_info == user_info_again
        
        # Assert - Verify both requests were logged
        assert len(oauth_service.auth_requests) == 2
    
    def test_oauth_service_with_different_user_types(self, oauth_service):
        """Test OAuth service with different types of users"""
        # Test verified user
        verified_user = oauth_service.get_user_info("valid_code_123")
        assert verified_user["verified"] is True
        
        # Test another verified user
        another_user = oauth_service.get_user_info("valid_code_456")
        assert another_user["verified"] is True
        
        # Verify they are different users
        assert verified_user["id"] != another_user["id"]
        assert verified_user["email"] != another_user["email"]