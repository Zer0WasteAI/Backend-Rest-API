import pytest
from unittest.mock import MagicMock
from datetime import datetime
from src.application.use_cases.inventory.update_food_item_use_case import UpdateFoodItemUseCase


class TestUpdateFoodItemUseCase:
    def setup_method(self):
        self.repo = MagicMock()
        self.calculator = MagicMock()
        self.uc = UpdateFoodItemUseCase(self.repo, self.calculator)

    def test_execute_with_expiration_date(self):
        data = {
            'name': 'pizza',
            'main_ingredients': ['flour'],
            'category': 'prepared',
            'calories': 800,
            'description': 'nice',
            'storage_type': 'fridge',
            'expiration_time': 2,
            'time_unit': 'days',
            'tips': 'none',
            'serving_quantity': 2,
            'image_path': '',
            'added_at': datetime.now().isoformat(),
            'expiration_date': datetime.now().isoformat()
        }
        self.uc.execute('u1', data)
        assert self.repo.update_food_item.called

    def test_execute_with_calculated_expiration(self):
        self.calculator.calculate_expiration_date.return_value = datetime.now()
        data = {
            'name': 'pizza',
            'main_ingredients': ['flour'],
            'category': 'prepared',
            'calories': 800,
            'description': 'nice',
            'storage_type': 'fridge',
            'expiration_time': 2,
            'time_unit': 'days',
            'tips': 'none',
            'serving_quantity': 2,
            'image_path': '',
            'added_at': datetime.now().isoformat(),
        }
        self.uc.execute('u1', data)
        assert self.repo.update_food_item.called

    def test_execute_missing_expiration_info_raises(self):
        data = {
            'name': 'pizza',
            'main_ingredients': [],
            'category': 'prepared',
            'calories': 800,
            'description': 'nice',
            'storage_type': 'fridge',
            'tips': 'none',
            'serving_quantity': 2,
            'image_path': '',
            'added_at': datetime.now().isoformat(),
        }
        with pytest.raises(ValueError):
            self.uc.execute('u1', data)

