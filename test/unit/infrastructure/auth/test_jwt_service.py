"""
Unit tests for JWTService
Tests JWT token creation, validation, and security features
"""
import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from flask import Flask

from src.infrastructure.auth.jwt_service import JWTService
from src.shared.exceptions.custom import InvalidTokenException
from src.config.config import Config


class TestJWTService:
    """Test suite for JWTService"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
        app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
        return app
    
    @pytest.fixture
    def mock_token_security_repo(self):
        """Mock TokenSecurityRepository"""
        return Mock()
    
    @pytest.fixture
    def jwt_service(self, mock_token_security_repo):
        """JWTService instance with mocked dependencies"""
        with patch('src.infrastructure.auth.jwt_service.TokenSecurityRepository') as mock_repo_class:
            mock_repo_class.return_value = mock_token_security_repo
            service = JWTService()
            service.token_security_repo = mock_token_security_repo
            return service
    
    @pytest.fixture
    def mock_request_context(self, app):
        """Create mock request context"""
        with app.test_request_context(
            '/',
            headers={'User-Agent': 'TestAgent/1.0'},
            environ_base={'REMOTE_ADDR': '192.168.1.100'}
        ):
            yield
    
    def test_constructor_initializes_repository(self):
        """Test that constructor initializes token security repository"""
        with patch('src.infrastructure.auth.jwt_service.TokenSecurityRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            
            # Act
            service = JWTService()
            
            # Assert
            mock_repo_class.assert_called_once()
            assert service.token_security_repo == mock_repo
    
    def test_create_tokens_success(self, jwt_service, mock_token_security_repo, mock_request_context):
        """Test successful token creation"""
        # Arrange
        identity = "user-123"
        mock_access_jti = "access-jti-123"
        mock_refresh_jti = "refresh-jti-456"
        
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.side_effect = [
                uuid.UUID(mock_access_jti.ljust(36, '0')),  # Pad to valid UUID length
                uuid.UUID(mock_refresh_jti.ljust(36, '0'))
            ]
            
            with patch('src.infrastructure.auth.jwt_service.create_access_token') as mock_create_access:
                with patch('src.infrastructure.auth.jwt_service.create_refresh_token') as mock_create_refresh:
                    with patch('datetime.datetime') as mock_datetime:
                        mock_create_access.return_value = "access_token_value"
                        mock_create_refresh.return_value = "refresh_token_value"
                        
                        fixed_datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
                        mock_datetime.now.return_value = fixed_datetime
                        
                        # Mock Config
                        with patch.object(Config, 'JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=30)):
                            # Act
                            result = jwt_service.create_tokens(identity)
                            
                            # Assert
                            assert result["access_token"] == "access_token_value"
                            assert result["refresh_token"] == "refresh_token_value"
                            assert result["token_type"] == "Bearer"
                            assert result["access_jti"] == mock_access_jti.ljust(36, '0')
                            assert result["refresh_jti"] == mock_refresh_jti.ljust(36, '0')
                            
                            # Verify token creation calls
                            mock_create_access.assert_called_once_with(
                                identity=identity,
                                additional_claims={"jti": mock_access_jti.ljust(36, '0')}
                            )
                            mock_create_refresh.assert_called_once_with(
                                identity=identity,
                                additional_claims={"jti": mock_refresh_jti.ljust(36, '0')}
                            )
                            
                            # Verify repository tracking call
                            expected_expires = fixed_datetime + timedelta(days=30)
                            mock_token_security_repo.track_refresh_token.assert_called_once_with(
                                jti=mock_refresh_jti.ljust(36, '0'),
                                user_uid=identity,
                                expires_at=expected_expires,
                                parent_jti=None,
                                ip_address='192.168.1.100',
                                user_agent='TestAgent/1.0'
                            )
    
    def test_create_tokens_with_parent_refresh_jti(self, jwt_service, mock_token_security_repo, mock_request_context):
        """Test token creation with parent refresh JTI (token rotation)"""
        # Arrange
        identity = "user-456"
        parent_refresh_jti = "parent-refresh-jti"
        
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.side_effect = [
                uuid.UUID('12345678-1234-5678-9012-123456789012'),
                uuid.UUID('87654321-4321-8765-2109-876543210987')
            ]
            
            with patch('src.infrastructure.auth.jwt_service.create_access_token'):
                with patch('src.infrastructure.auth.jwt_service.create_refresh_token'):
                    with patch('src.infrastructure.auth.jwt_service.security_logger') as mock_logger:
                        with patch('datetime.datetime') as mock_datetime:
                            mock_datetime.now.return_value = datetime.now(timezone.utc)
                            with patch.object(Config, 'JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=30)):
                                # Act
                                result = jwt_service.create_tokens(identity, parent_refresh_jti)
                                
                                # Assert
                                mock_token_security_repo.track_refresh_token.assert_called_once()
                                call_args = mock_token_security_repo.track_refresh_token.call_args[1]
                                assert call_args['parent_jti'] == parent_refresh_jti
                                
                                # Verify token rotation logging
                                mock_logger.log_token_rotation.assert_called_once_with(
                                    identity, parent_refresh_jti, '87654321-4321-8765-2109-876543210987'
                                )
    
    def test_get_client_ip_with_x_forwarded_for(self, jwt_service):
        """Test client IP extraction with X-Forwarded-For header"""
        with patch('flask.request') as mock_request:
            mock_request.headers.get.side_effect = lambda header, default=None: {
                'X-Forwarded-For': '203.0.113.195, 70.41.3.18, 150.172.238.178',
                'User-Agent': 'TestAgent'
            }.get(header, default)
            
            # Act
            ip = jwt_service._get_client_ip()
            
            # Assert
            assert ip == '203.0.113.195'  # First IP in the chain
    
    def test_get_client_ip_with_x_real_ip(self, jwt_service):
        """Test client IP extraction with X-Real-IP header"""
        with patch('flask.request') as mock_request:
            mock_request.headers.get.side_effect = lambda header, default=None: {
                'X-Forwarded-For': None,
                'X-Real-IP': '198.51.100.178',
                'User-Agent': 'TestAgent'
            }.get(header, default)
            
            # Act
            ip = jwt_service._get_client_ip()
            
            # Assert
            assert ip == '198.51.100.178'
    
    def test_get_client_ip_fallback_to_remote_addr(self, jwt_service):
        """Test client IP extraction fallback to remote_addr"""
        with patch('flask.request') as mock_request:
            mock_request.headers.get.return_value = None
            mock_request.remote_addr = '192.168.1.50'
            
            # Act
            ip = jwt_service._get_client_ip()
            
            # Assert
            assert ip == '192.168.1.50'
    
    def test_get_client_ip_unknown_fallback(self, jwt_service):
        """Test client IP extraction when all sources are None"""
        with patch('flask.request') as mock_request:
            mock_request.headers.get.return_value = None
            mock_request.remote_addr = None
            
            # Act
            ip = jwt_service._get_client_ip()
            
            # Assert
            assert ip == 'unknown'
    
    def test_decode_token_success(self, jwt_service, mock_token_security_repo):
        """Test successful token decoding"""
        # Arrange
        token = "valid_token"
        decoded_payload = {"sub": "user-123", "jti": "token-jti-123"}
        mock_token_security_repo.is_token_blacklisted.return_value = False
        
        with patch('src.infrastructure.auth.jwt_service.decode_token') as mock_decode:
            mock_decode.return_value = decoded_payload
            
            # Act
            result = jwt_service.decode_token(token)
            
            # Assert
            assert result == decoded_payload
            mock_decode.assert_called_once_with(token)
            mock_token_security_repo.is_token_blacklisted.assert_called_once_with("token-jti-123")
    
    def test_decode_token_blacklisted(self, jwt_service, mock_token_security_repo):
        """Test token decoding with blacklisted token"""
        # Arrange
        token = "blacklisted_token"
        decoded_payload = {"sub": "user-123", "jti": "blacklisted-jti"}
        mock_token_security_repo.is_token_blacklisted.return_value = True
        
        with patch('src.infrastructure.auth.jwt_service.decode_token') as mock_decode:
            with patch('src.infrastructure.auth.jwt_service.security_logger') as mock_logger:
                mock_decode.return_value = decoded_payload
                
                # Act & Assert
                with pytest.raises(InvalidTokenException, match="Token has been revoked"):
                    jwt_service.decode_token(token)
                
                # Verify logging
                mock_logger.log_security_event.assert_called_once()
    
    def test_decode_token_invalid_token(self, jwt_service, mock_token_security_repo):
        """Test token decoding with invalid token"""
        # Arrange
        token = "invalid_token"
        
        with patch('src.infrastructure.auth.jwt_service.decode_token') as mock_decode:
            with patch('src.infrastructure.auth.jwt_service.security_logger') as mock_logger:
                mock_decode.side_effect = Exception("Invalid token format")
                
                # Act & Assert
                with pytest.raises(InvalidTokenException):
                    jwt_service.decode_token(token)
                
                # Verify logging
                mock_logger.log_security_event.assert_called_once()
    
    def test_validate_refresh_token_use_success(self, jwt_service, mock_token_security_repo):
        """Test successful refresh token validation"""
        # Arrange
        refresh_jti = "valid-refresh-jti"
        user_uid = "user-123"
        
        mock_token_security_repo.is_token_blacklisted.return_value = False
        mock_token_security_repo.is_refresh_token_compromised.return_value = False
        mock_token_security_repo.mark_refresh_token_used.return_value = True
        
        # Act
        result = jwt_service.validate_refresh_token_use(refresh_jti, user_uid)
        
        # Assert
        assert result is True
        mock_token_security_repo.is_token_blacklisted.assert_called_once_with(refresh_jti)
        mock_token_security_repo.is_refresh_token_compromised.assert_called_once_with(refresh_jti)
        mock_token_security_repo.mark_refresh_token_used.assert_called_once_with(refresh_jti)
    
    def test_validate_refresh_token_use_blacklisted(self, jwt_service, mock_token_security_repo):
        """Test refresh token validation with blacklisted token"""
        # Arrange
        refresh_jti = "blacklisted-refresh-jti"
        user_uid = "user-123"
        
        mock_token_security_repo.is_token_blacklisted.return_value = True
        
        with patch('src.infrastructure.auth.jwt_service.security_logger') as mock_logger:
            # Act & Assert
            with pytest.raises(InvalidTokenException, match="Token has been revoked"):
                jwt_service.validate_refresh_token_use(refresh_jti, user_uid)
            
            # Verify logging
            mock_logger.log_security_event.assert_called_once()
    
    def test_validate_refresh_token_use_compromised(self, jwt_service, mock_token_security_repo):
        """Test refresh token validation with compromised token"""
        # Arrange
        refresh_jti = "compromised-refresh-jti"
        user_uid = "user-123"
        
        mock_token_security_repo.is_token_blacklisted.return_value = False
        mock_token_security_repo.is_refresh_token_compromised.return_value = True
        
        with patch('src.infrastructure.auth.jwt_service.security_logger') as mock_logger:
            # Act & Assert
            with pytest.raises(InvalidTokenException, match="Security breach detected"):
                jwt_service.validate_refresh_token_use(refresh_jti, user_uid)
            
            # Verify security actions
            mock_token_security_repo.blacklist_all_user_tokens.assert_called_once_with(
                user_uid=user_uid,
                reason='refresh_token_reuse_detected'
            )
            mock_logger.log_token_reuse.assert_called_once_with(user_uid, refresh_jti)
            mock_logger.log_security_event.assert_called()
    
    def test_validate_refresh_token_use_double_use(self, jwt_service, mock_token_security_repo):
        """Test refresh token validation with double use detection"""
        # Arrange
        refresh_jti = "double-used-refresh-jti"
        user_uid = "user-123"
        
        mock_token_security_repo.is_token_blacklisted.return_value = False
        mock_token_security_repo.is_refresh_token_compromised.return_value = False
        mock_token_security_repo.mark_refresh_token_used.return_value = False  # Already used
        
        with patch('src.infrastructure.auth.jwt_service.security_logger') as mock_logger:
            # Act & Assert
            with pytest.raises(InvalidTokenException, match="Security breach detected"):
                jwt_service.validate_refresh_token_use(refresh_jti, user_uid)
            
            # Verify security actions
            mock_token_security_repo.blacklist_all_user_tokens.assert_called_once_with(
                user_uid=user_uid,
                reason='refresh_token_reuse_detected'
            )
            mock_logger.log_token_reuse.assert_called_once_with(user_uid, refresh_jti)
    
    def test_revoke_token_access_token(self, jwt_service, mock_token_security_repo):
        """Test revoking an access token"""
        # Arrange
        jti = "access-token-jti"
        token_type = "access"
        user_uid = "user-123"
        reason = "logout"
        
        with patch('datetime.datetime') as mock_datetime:
            with patch('src.infrastructure.auth.jwt_service.security_logger') as mock_logger:
                fixed_datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
                mock_datetime.now.return_value = fixed_datetime
                
                with patch.object(Config, 'JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=1)):
                    mock_token_security_repo.add_to_blacklist.return_value = True
                    
                    # Act
                    result = jwt_service.revoke_token(jti, token_type, user_uid, reason)
                    
                    # Assert
                    assert result is True
                    expected_expires = fixed_datetime + timedelta(hours=1)
                    mock_token_security_repo.add_to_blacklist.assert_called_once_with(
                        jti=jti,
                        token_type=token_type,
                        user_uid=user_uid,
                        expires_at=expected_expires,
                        reason=reason
                    )
                    mock_logger.log_security_event.assert_called_once()
    
    def test_revoke_token_refresh_token(self, jwt_service, mock_token_security_repo):
        """Test revoking a refresh token"""
        # Arrange
        jti = "refresh-token-jti"
        token_type = "refresh"
        user_uid = "user-456"
        
        with patch('datetime.datetime') as mock_datetime:
            with patch('src.infrastructure.auth.jwt_service.security_logger') as mock_logger:
                fixed_datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
                mock_datetime.now.return_value = fixed_datetime
                
                with patch.object(Config, 'JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=30)):
                    mock_token_security_repo.add_to_blacklist.return_value = True
                    
                    # Act
                    result = jwt_service.revoke_token(jti, token_type, user_uid)
                    
                    # Assert
                    expected_expires = fixed_datetime + timedelta(days=30)
                    mock_token_security_repo.add_to_blacklist.assert_called_once_with(
                        jti=jti,
                        token_type=token_type,
                        user_uid=user_uid,
                        expires_at=expected_expires,
                        reason='logout'  # Default reason
                    )
    
    def test_revoke_all_user_tokens(self, jwt_service, mock_token_security_repo):
        """Test revoking all tokens for a user"""
        # Arrange
        user_uid = "user-789"
        reason = "security_breach"
        mock_token_security_repo.blacklist_all_user_tokens.return_value = 5
        
        with patch('src.infrastructure.auth.jwt_service.security_logger') as mock_logger:
            # Act
            result = jwt_service.revoke_all_user_tokens(user_uid, reason)
            
            # Assert
            assert result == 5
            mock_token_security_repo.blacklist_all_user_tokens.assert_called_once_with(user_uid, reason)
            mock_logger.log_security_event.assert_called_once()
            
            # Verify log content
            log_call = mock_logger.log_security_event.call_args[1]
            assert log_call["user_uid"] == user_uid
            assert log_call["reason"] == reason
            assert log_call["tokens_revoked"] == 5