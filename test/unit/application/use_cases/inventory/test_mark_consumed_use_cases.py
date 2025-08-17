import pytest
from unittest.mock import MagicMock
from datetime import datetime
from src.application.use_cases.inventory.mark_food_item_consumed_use_case import MarkFoodItemConsumedUseCase
from src.application.use_cases.inventory.mark_ingredient_stack_consumed_use_case import MarkIngredientStackConsumedUseCase


class TestMarkFoodItemConsumedUseCase:
    def setup_method(self):
        self.repo = MagicMock()
        self.uc = MarkFoodItemConsumedUseCase(self.repo)

    def test_full_consumption_deletes_item(self):
        self.repo.get_food_item.return_value = {
            'serving_quantity': 2, 'main_ingredients': [], 'category': 'c', 'calories': 100,
            'description': '', 'storage_type': 'fridge', 'expiration_time': 2, 'time_unit': 'days',
            'tips': '', 'image_path': '', 'expiration_date': datetime.now(),
        }
        result = self.uc.execute('u', 'Pizza', '2024-01-01T00:00:00Z')
        assert result['action'] == 'full_consumption'
        assert self.repo.delete_food_item.called

    def test_partial_consumption_updates_item(self):
        self.repo.get_food_item.return_value = {
            'serving_quantity': 3, 'main_ingredients': [], 'category': 'c', 'calories': 100,
            'description': '', 'storage_type': 'fridge', 'expiration_time': 2, 'time_unit': 'days',
            'tips': '', 'image_path': '', 'expiration_date': datetime.now(),
        }
        result = self.uc.execute('u', 'Pizza', '2024-01-01T00:00:00Z', consumed_portions=1)
        assert result['action'] == 'partial_consumption'
        assert result['remaining_portions'] == 2
        assert self.repo.update_food_item.called

    def test_invalid_consumed_portions_raises(self):
        self.repo.get_food_item.return_value = {'serving_quantity': 1}
        with pytest.raises(ValueError):
            self.uc.execute('u', 'Pizza', '2024-01-01T00:00:00Z', consumed_portions=0)
        with pytest.raises(ValueError):
            self.uc.execute('u', 'Pizza', '2024-01-01T00:00:00Z', consumed_portions=2)


class TestMarkIngredientStackConsumedUseCase:
    def setup_method(self):
        self.repo = MagicMock()
        self.uc = MarkIngredientStackConsumedUseCase(self.repo)

    def test_full_consumption_deletes_stack(self):
        self.repo.get_ingredient_stack.return_value = {
            'quantity': 5, 'type_unit': 'g', 'expiration_date': datetime.now(),
            'storage_type': 'fridge', 'tips': '', 'image_path': ''
        }
        result = self.uc.execute('u', 'tomato', '2024-01-01T00:00:00Z')
        assert result['action'] == 'full_consumption'
        assert self.repo.delete_ingredient_stack.called

    def test_partial_consumption_updates_stack(self):
        self.repo.get_ingredient_stack.return_value = {
            'quantity': 10, 'type_unit': 'g', 'expiration_date': datetime.now(),
            'storage_type': 'fridge', 'tips': '', 'image_path': ''
        }
        result = self.uc.execute('u', 'tomato', '2024-01-01T00:00:00Z', consumed_quantity=4)
        assert result['action'] == 'partial_consumption'
        assert result['remaining_quantity'] == 6
        assert self.repo.update_ingredient_stack.called

    def test_invalid_consumed_quantity_raises(self):
        self.repo.get_ingredient_stack.return_value = {'quantity': 1, 'type_unit': 'g'}
        with pytest.raises(ValueError):
            self.uc.execute('u', 'tomato', '2024-01-01T00:00:00Z', consumed_quantity=0)
        with pytest.raises(ValueError):
            self.uc.execute('u', 'tomato', '2024-01-01T00:00:00Z', consumed_quantity=2)

