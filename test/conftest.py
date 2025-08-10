import os
import pytest
from flask import Flask

# Ensure testing environment is set before importing app
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("TESTING", "1")

from src.main import create_app


@pytest.fixture(scope="session")
def app() -> Flask:
    app = create_app()
    app.config.update({
        "TESTING": True,
        # Use in-memory SQLite for unit tests that may touch the DB layer
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    return app


@pytest.fixture()
def client(app):
    return app.test_client()

