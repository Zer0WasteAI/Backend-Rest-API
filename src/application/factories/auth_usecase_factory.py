from src.application.use_cases.auth.logout_usecase import LogoutUseCase
from src.application.use_cases.auth.refresh_token_usecase import RefreshTokenUseCase
# Removed SendSMSOtpUseCase and VerifySMSOtpUseCase imports

from src.infrastructure.db.user_repository import UserRepository
from src.infrastructure.db.auth_repository import AuthRepository
from src.infrastructure.db.profile_repository import ProfileRepository
from src.infrastructure.firebase.firestore_profile_service import FirestoreProfileService
from src.infrastructure.auth.jwt_service import JWTService
from src.infrastructure.db.token_security_repository import TokenSecurityRepository
# Removed SMTPEmailService import

# Factories for individual services/repositories
def make_user_repository():
    return UserRepository()

def make_auth_repository():
    return AuthRepository()

def make_profile_repository():
    return ProfileRepository()

def make_firestore_profile_service():
    return FirestoreProfileService()

def make_jwt_service():
    return JWTService()

def make_token_security_repository():
    return TokenSecurityRepository()

# Factories for use cases
def make_logout_use_case():
    return LogoutUseCase(
        jwt_service=make_jwt_service(),
        token_security_repo=make_token_security_repository()
    )

def make_refresh_token_use_case():
    return RefreshTokenUseCase(
        jwt_service=make_jwt_service(),
        token_security_repo=make_token_security_repository()
    )
