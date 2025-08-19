import os
import pytest
from flask import Flask

# Ensure testing environment is set before importing app
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("TESTING", "1")

from src.main import create_app
from src.infrastructure.db.base import db
from flask_jwt_extended import create_access_token


@pytest.fixture(scope="session")
def app() -> Flask:
    app = create_app()
    app.config.update({
        "TESTING": True,
        # Use in-memory SQLite for unit tests that may touch the DB layer
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        # JWT Configuration for testing
        "JWT_SECRET_KEY": "test-secret-key-global",
        "JWT_TOKEN_LOCATION": ["headers"],
        "JWT_HEADER_NAME": "Authorization", 
        "JWT_HEADER_TYPE": "Bearer",
        "JWT_ACCESS_TOKEN_EXPIRES": False,
        "WTF_CSRF_ENABLED": False
    })
    # Ensure all tables exist for unit tests that touch DB
    with app.app_context():
        db.create_all()
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_header(app):
    with app.app_context():
        token = create_access_token(identity="test-user-uid")
    return {"Authorization": f"Bearer {token}"}
