from src.application.use_cases.auth.logout_usecase import LogoutUseCase
from src.application.use_cases.auth.refresh_token_usecase import RefreshTokenUseCase
from src.application.use_cases.auth.register_user_usecase import RegisterUserUseCase
from src.application.use_cases.auth.login_email_usecase import LoginEmailUseCase
from src.application.use_cases.auth.change_password_usecase import ChangePasswordUseCase
from src.application.use_cases.auth.send_email_reset_code_usecase import SendEmailResetCodeUseCase
from src.application.use_cases.auth.send_sms_otp_usecase import SendSMSOtpUseCase
from src.application.use_cases.auth.verify_email_reset_code_usecase import VerifyEmailResetCodeUseCase
from src.application.use_cases.auth.verify_sms_otp_usecase import VerifySMSOtpUseCase
from src.application.use_cases.auth.login_google_usecase import LoginGoogleUseCase
from src.application.use_cases.auth.login_facebook_usecase import LoginFacebookUseCase
from src.application.use_cases.auth.login_apple_usecase import LoginAppleUseCase

from src.infrastructure.db.user_repository import UserRepository
from src.infrastructure.db.auth_repository import AuthRepository
from src.infrastructure.db.profile_repository import ProfileRepository
from src.infrastructure.auth.jwt_service import JWTService
from src.infrastructure.email.smtp_email_service import SMTPEmailService
from src.infrastructure.sms.twilio_sms_service import TwilioSMSService
from src.infrastructure.oauth.google_oauth_service import GoogleOAuthService
from src.infrastructure.oauth.facebook_oauth_service import FacebookOAuthService
from src.infrastructure.oauth.apple_oauth_service import AppleOAuthService


def make_register_user_use_case():
    return RegisterUserUseCase(UserRepository(), AuthRepository(), ProfileRepository(), JWTService())

def make_login_email_use_case():
    return LoginEmailUseCase(UserRepository(), AuthRepository(), JWTService())

def make_change_password_use_case():
    return ChangePasswordUseCase(UserRepository(), AuthRepository())

def make_send_sms_otp_use_case():
    return SendSMSOtpUseCase(TwilioSMSService())

def make_verify_sms_otp_use_case():
    return VerifySMSOtpUseCase()

def make_login_google_use_case():
    return LoginGoogleUseCase(GoogleOAuthService(), JWTService(), UserRepository(), AuthRepository(), ProfileRepository())

def make_login_facebook_use_case():
    return LoginFacebookUseCase(FacebookOAuthService(), JWTService(), UserRepository(), AuthRepository(), ProfileRepository())

def make_login_apple_use_case():
    return LoginAppleUseCase(AppleOAuthService(), JWTService(), UserRepository(), AuthRepository(), ProfileRepository())

def make_logout_use_case():
    return LogoutUseCase(AuthRepository())

def make_refresh_token_use_case():
    return RefreshTokenUseCase(JWTService())

def make_send_email_reset_code_use_case():
    return SendEmailResetCodeUseCase(SMTPEmailService(), UserRepository())

def make_verify_email_reset_code_use_case():
    return VerifyEmailResetCodeUseCase()
