from abc import ABC, abstractmethod

class EmailService(ABC):
    @abstractmethod
    def send_otp(self, to: str, code: str):
        """
        Send an OTP code to the specified email address.

        :param to: The recipient's email address.
        :param code: The OTP code to send.
        """
        pass