import importlib
import types


SERVICE_MODULES = [
    "src.application.services.file_upload_service",
    "src.application.services.food_image_generator_service",
    "src.application.services.image_upload_validator",
    "src.application.services.ingredient_image_generator_service",
    "src.application.services.inventory_image_upload_service",
    "src.application.services.inventory_image_upload_validator",
    "src.application.services.recipe_image_generator_service",
]


def test_service_modules_import():
    for module_path in SERVICE_MODULES:
        mod = importlib.import_module(module_path)
        assert isinstance(mod, types.ModuleType)

