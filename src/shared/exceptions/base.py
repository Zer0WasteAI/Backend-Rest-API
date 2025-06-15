class AppException(Exception):
    """
    Exception base class for the application.
    """

    def __init__(self, message="Error processing request", status_code=500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {"error": self.message}
