from twilio.rest import Client
from src.config.config import Config
from src.domain.services.sms_service import SMSService
from src.shared.exceptions.custom import SMSDeliveryException

class TwilioSMSService(SMSService):
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)

    def send_otp(self, phone: str, code: str):
        try:
            message = self.client.messages.create(
                body=f"Tu código OTP es: {code}",
                from_=Config.TWILIO_PHONE_NUMBER,
                to=phone
            )
            return message.sid
        except Exception as e:
            raise SMSDeliveryException(f"No se pudo enviar el SMS: {str(e)}")
