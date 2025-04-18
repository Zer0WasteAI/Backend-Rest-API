import random
from src.domain.services.email_service import EmailService
from src.shared.exceptions.custom import UserNotFoundException
from src.infrastructure.db.user_repository import UserRepository

email_reset_code_store = {}


def generate_otp():
    return str(random.randint(100000, 999999))


class SendEmailResetCodeUseCase:
    def __init__(self, email_service: EmailService, user_repository: UserRepository):
        self.email_service = email_service
        self.user_repository = user_repository

    def execute(self, email: str):
        user = self.user_repository.find_by_email(email)
        if not user:
            raise UserNotFoundException("Usuario no encontrado")

        code = generate_otp()
        email_reset_code_store[email] = code
        self.email_service.send_otp(email, code)
        return {"message": "Código enviado al correo"}
