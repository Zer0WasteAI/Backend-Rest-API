from marshmallow import ValidationError

from src.interface.serializers.reset_password_serializer import (
    SendPasswordResetCodeSchema,
    VerifyPasswordResetCodeSchema,
    ChangePasswordSchema,
)


def test_send_password_reset_code_schema_valid():
    data = {"email": "user@example.com"}
    loaded = SendPasswordResetCodeSchema().load(data)
    assert loaded["email"] == "user@example.com"


def test_send_password_reset_code_schema_invalid_email():
    data = {"email": "not-an-email"}
    try:
        SendPasswordResetCodeSchema().load(data)
        assert False, "Expected ValidationError"
    except ValidationError as e:
        assert "email" in e.messages


def test_verify_password_reset_code_schema_valid():
    data = {"email": "user@example.com", "code": "123456"}
    loaded = VerifyPasswordResetCodeSchema().load(data)
    assert loaded["code"] == "123456"


def test_verify_password_reset_code_schema_invalid_length():
    data = {"email": "user@example.com", "code": "123"}
    try:
        VerifyPasswordResetCodeSchema().load(data)
        assert False, "Expected ValidationError"
    except ValidationError as e:
        assert "code" in e.messages


def test_change_password_schema_valid():
    data = {"email": "user@example.com", "new_password": "123456"}
    loaded = ChangePasswordSchema().load(data)
    assert loaded["new_password"] == "123456"


def test_change_password_schema_too_short():
    data = {"email": "user@example.com", "new_password": "123"}
    try:
        ChangePasswordSchema().load(data)
        assert False, "Expected ValidationError"
    except ValidationError as e:
        assert "new_password" in e.messages

