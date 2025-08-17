import pytest
import uuid
from datetime import datetime, date, timedelta
from unittest.mock import Mock
from src.domain.models.cooking_session import CookingSession, CookingLevel, StepConsumption
from src.domain.models.environmental_savings import EnvironmentalSavings
from src.application.use_cases.recipes.calculate_environmental_savings_from_session import CalculateEnvironmentalSavingsFromSessionUseCase
from src.shared.exceptions.custom import RecipeNotFoundException


class TestEnvironmentalSavingsFromSession:
    """Test suite for environmental savings calculation from cooking sessions"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_session_repo = Mock()
        self.mock_env_repo = Mock()
        self.user_uid = "test_user_123"
        self.session_id = str(uuid.uuid4())
        self.recipe_uid = "recipe_test_001"

    def create_test_session(self, servings=2):
        """Helper to create test cooking session"""
        session = CookingSession(
            session_id=self.session_id,
            recipe_uid=self.recipe_uid,
            user_uid=self.user_uid,
            servings=servings,
            level=CookingLevel.INTERMEDIATE,
            started_at=datetime.utcnow()
        )
        
        # Add some consumption data
        consumptions = [
            StepConsumption("ing_chicken", "batch_123", 300, "g"),
            StepConsumption("ing_vegetables", "batch_456", 200, "g"),
            StepConsumption("ing_rice", "batch_789", 150, "g")
        ]
        
        for consumption in consumptions:
            session.steps.append(Mock(
                status="done",
                consumptions=[consumption]
            ))
        
        return session

    def test_calculate_savings_from_session_success(self):
        """Test successful environmental savings calculation from session"""
        # Arrange
        session = self.create_test_session(servings=3)
        
        saved_savings = EnvironmentalSavings(
            uid="env_calc_123",
            user_uid=self.user_uid,
            recipe_uid=self.recipe_uid,
            co2_reduction_kg=0.42,
            water_saved_liters=120.0,
            food_waste_reduced_kg=0.18,
            calculation_method="session_based"
        )
        
        self.mock_session_repo.find_by_id.return_value = session
        self.mock_env_repo.save.return_value = saved_savings
        
        use_case = CalculateEnvironmentalSavingsFromSessionUseCase(
            self.mock_session_repo,
            self.mock_env_repo
        )
        
        # Act
        result = use_case.execute(
            session_id=self.session_id,
            user_uid=self.user_uid
        )
        
        # Assert
        assert result["calculation_id"] == "env_calc_123"
        assert result["session_id"] == self.session_id
        assert result["co2e_kg"] > 0
        assert result["water_l"] > 0
        assert result["waste_kg"] > 0
        assert result["basis"] == "per_session"
        assert result["consumptions_analyzed"] == 3

    def test_calculate_savings_with_actual_consumptions(self):
        """Test calculation with provided actual consumptions (override session data)"""
        # Arrange
        session = self.create_test_session(servings=2)
        
        actual_consumptions = [
            {"ingredient_uid": "ing_chicken", "qty": 400, "unit": "g"},
            {"ingredient_uid": "ing_vegetables", "qty": 150, "unit": "g"}
        ]
        
        saved_savings = EnvironmentalSavings(
            uid="env_calc_456",
            user_uid=self.user_uid,
            recipe_uid=self.recipe_uid,
            co2_reduction_kg=0.35,
            water_saved_liters=90.0,
            food_waste_reduced_kg=0.15,
            calculation_method="session_based"
        )
        
        self.mock_session_repo.find_by_id.return_value = session
        self.mock_env_repo.save.return_value = saved_savings
        
        use_case = CalculateEnvironmentalSavingsFromSessionUseCase(
            self.mock_session_repo,
            self.mock_env_repo
        )
        
        # Act
        result = use_case.execute(
            session_id=self.session_id,
            user_uid=self.user_uid,
            actual_consumptions=actual_consumptions
        )
        
        # Assert
        assert result["consumptions_analyzed"] == 2
        assert result["co2e_kg"] == 0.35

    def test_calculate_savings_session_not_found(self):
        """Test calculation with non-existent session"""
        # Arrange
        self.mock_session_repo.find_by_id.return_value = None
        
        use_case = CalculateEnvironmentalSavingsFromSessionUseCase(
            self.mock_session_repo,
            self.mock_env_repo
        )
        
        # Act & Assert
        with pytest.raises(RecipeNotFoundException):
            use_case.execute(
                session_id="non_existent",
                user_uid=self.user_uid
            )

    def test_calculate_savings_wrong_user(self):
        """Test calculation with session belonging to different user"""
        # Arrange
        session = self.create_test_session()
        session.user_uid = "different_user"
        
        self.mock_session_repo.find_by_id.return_value = session
        
        use_case = CalculateEnvironmentalSavingsFromSessionUseCase(
            self.mock_session_repo,
            self.mock_env_repo
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Session does not belong to user"):
            use_case.execute(
                session_id=self.session_id,
                user_uid=self.user_uid
            )

    def test_calculate_savings_factors(self):
        """Test environmental savings calculation factors"""
        # Arrange
        use_case = CalculateEnvironmentalSavingsFromSessionUseCase(
            self.mock_session_repo,
            self.mock_env_repo
        )
        
        consumptions = [
            {"ingredient_uid": "ing_chicken", "qty": 1000, "unit": "g"},  # 1kg chicken
            {"ingredient_uid": "ing_beef", "qty": 500, "unit": "g"},     # 0.5kg beef
            {"ingredient_uid": "ing_vegetables", "qty": 300, "unit": "g"} # 0.3kg vegetables
        ]
        
        # Act
        result = use_case._calculate_savings(consumptions, servings=2)
        
        # Assert
        assert result["co2e_kg"] > 0
        assert result["water_l"] > 0
        assert result["waste_kg"] > 0
        
        # Beef should have higher impact than vegetables
        beef_only = use_case._calculate_savings([{"ingredient_uid": "ing_beef", "qty": 1000, "unit": "g"}], 2)
        veg_only = use_case._calculate_savings([{"ingredient_uid": "ing_vegetables", "qty": 1000, "unit": "g"}], 2)
        
        assert beef_only["co2e_kg"] > veg_only["co2e_kg"]

    def test_calculate_savings_servings_multiplier(self):
        """Test that more servings increase environmental impact"""
        # Arrange
        use_case = CalculateEnvironmentalSavingsFromSessionUseCase(
            self.mock_session_repo,
            self.mock_env_repo
        )
        
        consumptions = [{"ingredient_uid": "ing_chicken", "qty": 1000, "unit": "g"}]
        
        # Act
        result_2_servings = use_case._calculate_savings(consumptions, servings=2)
        result_4_servings = use_case._calculate_savings(consumptions, servings=4)
        
        # Assert
        assert result_4_servings["co2e_kg"] > result_2_servings["co2e_kg"]
        assert result_4_servings["water_l"] > result_2_servings["water_l"]
        assert result_4_servings["waste_kg"] > result_2_servings["waste_kg"]

    def test_convert_to_kg_various_units(self):
        """Test unit conversion to kg"""
        # Arrange
        use_case = CalculateEnvironmentalSavingsFromSessionUseCase(
            self.mock_session_repo,
            self.mock_env_repo
        )
        
        # Act & Assert
        assert use_case._convert_to_kg(1000, "g") == 1.0
        assert use_case._convert_to_kg(1, "kg") == 1.0
        assert use_case._convert_to_kg(1000, "ml") == 1.0  # Assuming 1ml = 1g
        assert use_case._convert_to_kg(1, "l") == 1.0
        assert use_case._convert_to_kg(10, "units") == 1.0  # 10 units = 1kg

    def test_calculate_savings_no_consumptions(self):
        """Test calculation with no consumptions"""
        # Arrange
        session = CookingSession(
            session_id=self.session_id,
            recipe_uid=self.recipe_uid,
            user_uid=self.user_uid,
            servings=2,
            level=CookingLevel.INTERMEDIATE,
            started_at=datetime.utcnow()
        )
        
        saved_savings = EnvironmentalSavings(
            uid="env_calc_empty",
            user_uid=self.user_uid,
            recipe_uid=self.recipe_uid,
            co2_reduction_kg=0.0,
            water_saved_liters=0.0,
            food_waste_reduced_kg=0.0,
            calculation_method="session_based"
        )
        
        self.mock_session_repo.find_by_id.return_value = session
        self.mock_env_repo.save.return_value = saved_savings
        
        use_case = CalculateEnvironmentalSavingsFromSessionUseCase(
            self.mock_session_repo,
            self.mock_env_repo
        )
        
        # Act
        result = use_case.execute(
            session_id=self.session_id,
            user_uid=self.user_uid
        )
        
        # Assert
        assert result["consumptions_analyzed"] == 0
        assert result["co2e_kg"] == 0.0
        assert result["water_l"] == 0.0
        assert result["waste_kg"] == 0.0


class TestEnvironmentalSavingsIntegration:
    """Integration tests for environmental savings workflow"""

    def test_session_to_savings_pipeline(self):
        """Test complete pipeline from cooking session to environmental savings"""
        # This would test the full integration including:
        # 1. Starting cooking session
        # 2. Completing steps with consumptions
        # 3. Finishing session
        # 4. Calculating environmental impact
        # For now, this is a placeholder for future implementation
        pass


if __name__ == "__main__":
    pytest.main([__file__])