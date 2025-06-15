from src.application.use_cases.inventory.add_ingredients_to_inventory_use_case import AddIngredientsToInventoryUseCase
from src.application.use_cases.inventory.add_ingredients_and_foods_to_inventory_use_case import AddIngredientsAndFoodsToInventoryUseCase
from src.application.use_cases.inventory.add_item_to_inventory_use_case import AddItemToInventoryUseCase
from src.application.use_cases.inventory.delete_food_item_use_case import DeleteFoodItemUseCase
from src.application.use_cases.inventory.mark_ingredient_stack_consumed_use_case import MarkIngredientStackConsumedUseCase
from src.application.use_cases.inventory.mark_food_item_consumed_use_case import MarkFoodItemConsumedUseCase
from src.application.use_cases.inventory.delete_ingredient_status_use_case import DeleteIngredientStackUseCase
from src.application.use_cases.inventory.delete_ingredient_complete_use_case import DeleteIngredientCompleteUseCase
from src.application.use_cases.inventory.get_ingredient_detail_use_case import GetIngredientDetailUseCase
from src.application.use_cases.inventory.get_food_detail_use_case import GetFoodDetailUseCase
from src.application.use_cases.inventory.get_ingredients_list_use_case import GetIngredientsListUseCase
from src.application.use_cases.inventory.get_foods_list_use_case import GetFoodsListUseCase
from src.application.use_cases.inventory.get_expiring_soon_use_case import GetExpiringSoonUseCase
from src.application.use_cases.inventory.get_inventory_content_use_case import GetInventoryContentUseCase
from src.application.use_cases.inventory.update_food_item_use_case import UpdateFoodItemUseCase
from src.application.use_cases.inventory.update_ingredient_stack_use_case import UpdateIngredientStackUseCase
from src.application.use_cases.inventory.update_ingredient_quantity_use_case import UpdateIngredientQuantityUseCase
from src.application.use_cases.inventory.update_food_quantity_use_case import UpdateFoodQuantityUseCase

from src.infrastructure.db.inventory_repository_impl import InventoryRepositoryImpl
from src.infrastructure.inventory.inventory_calcularor_impl import InventoryCalculatorImpl
from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService

def make_add_food_items_to_inventory_use_case(db):
    return None #AddFoodItemsToInventoryUseCase(InventoryRepositoryImpl(db), InventoryCalculatorImpl)
def make_add_ingredients_and_foods_to_inventory_use_case(db):
    return AddIngredientsAndFoodsToInventoryUseCase(InventoryRepositoryImpl(db), InventoryCalculatorImpl())
def make_add_ingredients_to_inventory_use_case(db):
    return AddIngredientsToInventoryUseCase(
        InventoryRepositoryImpl(db), 
        InventoryCalculatorImpl(), 
        GeminiAdapterService()
    )

def make_add_item_to_inventory_use_case(db):
    return AddItemToInventoryUseCase(
        InventoryRepositoryImpl(db),
        InventoryCalculatorImpl(),
        GeminiAdapterService()
    )
def make_delete_food_item_use_case(db):
    return DeleteFoodItemUseCase(InventoryRepositoryImpl(db))
def make_delete_ingredient_stack_use_case(db):
    return DeleteIngredientStackUseCase(InventoryRepositoryImpl(db))

def make_delete_ingredient_complete_use_case(db):
    return DeleteIngredientCompleteUseCase(InventoryRepositoryImpl(db))

def make_get_ingredient_detail_use_case(db):
    return GetIngredientDetailUseCase(InventoryRepositoryImpl(db))

def make_get_food_detail_use_case(db):
    return GetFoodDetailUseCase(InventoryRepositoryImpl(db))

def make_get_ingredients_list_use_case(db):
    return GetIngredientsListUseCase(InventoryRepositoryImpl(db))

def make_get_foods_list_use_case(db):
    return GetFoodsListUseCase(InventoryRepositoryImpl(db))
def make_get_expiring_soon_use_case(db):
    return GetExpiringSoonUseCase(InventoryRepositoryImpl(db))
def make_get_inventory_content_use_case(db):
    return GetInventoryContentUseCase(InventoryRepositoryImpl(db))
def make_update_food_item_use_case(db):
    return UpdateFoodItemUseCase(InventoryRepositoryImpl(db), InventoryCalculatorImpl())
def make_update_ingredient_stack_use_case(db):
    return UpdateIngredientStackUseCase(InventoryRepositoryImpl(db), InventoryCalculatorImpl())

def make_update_ingredient_quantity_use_case(db):
    return UpdateIngredientQuantityUseCase(InventoryRepositoryImpl(db))

def make_update_food_quantity_use_case(db):
    return UpdateFoodQuantityUseCase(InventoryRepositoryImpl(db))

def make_mark_ingredient_stack_consumed_use_case(db):
    return MarkIngredientStackConsumedUseCase(InventoryRepositoryImpl(db))

def make_mark_food_item_consumed_use_case(db):
    return MarkFoodItemConsumedUseCase(InventoryRepositoryImpl(db))