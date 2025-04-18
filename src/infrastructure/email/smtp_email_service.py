import smtplib
import ssl
from email.message import EmailMessage

from src.config.config import Config
from src.domain.services.email_service import EmailService
from src.shared.exceptions.custom import EmailSendFailureException


class SMTPEmailService(EmailService):
    def send_otp(self, to: str, code: str):
        subject = "Tu código de verificación"
        body = f"Tu código de verificación es: {code}"

        email = EmailMessage()
        email["From"] = Config.EMAIL_USER
        email["To"] = to
        email["Subject"] = subject
        email.set_content(body)

        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL(Config.EMAIL_HOST, Config.EMAIL_PORT, context=context) as smtp:
                smtp.login(Config.EMAIL_USER, Config.EMAIL_PASSWORD)
                smtp.send_message(email)
        except Exception as e:
            raise EmailSendFailureException(f"No se pudo enviar el correo: {str(e)}")