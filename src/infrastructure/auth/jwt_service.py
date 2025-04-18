from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.domain.services.auth_service import AuthService
from src.shared.exceptions.custom import InvalidTokenException


class JWTService(AuthService):
    def create_tokens(self, identity: str) -> dict:
        return {
            "access_token": create_access_token(identity=identity),
            "refresh_token": create_refresh_token(identity=identity),
            "token_type": "Bearer",
        }

    def decode_token(self, token: str) -> dict:
        try:
            return decode_token(token)
        except Exception as e:
            raise InvalidTokenException() from e