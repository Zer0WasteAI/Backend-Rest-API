import pytest
from unittest.mock import MagicMock
from datetime import datetime
from src.application.use_cases.inventory.get_food_detail_use_case import GetFoodDetailUseCase


class TestGetFoodDetailUseCase:
    def test_execute_returns_detail(self, monkeypatch):
        repo = MagicMock()
        repo.get_food_item.return_value = {
            'name': 'Pizza', 'category': 'prepared', 'serving_quantity': 2,
            'calories': 800, 'description': 'desc', 'storage_type': 'fridge', 'tips': '', 'image_path': '',
            'added_at': datetime.now().isoformat(), 'expiration_date': datetime.now().isoformat(),
            'expiration_time': 2, 'time_unit': 'days', 'main_ingredients': []
        }
        uc = GetFoodDetailUseCase(repo)
        # Avoid hitting real AI in enrichment
        monkeypatch.setenv('DISABLE_AI', '1')
        detail = uc.execute('u1', 'Pizza', datetime.now().isoformat())
        assert detail['name'] == 'Pizza'
        assert 'days_to_expire' in detail

    def test_execute_raises_on_missing_item(self):
        repo = MagicMock()
        repo.get_food_item.return_value = None
        uc = GetFoodDetailUseCase(repo)
        with pytest.raises(ValueError):
            uc.execute('u', 'X', datetime.now().isoformat())

