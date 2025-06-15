from abc import ABC, abstractmethod

class SMSService(ABC):
    @abstractmethod
    def send_otp(self, phone: str, code: str):
        """
        Envia un código OTP al número de teléfono proporcionado.

        :param phone: Número de teléfono al que se enviará el SMS.
        :param code: Codigo OTP a enviar.
        :raises SMSDeliveryException: Si ocurre un error al enviar el SMS.
        """
        pass