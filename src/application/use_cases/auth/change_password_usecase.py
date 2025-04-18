import bcrypt
from src.shared.exceptions.custom import UserNotFoundException, InvalidOTPException
from src.application.use_cases.auth.verify_email_reset_code_usecase import email_verified_for_reset

class ChangePasswordUseCase:
    def __init__(self, user_repository, auth_repository):
        self.user_repository = user_repository
        self.auth_repository = auth_repository

    def execute(self, email: str, new_password: str):
        if email not in email_verified_for_reset:
            raise InvalidOTPException("Verificación requerida para cambiar contraseña")

        user = self.user_repository.find_by_email(email)
        if not user:
            raise UserNotFoundException("Usuario no encontrado")

        auth_user = self.auth_repository.find_by_uid(user.uid)
        hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        auth_user.password_hash = hashed_password
        self.auth_repository.update(auth_user)

        del email_verified_for_reset[email]

        return {"message": "Contraseña actualizada exitosamente"}
