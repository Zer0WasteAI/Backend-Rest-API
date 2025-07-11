from src.infrastructure.db.schemas.profile_user_schema import ProfileUser, db
from src.infrastructure.db.schemas.user_schema import User
from sqlalchemy.orm import joinedload

class ProfileRepository:
    def create(self, data: dict):
        profile = ProfileUser(
            uid=data["uid"],
            name=data["name"],
            phone=data["phone"],
            photo_url=data.get("photo_url", ""),
            prefs=data.get("prefs", {})
        )
        db.session.add(profile)
        db.session.commit()
        return profile

    def find_by_uid(self, uid: str):
        return ProfileUser.query.filter_by(uid=uid).first()

    def update(self, uid: str, data: dict):
        profile = ProfileUser.query.filter_by(uid=uid).first()
        if profile:
            for key, value in data.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            db.session.commit()
            return profile
        return None

    def find_by_email(self, email: str):
        return db.session.query(ProfileUser)\
            .join(User, User.uid == ProfileUser.uid)\
            .filter(User.email == email)\
            .options(joinedload(ProfileUser.user))\
            .first()
