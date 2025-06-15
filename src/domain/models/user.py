class User:
    def __init__(self, uid: str, email: str, crated_at = None, updated_at = None):
        self.uid = uid
        self.email = email
        self.created_at = crated_at
        self.updated_at = updated_at

    def __repr__(self):
        return f"User(uid={self.uid}, email={self.email}, created_at={self.created_at}, updated_at={self.updated_at})"