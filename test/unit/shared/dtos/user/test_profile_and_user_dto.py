from src.shared.dtos.user.profile_dto import UpdateProfileDTO, ProfileResponseDTO
from src.shared.dtos.user.user_dto import RegisterUserDTO, UserResponseDTO


def test_profile_dtos():
    upd = UpdateProfileDTO(name="Alice", phone="123", photo_url="u", prefs=["a"])
    assert upd.name == "Alice" and upd.phone == "123" and upd.photo_url == "u" and upd.prefs == ["a"]

    resp = ProfileResponseDTO(uid="u1", name="Alice", phone="123")
    assert resp.uid == "u1" and resp.name == "Alice" and resp.phone == "123"


def test_user_dtos():
    reg = RegisterUserDTO(email="e@x", password="p", name="n", phone="1")
    assert reg.email == "e@x" and reg.password == "p" and reg.name == "n" and reg.phone == "1"

    out = UserResponseDTO(uid="u1", email="e@x")
    assert out.uid == "u1" and out.email == "e@x"

