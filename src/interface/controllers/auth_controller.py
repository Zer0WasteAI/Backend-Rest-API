from flasgger import swag_from
from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import get_jwt_identity, jwt_required

from src.config.config import Config
from src.interface.serializers.register_serializer import RegisterUserSchema
from src.interface.serializers.login_serializer import LoginUserSchema
from src.interface.serializers.reset_password_serializer import SendPasswordResetCodeSchema, \
    VerifyPasswordResetCodeSchema
from src.interface.serializers.sms_otp_serializer import SendSMSOtpSchema, VerifySMSOtpSchema
from src.interface.serializers.oauth_serializer import OAuthCodeSchema
from src.interface.serializers.change_password_serializer import ChangePasswordSchema
from src.shared.dtos.user.user_dto import RegisterUserDTO


from src.application.factories.auth_usecase_factory import (
    make_register_user_use_case,
    make_login_email_use_case,
    make_change_password_use_case,
    make_send_sms_otp_use_case,
    make_verify_sms_otp_use_case,
    make_login_google_use_case,
    make_login_facebook_use_case,
    make_login_apple_use_case,
    make_logout_use_case,
    make_refresh_token_use_case,
    make_send_email_reset_code_use_case,
    make_verify_email_reset_code_use_case,
)

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
@swag_from({
    'tags': ['Auth'],
    'summary': 'Registro de usuario',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'properties': {
                    'email': {'type': 'string'},
                    'password': {'type': 'string'},
                    'name': {'type': 'string'},
                    'phone': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        201: {'description': 'Registro exitoso'},
        400: {'description': 'Error de validación'}
    }
})
def register():
    data = request.get_json()
    errors = RegisterUserSchema().validate(data)
    if errors:
        return jsonify(errors), 400

    dto = RegisterUserDTO(**data)
    use_case = make_register_user_use_case()
    result = use_case.execute(dto)
    return jsonify(result), 201

@auth_bp.route("/login", methods=["POST"])
@swag_from({
    'tags': ['Auth'],
    'summary': 'Inicio de sesión con email y contraseña',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'properties': {
                    'email': {'type': 'string'},
                    'password': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Login exitoso'},
        400: {'description': 'Error de validación'}
    }
})
def login():
    data = request.get_json()
    errors = LoginUserSchema().validate(data)
    if errors:
        return jsonify(errors), 400

    use_case = make_login_email_use_case()
    result = use_case.execute(data["email"], data["password"])
    return jsonify(result), 200

@auth_bp.route("/password/change", methods=["POST"])
@swag_from({
    'tags': ['Auth'],
    'summary': 'Cambiar contraseña (requiere verificación previa)',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'properties': {
                    'email': {'type': 'string'},
                    'new_password': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Contraseña actualizada'},
        400: {'description': 'Error de validación o verificación'}
    }
})
def change_password():
    data = request.get_json()
    errors = ChangePasswordSchema().validate(data)
    if errors:
        return jsonify(errors), 400

    use_case = make_change_password_use_case()
    result = use_case.execute(data["email"], data["new_password"])
    return jsonify(result), 200

@auth_bp.route("/sms/send", methods=["POST"])
def send_sms():
    data = request.get_json()
    errors = SendSMSOtpSchema().validate(data)
    if errors:
        return jsonify(errors), 400

    use_case = make_send_sms_otp_use_case()
    result = use_case.execute(data["phone"])
    return jsonify(result), 200

@auth_bp.route("/sms/verify", methods=["POST"])
def verify_sms():
    data = request.get_json()
    errors = VerifySMSOtpSchema().validate(data)
    if errors:
        return jsonify(errors), 400

    use_case = make_verify_sms_otp_use_case()
    result = use_case.execute(data["phone"], data["code"])
    return jsonify(result), 200

@auth_bp.route("/login/google", methods=["POST"])
@swag_from({
    'tags': ['Auth'],
    'summary': 'Inicio de sesión con Google',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'properties': {
                    'code': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Login exitoso con Google'},
        400: {'description': 'Código inválido'}
    }
})
def login_google():
    data = request.get_json()
    errors = OAuthCodeSchema().validate(data)
    if errors:
        return jsonify(errors), 400

    use_case = make_login_google_use_case()
    result = use_case.execute(data["code"])
    return jsonify(result), 200

@auth_bp.route("/login/facebook", methods=["POST"])
@swag_from({
    'tags': ['Auth'],
    'summary': 'Inicio de sesión con Facebook',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'properties': {
                    'code': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Login exitoso con Facebook'},
        400: {'description': 'Código inválido'}
    }
})
def login_facebook():
    data = request.get_json()
    errors = OAuthCodeSchema().validate(data)
    if errors:
        return jsonify(errors), 400

    use_case = make_login_facebook_use_case()
    result = use_case.execute(data["code"])
    return jsonify(result), 200

@auth_bp.route("/login/apple", methods=["POST"])
@swag_from({
    'tags': ['Auth'],
    'summary': 'Inicio de sesión con Apple',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'properties': {
                    'code': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Login exitoso con Apple'},
        400: {'description': 'Código inválido'}
    }
})
def login_apple():
    data = request.get_json()
    errors = OAuthCodeSchema().validate(data)
    if errors:
        return jsonify(errors), 400

    use_case = make_login_apple_use_case()
    result = use_case.execute(data["code"])
    return jsonify(result), 200

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
@swag_from({
    'tags': ['Auth'],
    'security': [{"Bearer": []}],
    'summary': 'Renovación de token JWT',
    'responses': {
        200: {'description': 'Nuevo token generado'}
    }
})
def refresh_token():
    current_user = get_jwt_identity()
    use_case = make_refresh_token_use_case()
    result = use_case.execute(identity=current_user)
    return jsonify(result), 200

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
@swag_from({
    'tags': ['Auth'],
    'summary': 'Cerrar sesión (logout)',
    'security': [{'Bearer': []}],
    'responses': {
        200: {'description': 'Sesión cerrada'}
    }
})
def logout():
    uid = get_jwt_identity()
    use_case = make_logout_use_case()
    result = use_case.execute(uid)
    return jsonify(result), 200

@auth_bp.route("/email/send-password-reset-code", methods=["POST"])
@swag_from({
    'tags': ['Auth'],
    'summary': 'Enviar OTP al correo para cambio de contraseña',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'properties': {
                    'email': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Código enviado'}
    }
})
def send_password_reset_code():
    data = request.get_json()
    errors = SendPasswordResetCodeSchema().validate(data)
    if errors:
        return jsonify(errors), 400

    use_case = make_send_email_reset_code_use_case()
    result = use_case.execute(data["email"])
    return jsonify(result), 200

@auth_bp.route("/email/verify-password-reset-code", methods=["POST"])
@swag_from({
    'tags': ['Auth'],
    'summary': 'Verificar OTP del correo',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'properties': {
                    'email': {'type': 'string'},
                    'code': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Código verificado'}
    }
})
def verify_password_reset_code():
    data = request.get_json()
    errors = VerifyPasswordResetCodeSchema().validate(data)
    if errors:
        return jsonify(errors), 400

    use_case = make_verify_email_reset_code_use_case()
    result = use_case.execute(data["email"], data["code"])
    return jsonify(result), 200

@auth_bp.route("/google/callback")
def google_callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No se recibió el código"}), 400

    use_case = make_login_google_use_case()
    result = use_case.execute(code)

    return jsonify(result), 200

@auth_bp.route("/facebook/callback")
def facebook_callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "No se recibió el código de Facebook"}), 400

    use_case = make_login_facebook_use_case()
    result = use_case.execute(code)

    return jsonify(result), 200


@auth_bp.route("/google/initiate")
def google_initiate():
    redirect_uri = Config.GOOGLE_REDIRECT_URI
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={Config.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return redirect(auth_url)

@auth_bp.route("/facebook/initiate")
def facebook_initiate():
    redirect_uri = Config.FACEBOOK_REDIRECT_URI
    auth_url = (
        "https://www.facebook.com/v18.0/dialog/oauth"
        f"?client_id={Config.FACEBOOK_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=email,public_profile"
        f"&response_type=code"
    )
    return redirect(auth_url)

@auth_bp.route("/apple/initiate")
def apple_initiate():
    redirect_uri = Config.APPLE_REDIRECT_URI
    auth_url = (
        "https://appleid.apple.com/auth/authorize"
        f"?client_id={Config.APPLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=name%20email"
        f"&response_mode=form_post"
    )
    return redirect(auth_url)

@auth_bp.route("/apple/callback", methods=["GET", "POST"])
def apple_callback():
    code = request.values.get("code")
    if not code:
        return jsonify({"error": "No se recibió el código de Apple"}), 400

    use_case = make_login_apple_use_case()
    result = use_case.execute(code)

    return jsonify(result), 200
