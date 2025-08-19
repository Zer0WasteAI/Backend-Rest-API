from flask import Flask

from src.shared.decorators.response_handler import api_response
from src.shared.messages.response_messages import ServiceType
from src.shared.exceptions.custom import InvalidRequestDataException


def test_api_response_success_default_status(app: Flask, client):
    @api_response(ServiceType.RECIPES, action="generate")
    def _ok():
        return {"result": "done"}

    app.add_url_rule("/_resp_success", "_resp_success", _ok, methods=["GET"])

    resp = client.get("/_resp_success")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["service"] == ServiceType.RECIPES.value
    assert data["action"] == "generate"
    assert data["data"] == {"result": "done"}


def test_api_response_tuple_status_passthrough(app: Flask, client):
    @api_response(ServiceType.AUTH, action="login")
    def _created():
        return {"created": True}, 201

    app.add_url_rule("/_resp_tuple", "_resp_tuple", _created, methods=["GET"])

    resp = client.get("/_resp_tuple")
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["success"] is True
    assert data["service"] == ServiceType.AUTH.value
    assert data["action"] == "login"
    assert data["data"] == {"created": True}


def test_api_response_invalid_request_exception(app: Flask, client):
    @api_response(ServiceType.RECIPES, action="generate")
    def _invalid():
        raise InvalidRequestDataException("bad payload")

    app.add_url_rule("/_resp_invalid", "_resp_invalid", _invalid, methods=["GET"])

    resp = client.get("/_resp_invalid")
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "bad payload" in data.get("error_details", "")


def test_api_response_value_error(app: Flask, client):
    @api_response(ServiceType.USER, action="update")
    def _value_err():
        raise ValueError("invalid value")

    app.add_url_rule("/_resp_valueerror", "_resp_valueerror", _value_err, methods=["GET"])

    resp = client.get("/_resp_valueerror")
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False


def test_api_response_generic_exception(app: Flask, client):
    @api_response(ServiceType.USER, action="get")
    def _boom():
        raise RuntimeError("unexpected")

    app.add_url_rule("/_resp_exception", "_resp_exception", _boom, methods=["GET"])

    resp = client.get("/_resp_exception")
    assert resp.status_code == 500
    data = resp.get_json()
    assert data["success"] is False

