class AuthUser:
    def __init__(self, uid: str, password_hash: str, provider: str, is_verified: bool, is_active: bool, jwt_token=None):
        self.uid = uid
        self.password_hash = password_hash
        self.provider = provider
        self.is_verified = is_verified
        self.is_active = is_active
        self.jwt_token = jwt_token

    def __repr__(self):
        return f"AuthUser(uid={self.uid}, provider={self.provider}, is_verified={self.is_verified}, is_active={self.is_active})"