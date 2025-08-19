import importlib
import types


FACTORY_MODULES = [
    "src.application.factories.food_image_generator_factory",
    "src.application.factories.generation_usecase_factory",
    "src.application.factories.image_management_usecase_factory",
    "src.application.factories.ingredient_image_generator_factory",
    "src.application.factories.inventory_image_upload_factory",
    "src.application.factories.inventory_usecase_factory",
    "src.application.factories.planning_usecase_factory",
    "src.application.factories.recognition_usecase_factory",
    "src.application.factories.unified_upload_factory",
]


def test_factory_modules_import_and_expose_makers():
    for module_path in FACTORY_MODULES:
        mod = importlib.import_module(module_path)
        assert isinstance(mod, types.ModuleType)
        makers = [getattr(mod, name) for name in dir(mod) if name.startswith("make_")]
        assert makers, f"No maker functions found in {module_path}"

