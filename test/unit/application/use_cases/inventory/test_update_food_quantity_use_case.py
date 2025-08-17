import pytest
from unittest.mock import MagicMock
from src.application.use_cases.inventory.update_food_quantity_use_case import UpdateFoodQuantityUseCase


class TestUpdateFoodQuantityUseCase:
    def test_execute_updates_serving_quantity(self):
        repo = MagicMock()
        repo.get_food_item.return_value = {
            'main_ingredients': [], 'category': 'prepared', 'calories': 500,
            'description': '', 'storage_type': 'fridge', 'expiration_time': 2,
            'time_unit': 'days', 'tips': '', 'serving_quantity': 1,
            'image_path': '', 'expiration_date': None
        }
        uc = UpdateFoodQuantityUseCase(repo)
        uc.execute('u', 'Pizza', '2024-01-01T00:00:00Z', new_quantity=3)
        assert repo.update_food_item.called
        args, kwargs = repo.update_food_item.call_args
        assert kwargs['user_uid'] == 'u'
        assert kwargs['updated_food_item'].serving_quantity == 3

    def test_execute_raises_when_missing(self):
        repo = MagicMock()
        repo.get_food_item.return_value = None
        uc = UpdateFoodQuantityUseCase(repo)
        with pytest.raises(ValueError):
            uc.execute('u', 'X', '2024-01-01T00:00:00Z', 1)

