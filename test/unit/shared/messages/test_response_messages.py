from src.shared.messages.response_messages import (
    ResponseMessages,
    APIResponse,
    ServiceType,
    MessageType,
)


def test_get_message_specific_and_generic():
    # Specific auth+login success
    msg = ResponseMessages.get_message(ServiceType.AUTH, MessageType.SUCCESS, "login")
    assert "Bienvenido" in msg or "exitos" in msg

    # Generic fallback for unknown action
    generic = ResponseMessages.get_message(ServiceType.AUTH, MessageType.SUCCESS, "unknown_action")
    assert "Operación" in generic or "completada" in generic


def test_api_response_success_and_error_shapes():
    data, status = APIResponse.success(ServiceType.USER, action="update", data={"a": 1})
    assert status == 200
    assert data["success"] is True
    assert data["service"] == ServiceType.USER.value
    assert data["action"] == "update"
    assert data["data"] == {"a": 1}

    err, err_status = APIResponse.error(ServiceType.RECIPES, action="save", error_details="boom")
    assert err_status == 400
    assert err["success"] is False
    assert err["service"] == ServiceType.RECIPES.value
    assert err["action"] == "save"
    assert err["error_details"] == "boom"


def test_api_response_unauthorized_and_not_found():
    unauth, code = APIResponse.unauthorized(ServiceType.AUTH, action="access")
    assert code == 401
    assert unauth["success"] is False
    assert unauth["error_type"] == "unauthorized"

    nf, nf_code = APIResponse.not_found(ServiceType.IMAGES, resource="file")
    assert nf_code == 404
    assert nf["success"] is False
    assert nf["error_type"] == "not_found"
    assert nf["resource"] == "file"

