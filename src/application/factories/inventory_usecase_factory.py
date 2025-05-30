from src.application.use_cases.inventory.get_inventory_use_case import GetInventoryUseCase
from src.application.use_cases.inventory.get_expiring_soon_use_case import GetExpiringSoonUseCase
from src.application.use_cases.inventory.add_ingredient_to_inventory_use_case import AddIngredientToInventoryUseCase
from src.application.use_cases.inventory.add_food_item_to_inventory_use_case import AddFoodItemToInventoryUseCase

from src.infrastructure.db.inventory_repository_impl import InventoryRepositoryImpl
from src.infrastructure.inventory.inventory_calcularor_impl import InventoryCalculatorImpl

def make_get_inventory_use_case(db):
    return GetInventoryUseCase(InventoryRepositoryImpl(db))

def make_get_expiring_soon_use_case(db):
    return GetExpiringSoonUseCase(InventoryRepositoryImpl(db))

def make_add_ingredient_to_inventory_use_case(db):
    return AddIngredientToInventoryUseCase(InventoryRepositoryImpl(db), InventoryCalculatorImpl)

def make_add_food_item_to_inventory_use_case(db):
    return AddFoodItemToInventoryUseCase(InventoryRepositoryImpl(db), InventoryCalculatorImpl)