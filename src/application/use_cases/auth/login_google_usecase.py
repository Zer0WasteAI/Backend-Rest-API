import uuid
from datetime import datetime, timezone

class LoginGoogleUseCase:
    def __init__(self, oauth_service, auth_service, user_repository, auth_repository, profile_repository):
        self.oauth_service = oauth_service
        self.auth_service = auth_service
        self.user_repository = user_repository
        self.auth_repository = auth_repository
        self.profile_repository = profile_repository

    def execute(self, code: str) -> dict:
        user_info = self.oauth_service.get_user_info(code)
        email = user_info["email"]

        user = self.user_repository.find_by_email(email)
        if not user:
            uid = str(uuid.uuid4())

            self.user_repository.create({
                "uid": uid,
                "email": email,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })

            self.auth_repository.create({
                "uid": uid,
                "password_hash": "",
                "auth_provider": "google",
                "is_verified": True,
                "is_active": True
            })

            self.profile_repository.create({
                "uid": uid,
                "name": user_info.get("name", ""),
                "phone": "",
                "photo_url": user_info.get("picture", ""),
                "prefs": []
            })

            user = self.user_repository.find_by_email(user_info["email"])

        profile = self.profile_repository.find_by_uid(user.uid)
        tokens = self.auth_service.create_tokens(identity=user.uid)

        return {
            **tokens,
            "user": {
                "uid": user.uid,
                "email": user.email,
                "name": profile.name,
                "photo_url": profile.photo_url
            }
        }
