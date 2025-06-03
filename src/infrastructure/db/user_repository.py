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
    def update(uid: str, data: dict):
        user = User.query.filter_by(uid=uid).first()
        if user:
            for key, value in data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return user
        return None

    @staticmethod
    def update_email(uid: str, new_email: str):
        user = User.query.filter_by(uid=uid).first()
        if user:
            user.email = new_email
            user.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return user
        return None

    @staticmethod
    def update_uid(old_uid: str, new_uid: str):
        """
        Actualiza el UID de un usuario existente.
        Útil cuando Firebase asigna un nuevo UID al mismo usuario.
        """
        user = User.query.filter_by(uid=old_uid).first()
        if user:
            user.uid = new_uid
            user.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            return user
        return None

    @staticmethod
    def find_user_with_auth_by_email(email: str):
        return User.query.options(joinedload(User.auth)).filter_by(email=email).first()
