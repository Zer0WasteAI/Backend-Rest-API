import pytest
from flask import Flask
from flask_jwt_extended import JWTManager
from unittest.mock import patch


def test_configure_jwt_callbacks_registers_blocklist_loader():
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'test'
    jwt = JWTManager(app)

    with app.app_context():
        with patch('src.infrastructure.auth.jwt_callbacks.TokenSecurityRepository') as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.is_token_blacklisted.return_value = True

            from src.infrastructure.auth.jwt_callbacks import configure_jwt_callbacks
            configure_jwt_callbacks(jwt)

            # Access internal callback and invoke
            cb = getattr(jwt, '_token_in_blocklist_callback', None)
            assert cb is not None
            assert cb({}, {'jti': 'abc'}) is True

