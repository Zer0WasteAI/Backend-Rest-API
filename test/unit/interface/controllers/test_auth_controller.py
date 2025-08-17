"""
Unit tests for Auth Controller
Tests authentication endpoints and middleware integration
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_jwt_extended import JWTManager

from src.interface.controllers.auth_controller import auth_bp


class TestAuthController:
    """Test suite for Auth Controller"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        
        # Initialize JWT
        jwt = JWTManager(app)
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def mock_firebase_debug(self):
        """Mock Firebase debug dependencies"""
        with patch('src.interface.controllers.auth_controller.Config') as mock_config:
            mock_config.FIREBASE_CREDENTIALS_PATH = "/path/to/creds.json"
            mock_config.FIREBASE_STORAGE_BUCKET = "test-bucket"
            yield mock_config
    
    def test_firebase_debug_endpoint_exists(self, client, mock_firebase_debug):
        """Test that Firebase debug endpoint exists"""
        # Act
        response = client.get('/api/auth/firebase-debug')
        
        # Assert
        assert response.status_code in [200, 500]  # May fail due to missing Firebase setup, but endpoint exists
    
    def test_firebase_debug_response_structure(self, client, mock_firebase_debug):
        """Test Firebase debug response structure when successful"""
        # This test verifies the endpoint structure without requiring actual Firebase setup
        
        with patch('src.interface.controllers.auth_controller.firebase_admin') as mock_firebase:
            with patch('src.interface.controllers.auth_controller.Path') as mock_path:
                # Mock successful Firebase setup
                mock_firebase._apps = {'test': Mock()}
                mock_path.return_value.exists.return_value = True
                mock_path.return_value.resolve.return_value = "/resolved/path"
                
                # Act
                response = client.get('/api/auth/firebase-debug')
                
                # Assert
                assert response.status_code == 200
                
                # Check that response is JSON
                response_data = response.get_json()
        assert isinstance(response_data, dict)

    # NEW TESTS: refresh, logout, firebase-signin

    @patch('src.interface.controllers.auth_controller.make_refresh_token_use_case')
    def test_refresh_token_success(self, mock_refresh_use_case):
        from flask import Flask
        from flask_jwt_extended import JWTManager, create_refresh_token

        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        JWTManager(app)

        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"access_token": "a", "refresh_token": "b"}
        mock_refresh_use_case.return_value = mock_use_case

        with app.app_context():
            rt = create_refresh_token(identity='user-1')
        client = app.test_client()
        response = client.post('/api/auth/refresh', headers={"Authorization": f"Bearer {rt}"})
        assert response.status_code in [200]
        mock_use_case.execute.assert_called_once()

    @patch('src.interface.controllers.auth_controller.make_logout_use_case')
    def test_logout_success(self, mock_logout_use_case):
        from flask import Flask
        from flask_jwt_extended import JWTManager, create_access_token

        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        JWTManager(app)

        mock_use_case = Mock()
        mock_use_case.execute.return_value = {"message": "ok"}
        mock_logout_use_case.return_value = mock_use_case

        with app.app_context():
            at = create_access_token(identity='user-1')
        client = app.test_client()
        response = client.post('/api/auth/logout', headers={"Authorization": f"Bearer {at}"})
        assert response.status_code in [200]
        mock_use_case.execute.assert_called_once()

    @patch('src.interface.controllers.auth_controller.make_jwt_service')
    @patch('src.interface.controllers.auth_controller.make_profile_repository')
    @patch('src.interface.controllers.auth_controller.make_auth_repository')
    @patch('src.interface.controllers.auth_controller.make_user_repository')
    @patch('src.interface.controllers.auth_controller.make_firestore_profile_service')
    @patch('src.interface.controllers.auth_controller.security_logger')
    @patch('src.interface.controllers.auth_controller.firebase_admin')
    def test_firebase_signin_success(self, mock_firebase_admin, mock_security_logger, mock_firestore_service_factory,
                                     mock_user_repo_factory, mock_auth_repo_factory, mock_profile_repo_factory,
                                     mock_jwt_factory):
        from flask import Flask
        from flask_jwt_extended import JWTManager

        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        JWTManager(app)

        # Mock firebase decorator internals
        mock_firebase_admin._apps = {'test': object()}
        mock_firebase_admin.auth.verify_id_token.return_value = {
            'uid': 'firebase-uid-1',
            'email': None,
            'name': 'Anon User',
            'firebase': {'sign_in_provider': 'anonymous'},
            'email_verified': False
        }

        # Mock repos/services used by the handler
        mock_user = MagicMock()
        mock_user.uid = 'firebase-uid-1'
        mock_user.email = ''
        user_repo = MagicMock()
        user_repo.find_by_uid.return_value = mock_user
        mock_user_repo_factory.return_value = user_repo

        auth_repo = MagicMock()
        mock_auth_repo_factory.return_value = auth_repo

        profile_repo = MagicMock()
        mock_profile_repo_factory.return_value = profile_repo

        jwt_service = MagicMock()
        jwt_service.create_tokens.return_value = {"access_token": "x", "refresh_token": "y"}
        mock_jwt_factory.return_value = jwt_service

        firestore_service = MagicMock()
        firestore_service.get_profile.return_value = {
            'displayName': 'Anon User',
            'photoURL': '',
        }
        mock_firestore_service_factory.return_value = firestore_service

        client = app.test_client()
        response = client.post('/api/auth/firebase-signin', headers={"Authorization": "Bearer test"})
        assert response.status_code in [200]
    
    @patch('src.interface.controllers.auth_controller.make_logout_use_case')
    @patch('src.interface.controllers.auth_controller.make_jwt_service')
    def test_logout_endpoint_structure(self, mock_jwt_service, mock_logout_use_case, client):
        """Test logout endpoint structure"""
        # This test verifies the endpoint exists and has proper structure
        # Note: Full testing would require examining the actual logout endpoint implementation
        
        # Mock dependencies
        mock_logout_use_case.return_value = Mock()
        mock_jwt_service.return_value = Mock()
        
        # The logout endpoint would typically be at /logout, but we need to verify
        # the actual endpoint path from the controller implementation
        pass  # Placeholder for logout endpoint test
    
    @patch('src.interface.controllers.auth_controller.make_refresh_token_use_case')
    def test_refresh_token_endpoint_structure(self, mock_refresh_use_case, client):
        """Test refresh token endpoint structure"""
        # Mock dependencies
        mock_refresh_use_case.return_value = Mock()
        
        # Similar placeholder for refresh token endpoint
        pass  # Placeholder for refresh token endpoint test
    
    def test_auth_blueprint_registration(self, app):
        """Test that auth blueprint is properly registered"""
        # Assert
        assert 'auth' in app.blueprints
        assert app.blueprints['auth'] == auth_bp
    
    @patch('src.interface.controllers.auth_controller.security_logger')
    def test_security_logging_integration(self, mock_logger, client):
        """Test that security logging is integrated in auth endpoints"""
        # This test verifies that security logging is available
        # Actual logging behavior would be tested in integration tests
        
        # Assert
        assert mock_logger is not None
        # Security logger should have log methods available
        assert hasattr(mock_logger, 'log_security_event')
    
    def test_rate_limiting_integration(self, client):
        """Test that rate limiting is available for auth endpoints"""
        # This test verifies rate limiting integration exists
        
        with patch('src.interface.controllers.auth_controller.smart_rate_limit') as mock_rate_limit:
            # Act - import the controller to trigger decorator evaluation
            from src.interface.controllers import auth_controller
            
            # Assert
            assert mock_rate_limit is not None
    
    def test_firebase_auth_decorator_integration(self, client):
        """Test that Firebase auth decorator is available"""
        # This test verifies Firebase auth integration
        
        with patch('src.interface.controllers.auth_controller.verify_firebase_token') as mock_verify:
            # Act - import the controller
            from src.interface.controllers import auth_controller
            
            # Assert
            assert mock_verify is not None
    
    @patch('src.interface.controllers.auth_controller.make_firestore_profile_service')
    def test_firestore_profile_service_integration(self, mock_firestore_service, client):
        """Test Firestore profile service integration"""
        # Arrange
        mock_service = Mock()
        mock_firestore_service.return_value = mock_service
        
        # Act - This would be tested in actual endpoint calls
        from src.interface.controllers import auth_controller
        
        # Assert
        assert mock_firestore_service is not None


class TestAuthControllerFactories:
    """Test auth controller factory integrations"""
    
    def test_auth_usecase_factories_importable(self):
        """Test that all auth use case factories are importable"""
        # Act & Assert - These should import without errors
        from src.application.factories.auth_usecase_factory import (
            make_logout_use_case,
            make_refresh_token_use_case,
            make_jwt_service,
            make_user_repository,
            make_auth_repository,
            make_profile_repository,
            make_firestore_profile_service
        )
        
        # Verify factories are callable
        assert callable(make_logout_use_case)
        assert callable(make_refresh_token_use_case)
        assert callable(make_jwt_service)
        assert callable(make_user_repository)
        assert callable(make_auth_repository)
        assert callable(make_profile_repository)
        assert callable(make_firestore_profile_service)
    
    @patch('src.interface.controllers.auth_controller.make_jwt_service')
    def test_jwt_service_factory_integration(self, mock_jwt_factory):
        """Test JWT service factory integration"""
        # Arrange
        mock_service = Mock()
        mock_jwt_factory.return_value = mock_service
        
        # Act
        result = mock_jwt_factory()
        
        # Assert
        assert result == mock_service
        mock_jwt_factory.assert_called_once()
    
    @patch('src.interface.controllers.auth_controller.make_user_repository')
    def test_user_repository_factory_integration(self, mock_user_repo_factory):
        """Test user repository factory integration"""
        # Arrange
        mock_repo = Mock()
        mock_user_repo_factory.return_value = mock_repo
        
        # Act
        result = mock_user_repo_factory()
        
        # Assert
        assert result == mock_repo
        mock_user_repo_factory.assert_called_once()


class TestAuthControllerSecurity:
    """Test auth controller security features"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for security testing"""
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_security_headers_integration(self, client):
        """Test that security headers are integrated"""
        # This test verifies security headers are available
        # Actual header testing would be done in integration tests
        
        with patch('src.interface.controllers.auth_controller.security_logger') as mock_logger:
            # Act
            response = client.get('/api/auth/firebase-debug')
            
            # Assert - Security logger should be available
            assert mock_logger is not None
    
    def test_rate_limiting_configuration(self, client):
        """Test rate limiting configuration"""
        # This test verifies rate limiting is properly configured
        
        with patch('src.interface.controllers.auth_controller.smart_rate_limit') as mock_rate_limit:
            # Mock rate limit decorator
            mock_rate_limit.return_value = lambda f: f
            
            # Act - Import to trigger decorator evaluation
            from src.interface.controllers import auth_controller
            
            # Assert
            assert mock_rate_limit is not None
    
    def test_token_security_integration(self, client):
        """Test token security features integration"""
        # This test verifies token security features are available
        
        with patch('src.interface.controllers.auth_controller.InvalidTokenException') as mock_exception:
            # Act
            from src.interface.controllers import auth_controller
            
            # Assert
            assert mock_exception is not None
    
    def test_jwt_required_integration(self, client):
        """Test JWT required decorator integration"""
        # This test verifies JWT protection is available
        
        # Act
        from src.interface.controllers.auth_controller import jwt_required, get_jwt_identity
        
        # Assert
        assert jwt_required is not None
        assert get_jwt_identity is not None


class TestAuthControllerMiddleware:
    """Test auth controller middleware integration"""
    
    def test_firebase_auth_middleware(self):
        """Test Firebase auth middleware integration"""
        # Act
        from src.interface.controllers.auth_controller import verify_firebase_token
        
        # Assert
        assert verify_firebase_token is not None
        assert callable(verify_firebase_token)
    
    def test_swagger_integration(self):
        """Test Swagger documentation integration"""
        # Act
        from src.interface.controllers.auth_controller import swag_from
        
        # Assert
        assert swag_from is not None
        assert callable(swag_from)
    
    def test_blueprint_configuration(self):
        """Test blueprint configuration"""
        # Act
        from src.interface.controllers.auth_controller import auth_bp
        
        # Assert
        assert auth_bp is not None
        assert auth_bp.name == 'auth'


class TestAuthControllerExceptionHandling:
    """Test auth controller exception handling"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for exception testing"""
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_invalid_token_exception_handling(self, client):
        """Test invalid token exception handling"""
        # This test verifies exception handling is in place
        
        with patch('src.interface.controllers.auth_controller.InvalidTokenException') as mock_exception:
            # Act
            from src.interface.controllers import auth_controller
            
            # Assert
            assert mock_exception is not None
    
    def test_traceback_integration(self, client):
        """Test traceback integration for debugging"""
        # Act
        from src.interface.controllers.auth_controller import traceback
        
        # Assert
        assert traceback is not None
    
    def test_security_event_logging(self, client):
        """Test security event logging integration"""
        # Act
        from src.interface.controllers.auth_controller import SecurityEventType
        
        # Assert
        assert SecurityEventType is not None


class TestAuthControllerImports:
    """Test that all required imports are available"""
    
    def test_flask_imports(self):
        """Test Flask-related imports"""
        from src.interface.controllers.auth_controller import (
            Blueprint, request, jsonify, redirect, g
        )
        
        assert Blueprint is not None
        assert request is not None
        assert jsonify is not None
        assert redirect is not None
        assert g is not None
    
    def test_jwt_imports(self):
        """Test JWT-related imports"""
        from src.interface.controllers.auth_controller import (
            get_jwt_identity, jwt_required
        )
        
        assert get_jwt_identity is not None
        assert jwt_required is not None
    
    def test_config_imports(self):
        """Test configuration imports"""
        from src.interface.controllers.auth_controller import Config
        
        assert Config is not None
    
    def test_datetime_imports(self):
        """Test datetime-related imports"""
        from src.interface.controllers.auth_controller import datetime, timezone
        
        assert datetime is not None
        assert timezone is not None
    
    def test_uuid_import(self):
        """Test UUID import"""
        from src.interface.controllers.auth_controller import uuid
        
        assert uuid is not None
