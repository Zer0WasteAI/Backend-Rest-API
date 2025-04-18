import random

sms_otp_store = {}


def generate_otp():
    return str(random.randint(100000, 999999))


class SendSMSOtpUseCase:
    def __init__(self, sms_service):
        self.sms_service = sms_service

    def execute(self, phone: str):
        code = generate_otp()
        sms_otp_store[phone] = code
        self.sms_service.send_otp(phone, code)
        return {"message": "OTP enviado correctamente"}
