import bcrypt
from src.shared.exceptions.custom import UserNotFoundException, InvalidOTPException

class LoginEmailUseCase:
    def __init__(self, user_repository, auth_repository, auth_service):
        self.user_repository = user_repository
        self.auth_repository = auth_repository
        self.auth_service = auth_service

    def execute(self, email: str, password: str):
        user = self.user_repository.find_by_email(email)
        if not user:
            raise UserNotFoundException("Usuario no encontrado")

        auth_user = self.auth_repository.find_by_uid(user.uid)
        if not bcrypt.checkpw(password.encode(), auth_user.password_hash.encode('utf-8')):
            raise InvalidOTPException("Contraseña incorrecta")

        return self.auth_service.create_tokens(identity=user.uid)