from src.shared.exceptions.custom import InvalidOTPException
from src.application.use_cases.auth.send_email_reset_code_usecase import email_reset_code_store

email_verified_for_reset = {}

class VerifyEmailResetCodeUseCase:
    @staticmethod
    def execute(email: str, code: str):
        expected = email_reset_code_store.get(email)

        if not expected or expected != code:
            raise InvalidOTPException("Código inválido o expirado")

        email_verified_for_reset[email] = True
        del email_reset_code_store[email]
        return {"message": "Código verificado correctamente"}
