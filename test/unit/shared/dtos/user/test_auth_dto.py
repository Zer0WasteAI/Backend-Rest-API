from src.shared.dtos.user.auth_dto import (
    LoginRequestDTO,
    LoginResponseDTO,
    OAuthLoginDTO,
)


def test_login_request_dto():
    dto = LoginRequestDTO(email="e@x.com", password="pw")
    assert dto.email == "e@x.com"
    assert dto.password == "pw"


def test_login_response_dto_defaults():
    dto = LoginResponseDTO(access_token="a", refresh_token="r")
    assert dto.access_token == "a"
    assert dto.refresh_token == "r"
    assert dto.token_type == "Bearer"


def test_oauth_login_dto():
    dto = OAuthLoginDTO(code="xyz")
    assert dto.code == "xyz"

