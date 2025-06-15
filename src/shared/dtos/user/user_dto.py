class RegisterUserDTO:
    def __init__(self, email: str, password: str, name: str, phone: str):
        self.email = email
        self.password = password
        self.name = name
        self.phone = phone

class UserResponseDTO:
    def __init__(self, uid: str, email: str, created_at=None, updated_at=None):
        self.uid = uid
        self.email = email
        self.created_at = created_at
        self.updated_at = updated_at
