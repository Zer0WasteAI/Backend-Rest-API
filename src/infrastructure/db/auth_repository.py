from src.infrastructure.db.schemas.user_schema import User
from src.infrastructure.db.schemas.auth_user_schema import AuthUser, db

class AuthRepository:
    def create(self, data: dict):
        auth_user = AuthUser(
            uid=data["uid"],
            auth_provider=data["auth_provider"],
            is_verified=data.get("is_verified", False),
            is_active=data.get("is_active", True)
        )
        db.session.add(auth_user)
        db.session.commit()
        return auth_user

    def find_by_uid(self, uid: str):
        return AuthUser.query.filter_by(uid=uid).first()

    def find_by_uid_and_provider(self, uid: str, provider: str):
        return AuthUser.query.filter_by(uid=uid, auth_provider=provider).first()

    def find_by_email(self, email: str):
        return db.session.query(AuthUser).join(User).filter(User.email == email).first()

    def update(self, uid: str, provider: str, data: dict):
        auth_user = AuthUser.query.filter_by(uid=uid, auth_provider=provider).first()
        if auth_user:
            for key, value in data.items():
                if hasattr(auth_user, key):
                    setattr(auth_user, key, value)
            db.session.commit()
            return auth_user
        return None
