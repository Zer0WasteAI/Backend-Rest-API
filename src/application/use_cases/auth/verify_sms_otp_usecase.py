from src.shared.exceptions.custom import InvalidOTPException
from src.application.use_cases.auth.send_sms_otp_usecase import sms_otp_store

class VerifySMSOtpUseCase:
    @staticmethod
    def execute(phone: str, code: str):
        expected = sms_otp_store.get(phone)

        if not expected or expected != code:
            raise InvalidOTPException("Código inválido o expirado")

        del sms_otp_store[phone]

        return {"message": "OTP verificado correctamente"}
