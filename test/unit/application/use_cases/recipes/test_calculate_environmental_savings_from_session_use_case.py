import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from src.application.use_cases.recipes.calculate_environmental_savings_from_session import (
    CalculateEnvironmentalSavingsFromSessionUseCase
)
from src.shared.exceptions.custom import RecipeNotFoundException


class TestCalculateEnvironmentalSavingsFromSessionUseCase:
    def setup_method(self):
        self.session_repo = MagicMock()
        self.env_repo = MagicMock()
        self.uc = CalculateEnvironmentalSavingsFromSessionUseCase(self.session_repo, self.env_repo)

    def test_session_not_found_raises(self):
        self.session_repo.find_by_id.return_value = None
        with pytest.raises(RecipeNotFoundException):
            self.uc.execute('sess1', 'u1')

    def test_user_mismatch_raises(self):
        session = MagicMock()
        session.user_uid = 'other'
        self.session_repo.find_by_id.return_value = session
        with pytest.raises(ValueError):
            self.uc.execute('sess1', 'u1')

    def test_success_with_actual_consumptions(self):
        # Arrange session
        session = MagicMock()
        session.user_uid = 'u1'
        session.recipe_uid = 'r1'
        session.servings = 2
        self.session_repo.find_by_id.return_value = session

        saved = MagicMock()
        saved.uid = 'calc1'
        saved.calculated_at = datetime.now(timezone.utc)
        self.env_repo.save.return_value = saved

        consumptions = [
            {"ingredient_uid": "ing_vegetables", "qty": 0.5, "unit": "kg"},
            {"ingredient_uid": "ing_rice", "qty": 200, "unit": "g"},
        ]

        # Act
        res = self.uc.execute('sess1', 'u1', actual_consumptions=consumptions)

        # Assert
        assert res['calculation_id'] == 'calc1'
        assert res['session_id'] == 'sess1'
        assert 'co2e_kg' in res and 'water_l' in res and 'waste_kg' in res
        self.env_repo.save.assert_called_once()

    def test_uses_session_consumptions_when_not_provided(self):
        session = MagicMock()
        session.user_uid = 'u1'
        session.recipe_uid = 'r1'
        session.servings = 2
        # Mock session consumptions objects with attrs ingredient_uid, qty, unit
        c = MagicMock()
        c.ingredient_uid = 'ing_vegetables'
        c.qty = 100
        c.unit = 'g'
        session.get_all_consumptions.return_value = [c]
        self.session_repo.find_by_id.return_value = session

        saved = MagicMock()
        saved.uid = 'calc1'
        saved.calculated_at = datetime.now(timezone.utc)
        self.env_repo.save.return_value = saved

        res = self.uc.execute('sess1', 'u1')
        assert res['calculation_id'] == 'calc1'

