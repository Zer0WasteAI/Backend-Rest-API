from src.application.use_cases.auth.logout_usecase import LogoutUseCase
from src.application.use_cases.auth.refresh_token_usecase import RefreshTokenUseCase
# Removed SendSMSOtpUseCase and VerifySMSOtpUseCase imports

from src.infrastructure.db.user_repository import UserRepository
from src.infrastructure.db.auth_repository import AuthRepository
from src.infrastructure.db.profile_repository import ProfileRepository
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

def make_jwt_service():
    return JWTService()

def make_token_security_repository():
    return TokenSecurityRepository()

# Use case factories
def make_logout_use_case():
    return LogoutUseCase(make_auth_repository(), make_jwt_service())

def make_refresh_token_use_case():
    return RefreshTokenUseCase(make_jwt_service())
