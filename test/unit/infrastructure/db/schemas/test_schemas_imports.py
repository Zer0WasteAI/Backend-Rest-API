import importlib
import types


SCHEMA_MODULES = [
    "src.infrastructure.db.schemas.auth_user_schema",
    "src.infrastructure.db.schemas.profile_user_schema",
    "src.infrastructure.db.schemas.token_blacklist_schema",
    "src.infrastructure.db.schemas.user_schema",
]


def test_schema_modules_import():
    for module_path in SCHEMA_MODULES:
        mod = importlib.import_module(module_path)
        assert isinstance(mod, types.ModuleType)

