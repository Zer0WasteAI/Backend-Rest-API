class LoginOAuthUseCase:
    def __init__(self, oauth_service, auth_service):
        self.oauth_service = oauth_service
        self.auth_service = auth_service

    def execute(self, code: str) -> dict:
        user_info = self.oauth_service.get_user_info(code)
        return self.auth_service.create_tokens(identity=user_info["uid"])