import requests

from src.config.config import Config
from src.domain.services.oauth_service import OAuthService
from src.shared.exceptions.custom import UnauthorizedAccessException


class FacebookOAuthService(OAuthService):
    def get_user_info(self, code: str) -> dict:

        try:
            redirect_uri = Config.FACEBOOK_REDIRECT_URI
            token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
            token_payload = {
                "client_id": Config.FACEBOOK_CLIENT_ID,
                "client_secret": Config.FACEBOOK_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "code": code,
            }

            token_response = requests.get(token_url, params=token_payload)
            token_response.raise_for_status()
            access_token = token_response.json()["access_token"]

            user_info_url = "https://graph.facebook.com/me"
            user_info_params = {
                "fields": "id,name,email,picture",
                "access_token": access_token,
            }

            user_info_response = requests.get(user_info_url, params=user_info_params)
            user_info_response.raise_for_status()
            user = user_info_response.json()

            return {
                "email": user.get("email", f"{user['id']}@facebook.com"),
                "name": user.get("name"),
                "picture": f"https://graph.facebook.com/{user['id']}/picture?type=large"
            }

        except Exception as e:
            raise UnauthorizedAccessException(f"Error en login con Facebook: {str(e)}")