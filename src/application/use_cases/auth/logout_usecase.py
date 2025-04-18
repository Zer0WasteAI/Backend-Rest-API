class LogoutUseCase:
    def __init__(self, auth_repository):
        self.auth_repository = auth_repository

    def execute(self, uid: str):
        self.auth_repository.update_jwt_token(uid, None)
        return {"message": "Sesión cerrada"}