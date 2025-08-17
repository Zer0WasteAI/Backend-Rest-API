from flask import Flask


def test_add_security_headers_sets_common_headers():
    app = Flask(__name__)
    from src.infrastructure.security.security_headers import add_security_headers
    add_security_headers(app)

    @app.route('/ping')
    def ping():
        return 'ok', 200

    client = app.test_client()
    resp = client.get('/ping')
    # Check a subset of important headers
    assert resp.headers.get('X-Content-Type-Options') == 'nosniff'
    assert resp.headers.get('X-Frame-Options') == 'DENY'
    assert 'default-src' in resp.headers.get('Content-Security-Policy', '')
    assert resp.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
    assert 'geolocation' in resp.headers.get('Permissions-Policy', '')

