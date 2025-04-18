class RefreshTokenUseCase:
    def __init__(self, auth_service):
        self.auth_service = auth_service

    def execute(self, identity: str) -> dict:
        return self.auth_service.create_tokens(identity=identity)