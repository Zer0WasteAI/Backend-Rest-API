import importlib
import types


def test_misc_infrastructure_imports():
    for module_path in [
        "src.infrastructure.inventory.inventory_calcularor_impl",
        "src.infrastructure.security.security_logger",
        "src.interface.middlewares.firebase_auth_decorator",
        "src.infrastructure.async_tasks.async_task_service",
    ]:
        mod = importlib.import_module(module_path)
        assert isinstance(mod, types.ModuleType)

