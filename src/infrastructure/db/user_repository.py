from sqlalchemy.orm import joinedload

from src.infrastructure.db.schemas.user_schema import User, db
from datetime import datetime, timezone

class UserRepository:
    @staticmethod
    def create(data: dict):
        user = User(
            uid=data["uid"],
            email=data["email"],
            created_at=data.get("created_at", datetime.now(timezone.utc)),
            updated_at=data.get("updated_at", datetime.now(timezone.utc))
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def find_by_email(email: str):
        print("🔍 Buscando email:", email)
        print("🧩 Tablas conocidas por SQLAlchemy:", db.metadata.tables.keys())
        return User.query.filter_by(email=email).first()

    @staticmethod
    def exists_by_email(email: str) -> bool:
        return User.query.filter_by(email=email).first() is not None

    @staticmethod
    def find_by_uid(uid: str):
        return User.query.filter_by(uid=uid).first()

    @staticmethod
    def update_email(uid: str, new_email: str):
        user = User.query.filter_by(uid=uid).first()
        if user:
            user.email = new_email

    @staticmethod
    def find_user_with_auth_by_email(email: str):
        return User.query.options(joinedload(User.auth)).filter_by(email=email).first()
