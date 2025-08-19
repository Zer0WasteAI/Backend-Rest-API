import importlib
import types


USE_CASE_MODULES = [
    "src.application.use_cases.image_management.find_image_by_name_use_case",
    "src.application.use_cases.image_management.unified_upload_use_case",
    "src.application.use_cases.inventory.base_inventory_use_case",
    "src.application.use_cases.inventory.create_leftover_use_case",
]


def test_use_case_modules_import():
    for module_path in USE_CASE_MODULES:
        mod = importlib.import_module(module_path)
        assert isinstance(mod, types.ModuleType)

