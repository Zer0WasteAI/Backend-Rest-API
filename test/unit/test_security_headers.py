from flask import Flask

from src.infrastructure.security.security_headers import add_security_headers


def test_security_headers_added_to_response():
    app = Flask(__name__)
    add_security_headers(app)

    @app.route("/ping")
    def ping():
        return "ok", 200

    client = app.test_client()
    rv = client.get("/ping")
    headers = rv.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Content-Security-Policy" in headers
    assert headers.get("Strict-Transport-Security") is not None

