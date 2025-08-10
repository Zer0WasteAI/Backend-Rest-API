from flask import Flask
from contextlib import contextmanager

from src.infrastructure.optimization.rate_limiter import ZeroWasteRateLimiter


@contextmanager
def request_ctx(app: Flask):
    with app.test_request_context("/api/test"):
        yield


def test_rate_limit_key_uses_ip_when_no_jwt(monkeypatch):
    app = Flask(__name__)
    limiter = ZeroWasteRateLimiter()

    # Disable actual limiter init; only test key func behavior
    with request_ctx(app):
        # Force jwt functions to raise so it falls back to IP
        monkeypatch.setenv("FLASK_ENV", "testing")
        key = limiter._get_rate_limit_key()
        assert key.startswith("ip:")


def test_rate_limit_key_uses_user_uid_when_jwt(monkeypatch):
    app = Flask(__name__)
    limiter = ZeroWasteRateLimiter()

    # Monkeypatch JWT helpers used inside _get_rate_limit_key
    import src.infrastructure.optimization.rate_limiter as rl
    monkeypatch.setattr(rl, "verify_jwt_in_request", lambda optional=True: None)
    monkeypatch.setattr(rl, "get_jwt_identity", lambda: "user-uid-123")

    with request_ctx(app):
        key = limiter._get_rate_limit_key()
        assert key == "user:user-uid-123"

