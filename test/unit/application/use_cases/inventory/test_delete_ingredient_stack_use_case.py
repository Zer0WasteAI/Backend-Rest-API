import pytest
from unittest.mock import MagicMock

from src.application.use_cases.inventory.delete_ingredient_status_use_case import DeleteIngredientStackUseCase


class TestDeleteIngredientStackUseCase:
    def test_execute_deletes_when_exists(self):
        repo = MagicMock()
        repo.get_ingredient_stack.return_value = {'quantity': 1}
        uc = DeleteIngredientStackUseCase(repo)
        uc.execute('u1', 'Tomato', '2024-01-01T00:00:00Z')
        repo.delete_ingredient_stack.assert_called_once()

    def test_execute_raises_when_missing(self):
        repo = MagicMock()
        repo.get_ingredient_stack.return_value = None
        uc = DeleteIngredientStackUseCase(repo)
        with pytest.raises(ValueError):
            uc.execute('u1', 'Tomato', '2024-01-01T00:00:00Z')

