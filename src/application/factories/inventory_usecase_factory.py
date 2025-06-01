from src.application.use_cases.inventory.add_ingredients_to_inventory_use_case import AddIngredientsToInventoryUseCase
from src.application.use_cases.inventory.add_ingredients_and_foods_to_inventory_use_case import AddIngredientsAndFoodsToInventoryUseCase
from src.application.use_cases.inventory.delete_food_item_use_case import DeleteFoodItemUseCase
from src.application.use_cases.inventory.delete_ingredient_status_use_case import DeleteIngredientStackUseCase
from src.application.use_cases.inventory.get_expiring_soon_use_case import GetExpiringSoonUseCase
from src.application.use_cases.inventory.get_inventory_content_use_case import GetInventoryContentUseCase
from src.application.use_cases.inventory.update_food_item_use_case import UpdateFoodItemUseCase
from src.application.use_cases.inventory.update_ingredient_stack_use_case import UpdateIngredientStackUseCase

from src.infrastructure.db.inventory_repository_impl import InventoryRepositoryImpl
from src.infrastructure.inventory.inventory_calcularor_impl import InventoryCalculatorImpl

def make_add_food_items_to_inventory_use_case(db):
    return None #AddFoodItemsToInventoryUseCase(InventoryRepositoryImpl(db), InventoryCalculatorImpl)
def make_add_ingredients_and_foods_to_inventory_use_case(db):
    return AddIngredientsAndFoodsToInventoryUseCase(InventoryRepositoryImpl(db), InventoryCalculatorImpl())
def make_add_ingredients_to_inventory_use_case(db):
    return AddIngredientsToInventoryUseCase(InventoryRepositoryImpl(db), InventoryCalculatorImpl())
def make_delete_food_item_use_case(db):
    return DeleteFoodItemUseCase(InventoryRepositoryImpl(db))
def make_delete_ingredient_stack_use_case(db):
    return DeleteIngredientStackUseCase(InventoryRepositoryImpl(db))
def make_get_expiring_soon_use_case(db):
    return GetExpiringSoonUseCase(InventoryRepositoryImpl(db))
def make_get_inventory_content_use_case(db):
    return GetInventoryContentUseCase(InventoryRepositoryImpl(db))
def make_update_food_item_use_case(db):
    return UpdateFoodItemUseCase(InventoryRepositoryImpl(db), InventoryCalculatorImpl())
def make_update_ingredient_stack_use_case(db):
    return UpdateIngredientStackUseCase(InventoryRepositoryImpl(db), InventoryCalculatorImpl())