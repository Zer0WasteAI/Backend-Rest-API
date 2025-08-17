import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from src.application.use_cases.inventory.add_item_to_inventory_use_case import AddItemToInventoryUseCase


class TestAddItemToInventoryUseCase:
    def setup_method(self):
        self.repo = MagicMock()
        self.calculator = MagicMock()
        self.ai = MagicMock()
        self.uc = AddItemToInventoryUseCase(self.repo, self.calculator, self.ai)
        self.calculator.calculate_expiration_date.return_value = datetime.now(timezone.utc)

    def test_add_ingredient_flow(self):
        self.repo.get_by_user_uid.return_value = None  # triggers create
        self.ai.generate_ingredient_data.return_value = {
            'tips': 'store cold', 'expiration_time': 7, 'time_unit': 'days'
        }
        payload = {
            'name': 'Tomate', 'quantity': 2, 'unit': 'pcs',
            'storage_type': 'fridge', 'category': 'ingredient'
        }
        result = self.uc.execute('u1', payload)
        assert result['item_type'] == 'ingredient'
        assert self.repo.add_ingredient_stack.called

    def test_add_food_flow(self):
        self.repo.get_by_user_uid.return_value = object()
        self.ai.generate_food_data = MagicMock()
        self.ai.generate_food_data.return_value = {
            'food_category': 'prepared', 'expiration_time': 3, 'time_unit': 'days',
            'main_ingredients': [], 'description': None, 'tips': None
        }
        # monkeypatch the method used internally
        self.uc._enrich_food_with_ai = self.ai.generate_food_data

        payload = {
            'name': 'Pizza', 'quantity': 1, 'unit': 'portion',
            'storage_type': 'fridge', 'category': 'food'
        }
        result = self.uc.execute('u1', payload)
        assert result['item_type'] == 'food'
        assert self.repo.add_food_item.called

    def test_invalid_category_raises(self):
        payload = {
            'name': 'X', 'quantity': 1, 'unit': 'u', 'storage_type': 'fridge', 'category': 'unknown'
        }
        with pytest.raises(ValueError):
            self.uc.execute('u', payload)

    def test_missing_required_field_raises(self):
        payload = {'name': 'X', 'quantity': 1, 'unit': 'u', 'storage_type': 'fridge'}
        with pytest.raises(ValueError):
            self.uc.execute('u', payload)

