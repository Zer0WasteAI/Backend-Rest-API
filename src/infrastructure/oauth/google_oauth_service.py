import requests
from flask import url_for

from src.config.config import Config
from src.domain.services.oauth_service import OAuthService
from src.shared.exceptions.custom import UnauthorizedAccessException


class GoogleOAuthService(OAuthService):
    def get_user_info(self, code: str) -> dict:
        try:
            token_url = "https://oauth2.googleapis.com/token"

            redirect_uri = url_for('auth.google_callback', _external=True)

            token_payload = {
                "code": code,
                "client_id": Config.GOOGLE_CLIENT_ID,
                "client_secret": Config.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }

            token_response = requests.post(token_url, data=token_payload)
            token_response.raise_for_status()
            tokens = token_response.json()
            access_token = tokens.get("access_token")

            userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            userinfo_response = requests.get(userinfo_url, headers=headers)
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()

            return {
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
            }

        except Exception as e:
            raise UnauthorizedAccessException(f"Error en login con Google: {str(e)}")
