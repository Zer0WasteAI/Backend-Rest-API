from .base import AppException

class InvalidTokenException(AppException):
    def __init__(self, message="Token invalid or expired"):
        super().__init__(message, status_code=401)

class UnauthorizedAccessException(AppException):
    def __init__(self, message="Access not authorized"):
        super().__init__(message, status_code=403)

class OTPExpiredException(AppException):
    def __init__(self, message="Code OTP expired"):
        super().__init__(message, status_code=401)

class InvalidOTPException(AppException):
    def __init__(self, message="Code OTP invalid"):
        super().__init__(message, status_code=400)

class EmailSendFailureException(AppException):
    def __init__(self, message="Error sending email"):
        super().__init__(message, status_code=500)

class UserNotFoundException(AppException):
    def __init__(self, message="User not found"):
        super().__init__(message, status_code=404)

class EmailAlreadyExistsException(AppException):
    def __init__(self, message="Email already exists"):
        super().__init__(message, status_code=409)

class SMSDeliveryException(AppException):
    def __init__(self, message="Error sending SMS"):
        super().__init__(message, status_code=500)

class UnidentifiedImageException(AppException):
    def __init__(self, message="Unidentified image"):
        super().__init__(message, status_code=400)

class InvalidResponseFormatException(AppException):
    def __init__(self, message="Error parsing response from external service"):
        super().__init__(message, status_code=502)

class InvalidRequestDataException(AppException):
    def __init__(self, message="Invalid request data", details=None):
        super().__init__(message=message, status_code=400)
        self.details = details

    def to_dict(self):
        error_response = super().to_dict()
        if self.details:
            error_response["details"] = self.details
        return error_response
