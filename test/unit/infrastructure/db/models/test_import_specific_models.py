import importlib
import types


MODEL_MODULES = [
    "src.infrastructure.db.models.async_task_orm",
    "src.infrastructure.db.models.consumption_log_orm",
    "src.infrastructure.db.models.cooking_session_orm",
    "src.infrastructure.db.models.daily_meal_plan_orm",
    "src.infrastructure.db.models.environmental_savings_orm",
    "src.infrastructure.db.models.food_item_orm",
    "src.infrastructure.db.models.generation_orm",
    "src.infrastructure.db.models.ingredient_orm",
    "src.infrastructure.db.models.ingredient_stack_orm",
    "src.infrastructure.db.models.inventory_orm",
    "src.infrastructure.db.models.leftover_orm",
    "src.infrastructure.db.models.recipe_ingredient_orm",
    "src.infrastructure.db.models.recipe_orm",
    "src.infrastructure.db.models.recipe_step_orm",
    "src.infrastructure.db.models.recognition_orm",
    "src.infrastructure.db.models.user_favorite_recipes",
    "src.infrastructure.db.models.waste_log_orm",
]


def test_specific_model_modules_import():
    for module_path in MODEL_MODULES:
        mod = importlib.import_module(module_path)
        assert isinstance(mod, types.ModuleType)

