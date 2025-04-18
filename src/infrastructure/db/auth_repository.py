from src.infrastructure.db.schemas.user_schema import User
from src.infrastructure.db.schemas.auth_user_schema import AuthUser, db

class AuthRepository:
    def create(self, data: dict):
        auth_user = AuthUser(
            uid=data["uid"],
            password_hash=data["password_hash"],
            auth_provider=data["auth_provider"],
            is_verified=data.get("is_verified", False),
            is_active=data.get("is_active", True),
            jwt_token=data.get("jwt_token", None)
        )
        db.session.add(auth_user)
        db.session.commit()
        return auth_user

    def find_by_uid(self, uid: str):
        return AuthUser.query.filter_by(uid=uid).first()

    def find_by_email(self, email: str):
        return db.session.query(AuthUser).join(User).filter(User.email == email).first()

    def update_jwt_token(self, uid: str, new_token: str):
        auth_user = AuthUser.query.filter_by(uid=uid).first()
        if auth_user:
            auth_user.jwt_token = new_token
            db.session.commit()
            return auth_user
        return None

    def verify_password(self, uid: str, password_hash: str) -> bool:
        auth_user = AuthUser.query.filter_by(uid=uid).first()
        return auth_user and auth_user.password_hash == password_hash
