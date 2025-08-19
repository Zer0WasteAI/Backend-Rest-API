import importlib
import types


DOMAIN_MODULES = [
    "src.domain.models.auth_user",
    "src.domain.models.profile_user",
    "src.domain.value_objects.upload_request",
    "src.domain.repositories.base_repository",
]


def test_domain_modules_import():
    for module_path in DOMAIN_MODULES:
        mod = importlib.import_module(module_path)
        assert isinstance(mod, types.ModuleType)

