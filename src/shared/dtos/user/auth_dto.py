class LoginRequestDTO:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password

class LoginResponseDTO:
    def __init__(self, access_token: str, refresh_token: str, token_type: str = "Bearer"):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_type = token_type

class OAuthLoginDTO:
    def __init__(self, code: str):
        self.code = code