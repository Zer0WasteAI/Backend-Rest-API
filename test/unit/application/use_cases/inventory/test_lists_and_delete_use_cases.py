import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from src.application.use_cases.inventory.get_ingredients_list_use_case import GetIngredientsListUseCase
from src.application.use_cases.inventory.get_foods_list_use_case import GetFoodsListUseCase
from src.application.use_cases.inventory.delete_food_item_use_case import DeleteFoodItemUseCase
from src.application.use_cases.inventory.delete_ingredient_complete_use_case import DeleteIngredientCompleteUseCase


class TestGetIngredientsListUseCase:
    def test_empty_inventory_returns_defaults(self):
        repo = MagicMock()
        repo.get_by_user_uid.return_value = None
        uc = GetIngredientsListUseCase(repo)
        res = uc.execute('u')
        assert res['total_ingredients'] == 0

    def test_non_empty_inventory(self):
        # Build a minimal Inventory with one ingredient and one stack
        from src.domain.models.inventory import Inventory
        from src.domain.models.ingredient import Ingredient, IngredientStack
        inv = Inventory('u')
        ing = Ingredient('Tomato', 'g', 'fridge', tips='', image_path='')
        ing.add_stack(IngredientStack(10, 'g', datetime.now(timezone.utc), datetime.now(timezone.utc)))
        inv.ingredients['Tomato'] = ing

        repo = MagicMock()
        repo.get_by_user_uid.return_value = inv
        uc = GetIngredientsListUseCase(repo)
        res = uc.execute('u')
        assert res['total_ingredients'] == 1
        assert res['total_stacks'] >= 1


class TestGetFoodsListUseCase:
    def test_empty_foods_returns_defaults(self):
        repo = MagicMock()
        repo.get_all_food_items.return_value = []
        uc = GetFoodsListUseCase(repo)
        res = uc.execute('u')
        assert res['total_foods'] == 0

    def test_non_empty_foods(self):
        now = datetime.now(timezone.utc)
        repo = MagicMock()
        repo.get_all_food_items.return_value = [{
            'name': 'Pizza', 'main_ingredients': [], 'category': 'prepared', 'calories': 800,
            'description': '', 'storage_type': 'fridge', 'expiration_time': 2, 'time_unit': 'days',
            'tips': '', 'serving_quantity': 2, 'image_path': '', 'added_at': now, 'expiration_date': now
        }]
        uc = GetFoodsListUseCase(repo)
        res = uc.execute('u')
        assert res['total_foods'] == 1
        assert res['total_servings'] >= 2


class TestDeleteUseCases:
    def test_delete_food_item_use_case(self):
        repo = MagicMock()
        repo.get_food_item.return_value = {'name': 'Pizza'}
        uc = DeleteFoodItemUseCase(repo)
        uc.execute('u', 'Pizza', '2024-01-01T00:00:00Z')
        assert repo.delete_food_item.called

    def test_delete_food_item_missing_raises(self):
        repo = MagicMock()
        repo.get_food_item.return_value = None
        uc = DeleteFoodItemUseCase(repo)
        with pytest.raises(ValueError):
            uc.execute('u', 'Pizza', '2024-01-01T00:00:00Z')

    def test_delete_ingredient_complete_use_case(self):
        repo = MagicMock()
        repo.get_all_ingredient_stacks.return_value = [{'quantity': 1}]
        uc = DeleteIngredientCompleteUseCase(repo)
        uc.execute('u', 'Tomato')
        assert repo.delete_ingredient_complete.called

    def test_delete_ingredient_complete_missing_raises(self):
        repo = MagicMock()
        repo.get_all_ingredient_stacks.return_value = []
        uc = DeleteIngredientCompleteUseCase(repo)
        with pytest.raises(ValueError):
            uc.execute('u', 'Tomato')

