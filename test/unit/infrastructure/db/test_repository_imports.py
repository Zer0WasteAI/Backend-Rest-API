import importlib
import types


REPOSITORY_MODULES = [
    "src.infrastructure.db.profile_repository",
    "src.infrastructure.db.user_repository",
    "src.infrastructure.db.auth_repository",
    "src.infrastructure.db.recipe_generated_repository_impl",
    "src.infrastructure.db.token_security_repository",
]


def test_repository_modules_import():
    for module_path in REPOSITORY_MODULES:
        mod = importlib.import_module(module_path)
        assert isinstance(mod, types.ModuleType)

