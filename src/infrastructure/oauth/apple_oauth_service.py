import time
from pathlib import Path

import jwt
import requests

from src.config.config import Config
from src.domain.services.oauth_service import OAuthService
from src.shared.exceptions.custom import UnauthorizedAccessException


def _generate_client_secret() -> str:
    headers = {
        "alg": "ES256",
        "kid": Config.APPLE_KEY_ID,
    }

    payload = {
        "iss": Config.APPLE_CLIENT_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400 * 180,
        "aud": "https://appleid.apple.com",
        "sub": Config.APPLE_CLIENT_ID,
    }

    private_key_path = Path(Config.APPLE_PRIVATE_KEY_PATH)
    private_key = private_key_path.read_text()

    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)


class AppleOAuthService(OAuthService):
    def get_user_info(self, code: str) -> dict:
        try:
            redirect_uri = Config.APPLE_REDIRECT_URI
            client_secret = _generate_client_secret()

            token_url = "https://appleid.apple.com/auth/token"
            data = {
                "client_id": Config.APPLE_CLIENT_ID,
                "client_secret": client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }

            response = requests.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            id_token = token_data.get("id_token")

            decoded = jwt.decode(id_token, options={"verify_signature": False})
            return {
                "email": decoded.get("email"),
                "first_name": decoded.get("given_name"),
                "last_name": decoded.get("family_name"),
                "id": decoded.get("sub"),
                "picture": ""
            }
        except Exception as e:
            raise UnauthorizedAccessException(f"Error en login con Apple: {str(e)}")
