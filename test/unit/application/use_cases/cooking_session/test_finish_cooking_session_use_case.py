"""
Unit tests for Finish Cooking Session Use Case
Tests cooking session completion functionality
"""
import pytest
from datetime import datetime, date
from unittest.mock import Mock

from src.application.use_cases.cooking_session.finish_cooking_session_use_case import FinishCookingSessionUseCase
from src.shared.exceptions.custom import RecipeNotFoundException


class TestFinishCookingSessionUseCase:
    """Test suite for Finish Cooking Session Use Case"""

    @pytest.fixture
    def mock_cooking_session_repository(self):
        """Mock cooking session repository"""
        return Mock()

    @pytest.fixture
    def mock_environmental_savings_use_case(self):
        """Mock environmental savings use case"""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_cooking_session_repository, mock_environmental_savings_use_case):
        """Create use case with mocked dependencies"""
        return FinishCookingSessionUseCase(
            cooking_session_repository=mock_cooking_session_repository,
            environmental_savings_use_case=mock_environmental_savings_use_case
        )

    @pytest.fixture
    def mock_session(self):
        """Mock cooking session"""
        session = Mock()
        session.session_id = "session_123"
        session.user_uid = "user_123"
        session.recipe_uid = "recipe_123"
        session.servings = 4
        session.is_running.return_value = True
        session.finish_session.return_value = None
        session.get_all_consumptions.return_value = [Mock()]
        session.finished_at = datetime.now()
        session.get_total_cooking_time.return_value = 3600000  # 1 hour in ms
        return session

    def test_finish_session_success(self, use_case, mock_cooking_session_repository, 
                                   mock_environmental_savings_use_case, mock_session):
        """Test successful session completion"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_cooking_session_repository.save.return_value = mock_session
        
        mock_environmental_savings_use_case.execute.return_value = {
            "co2_reduction_kg": 0.5,
            "water_saved_liters": 10.0,
            "food_waste_reduced_kg": 0.2
        }
        
        # Act
        result = use_case.execute(
            session_id="session_123",
            user_uid="user_123",
            notes="Great cooking session!",
            photo_url="https://example.com/photo.jpg"
        )
        
        # Assert
        assert result["ok"] is True
        assert result["session_id"] == "session_123"
        assert result["total_cooking_time_ms"] == 3600000
        assert result["environmental_saving"]["co2e_kg"] == 0.5
        assert result["environmental_saving"]["water_l"] == 10.0
        assert result["environmental_saving"]["waste_kg"] == 0.2
        assert result["leftover_suggestion"]["portions"] == 2  # 4 servings - 2 = 2 portions
        
        mock_cooking_session_repository.find_by_id.assert_called_once_with("session_123")
        mock_session.finish_session.assert_called_once_with(
            notes="Great cooking session!",
            photo_url="https://example.com/photo.jpg"
        )
        mock_cooking_session_repository.save.assert_called_once_with(mock_session)

    def test_finish_session_not_found(self, use_case, mock_cooking_session_repository):
        """Test finishing session that doesn't exist"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(RecipeNotFoundException) as exc_info:
            use_case.execute(
                session_id="nonexistent_session",
                user_uid="user_123"
            )
        
        assert "Cooking session nonexistent_session not found" in str(exc_info.value)

    def test_finish_session_wrong_user(self, use_case, mock_cooking_session_repository, mock_session):
        """Test finishing session with wrong user"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_session.user_uid = "different_user"
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                session_id="session_123",
                user_uid="user_123"
            )
        
        assert "Session does not belong to user" in str(exc_info.value)

    def test_finish_session_already_finished(self, use_case, mock_cooking_session_repository, mock_session):
        """Test finishing session that's already finished"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_session.is_running.return_value = False
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                session_id="session_123",
                user_uid="user_123"
            )
        
        assert "Session is already finished" in str(exc_info.value)

    def test_finish_session_without_optional_params(self, use_case, mock_cooking_session_repository, 
                                                   mock_environmental_savings_use_case, mock_session):
        """Test finishing session without notes or photo"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_cooking_session_repository.save.return_value = mock_session
        
        mock_environmental_savings_use_case.execute.return_value = {
            "co2_reduction_kg": 0.3,
            "water_saved_liters": 8.0,
            "food_waste_reduced_kg": 0.1
        }
        
        # Act
        result = use_case.execute(
            session_id="session_123",
            user_uid="user_123"
        )
        
        # Assert
        assert result["ok"] is True
        mock_session.finish_session.assert_called_once_with(notes=None, photo_url=None)

    def test_finish_session_environmental_calculation_failure(self, use_case, mock_cooking_session_repository, 
                                                            mock_environmental_savings_use_case, mock_session):
        """Test session finishing when environmental calculation fails"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_cooking_session_repository.save.return_value = mock_session
        
        mock_environmental_savings_use_case.execute.side_effect = Exception("AI service unavailable")
        
        # Act
        result = use_case.execute(
            session_id="session_123",
            user_uid="user_123"
        )
        
        # Assert
        assert result["ok"] is True
        # Should have default environmental savings
        assert result["environmental_saving"]["co2e_kg"] == 0.0
        assert result["environmental_saving"]["water_l"] == 0.0
        assert result["environmental_saving"]["waste_kg"] == 0.0

    def test_finish_session_no_consumptions(self, use_case, mock_cooking_session_repository, 
                                          mock_environmental_savings_use_case, mock_session):
        """Test finishing session with no consumptions"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_cooking_session_repository.save.return_value = mock_session
        mock_session.get_all_consumptions.return_value = []
        
        # Environmental calculation should not be called if no consumptions
        
        # Act
        result = use_case.execute(
            session_id="session_123",
            user_uid="user_123"
        )
        
        # Assert
        assert result["ok"] is True
        # Should have default environmental savings when no consumptions
        assert result["environmental_saving"]["co2e_kg"] == 0.0
        assert result["environmental_saving"]["water_l"] == 0.0
        assert result["environmental_saving"]["waste_kg"] == 0.0

    def test_finish_session_small_servings_no_leftover_suggestion(self, use_case, mock_cooking_session_repository, 
                                                                mock_environmental_savings_use_case, mock_session):
        """Test finishing session with small servings doesn't suggest leftovers"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_cooking_session_repository.save.return_value = mock_session
        mock_session.servings = 2  # Small serving size
        
        mock_environmental_savings_use_case.execute.return_value = {
            "co2_reduction_kg": 0.2,
            "water_saved_liters": 5.0,
            "food_waste_reduced_kg": 0.1
        }
        
        # Act
        result = use_case.execute(
            session_id="session_123",
            user_uid="user_123"
        )
        
        # Assert
        assert result["ok"] is True
        assert result["leftover_suggestion"] is None

    def test_finish_session_large_servings_suggests_leftovers(self, use_case, mock_cooking_session_repository, 
                                                            mock_environmental_savings_use_case, mock_session):
        """Test finishing session with large servings suggests leftovers"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_cooking_session_repository.save.return_value = mock_session
        mock_session.servings = 6  # Large serving size
        
        mock_environmental_savings_use_case.execute.return_value = {
            "co2_reduction_kg": 0.8,
            "water_saved_liters": 15.0,
            "food_waste_reduced_kg": 0.3
        }
        
        # Act
        result = use_case.execute(
            session_id="session_123",
            user_uid="user_123"
        )
        
        # Assert
        assert result["ok"] is True
        assert result["leftover_suggestion"]["portions"] == 4  # 6 servings - 2 = 4 portions
        # Check eat_by date is 2 days from now
        eat_by = date.fromisoformat(result["leftover_suggestion"]["eat_by"])
        expected_date = date.today().replace(day=date.today().day + 2)
        assert eat_by == expected_date

    def test_finish_session_repository_error_propagation(self, use_case, mock_cooking_session_repository):
        """Test that repository errors are propagated"""
        # Arrange
        mock_cooking_session_repository.find_by_id.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                session_id="session_123",
                user_uid="user_123"
            )
        
        assert str(exc_info.value) == "Database connection error"

    def test_finish_session_save_error_propagation(self, use_case, mock_cooking_session_repository, 
                                                  mock_environmental_savings_use_case, mock_session):
        """Test that save errors are propagated"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_cooking_session_repository.save.side_effect = Exception("Save operation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                session_id="session_123",
                user_uid="user_123"
            )
        
        assert str(exc_info.value) == "Save operation failed"