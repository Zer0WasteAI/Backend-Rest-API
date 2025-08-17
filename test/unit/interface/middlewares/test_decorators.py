import pytest
from flask import Flask, jsonify
from unittest.mock import patch


def test_internal_only_decorator_allows_with_secret():
    app = Flask(__name__)
    app.config['INTERNAL_SECRET_KEY'] = 'secret'
    from src.shared.decorators.internal_only import internal_only

    @app.route('/internal')
    @internal_only
    def internal():
        return jsonify({"ok": True}), 200

    client = app.test_client()
    resp_forbidden = client.get('/internal')
    assert resp_forbidden.status_code == 403
    resp_ok = client.get('/internal', headers={'X-Internal-Secret': 'secret'})
    assert resp_ok.status_code == 200


def test_verify_firebase_token_decorator_paths():
    app = Flask(__name__)
    from src.interface.middlewares.firebase_auth_decorator import verify_firebase_token

    @app.route('/fb')
    @verify_firebase_token
    def fb():
        return jsonify({"ok": True}), 200

    client = app.test_client()
    # Missing header -> 401
    r = client.get('/fb')
    assert r.status_code == 401

    # Invalid header -> 401
    r = client.get('/fb', headers={'Authorization': 'Bearer '})
    assert r.status_code == 401

    # Success path: mock firebase_admin and its verify_id_token
    with patch('src.interface.middlewares.firebase_auth_decorator.firebase_admin') as fb_admin, \
         patch('src.interface.middlewares.firebase_auth_decorator.credentials') as creds, \
         patch('src.interface.middlewares.firebase_auth_decorator.Path') as path:
        fb_admin._apps = {'x': object()}  # simulate already initialized
        fb_admin.auth.verify_id_token.return_value = {'uid': 'u1', 'email_verified': True, 'firebase': {'sign_in_provider': 'password'}}
        r2 = client.get('/fb', headers={'Authorization': 'Bearer token'})
        assert r2.status_code in [200]

