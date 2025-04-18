import uuid
import bcrypt
from datetime import datetime, timezone
from src.shared.exceptions.custom import EmailAlreadyExistsException

class RegisterUserUseCase:
    def __init__(self, user_repository, auth_repository, profile_repository, auth_service):
        self.user_repository = user_repository
        self.auth_repository = auth_repository
        self.profile_repository = profile_repository
        self.auth_service = auth_service

    def execute(self, dto):
        if self.user_repository.exists_by_email(dto.email):
            raise EmailAlreadyExistsException()

        uid = str(uuid.uuid4())
        hashed_password = bcrypt.hashpw(dto.password.encode('utf-8'), bcrypt.gensalt()).decode()

        self.user_repository.create({
            "uid": uid,
            "email": dto.email,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })

        self.auth_repository.create({
            "uid": uid,
            "password_hash": hashed_password,
            "auth_provider": "email",
            "is_verified": False,
            "is_active": True
        })

        self.profile_repository.create({
            "uid": uid,
            "name": dto.name,
            "phone": dto.phone,
            "photo_url": "",
            "prefs": []
        })

        return self.auth_service.create_tokens(identity=uid)