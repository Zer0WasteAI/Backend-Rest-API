import pytest
from unittest.mock import MagicMock
from src.application.use_cases.inventory.update_ingredient_quantity_use_case import UpdateIngredientQuantityUseCase


class TestUpdateIngredientQuantityUseCase:
    def test_execute_updates_quantity_and_preserves_metadata(self):
        repo = MagicMock()
        # Current stack data returned by repo
        repo.get_ingredient_stack.return_value = {
            'quantity': 5.0,
            'type_unit': 'pcs',
            'expiration_date': None,
            'added_at': '2024-01-01T00:00:00Z',
            'storage_type': 'fridge',
            'tips': 'keep fresh',
            'image_path': ''
        }

        uc = UpdateIngredientQuantityUseCase(repo)
        uc.execute(
            user_uid='u1',
            ingredient_name='tomato',
            added_at='2024-01-01T00:00:00Z',
            new_quantity=3.0
        )

        # Should call repo.update_ingredient_stack with new stack and preserved meta
        assert repo.update_ingredient_stack.called
        args, kwargs = repo.update_ingredient_stack.call_args
        assert kwargs['user_uid'] == 'u1'
        assert kwargs['ingredient_name'] == 'tomato'
        # new_stack.quantity must be updated
        assert kwargs['new_stack'].quantity == 3.0
        # meta preserved
        assert kwargs['new_meta'].storage_type == 'fridge'

    def test_execute_raises_when_stack_missing(self):
        repo = MagicMock()
        repo.get_ingredient_stack.return_value = None
        uc = UpdateIngredientQuantityUseCase(repo)
        with pytest.raises(ValueError):
            uc.execute('u1', 'tomato', '2024-01-01T00:00:00Z', 1.0)

