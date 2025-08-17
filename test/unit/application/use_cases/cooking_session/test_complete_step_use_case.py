"""
Unit tests for Complete Step Use Case
Tests cooking session step completion functionality
"""
import pytest
from datetime import datetime
from unittest.mock import Mock

from src.application.use_cases.cooking_session.complete_step_use_case import CompleteStepUseCase
from src.shared.exceptions.custom import RecipeNotFoundException


class TestCompleteStepUseCase:
    """Test suite for Complete Step Use Case"""

    @pytest.fixture
    def mock_cooking_session_repository(self):
        """Mock cooking session repository"""
        return Mock()

    @pytest.fixture
    def mock_batch_repository(self):
        """Mock ingredient batch repository"""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_cooking_session_repository, mock_batch_repository):
        """Create use case with mocked dependencies"""
        return CompleteStepUseCase(
            cooking_session_repository=mock_cooking_session_repository,
            batch_repository=mock_batch_repository
        )

    @pytest.fixture
    def mock_session(self):
        """Mock cooking session"""
        session = Mock()
        session.session_id = "session_123"
        session.user_uid = "user_123"
        session.recipe_uid = "recipe_123"
        session.is_running.return_value = True
        session.complete_step.return_value = True
        return session

    @pytest.fixture
    def mock_consumption_log(self):
        """Mock consumption log"""
        log = Mock()
        log.ingredient_name = "Tomate"
        log.quantity_used = 2.0
        log.unit = "piezas"
        return log

    def test_complete_step_success(self, use_case, mock_cooking_session_repository, 
                                  mock_batch_repository, mock_session, mock_consumption_log):
        """Test successful step completion"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_cooking_session_repository.save.return_value = mock_session
        
        consumptions = [mock_consumption_log]
        
        # Act
        result = use_case.execute(
            session_id="session_123",
            user_uid="user_123",
            step_number=1,
            consumptions=consumptions
        )
        
        # Assert
        assert result["ok"] is True
        assert result["session_id"] == "session_123"
        assert result["step_completed"] == 1
        
        mock_cooking_session_repository.find_by_id.assert_called_once_with("session_123")
        mock_session.complete_step.assert_called_once_with(1, consumptions)
        mock_cooking_session_repository.save.assert_called_once_with(mock_session)

    def test_complete_step_session_not_found(self, use_case, mock_cooking_session_repository):
        """Test step completion when session not found"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(RecipeNotFoundException) as exc_info:
            use_case.execute(
                session_id="nonexistent_session",
                user_uid="user_123",
                step_number=1,
                consumptions=[]
            )
        
        assert "Cooking session nonexistent_session not found" in str(exc_info.value)

    def test_complete_step_wrong_user(self, use_case, mock_cooking_session_repository, mock_session):
        """Test step completion with wrong user"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_session.user_uid = "different_user"
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                session_id="session_123",
                user_uid="user_123",
                step_number=1,
                consumptions=[]
            )
        
        assert "Session does not belong to user" in str(exc_info.value)

    def test_complete_step_session_not_running(self, use_case, mock_cooking_session_repository, mock_session):
        """Test step completion when session is not running"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_session.is_running.return_value = False
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                session_id="session_123",
                user_uid="user_123",
                step_number=1,
                consumptions=[]
            )
        
        assert "Session is not running" in str(exc_info.value)

    def test_complete_step_invalid_step_number(self, use_case, mock_cooking_session_repository, mock_session):
        """Test step completion with invalid step number"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_session.complete_step.side_effect = ValueError("Invalid step number")
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                session_id="session_123",
                user_uid="user_123",
                step_number=999,
                consumptions=[]
            )
        
        assert "Invalid step number" in str(exc_info.value)

    def test_complete_step_with_multiple_consumptions(self, use_case, mock_cooking_session_repository, 
                                                     mock_batch_repository, mock_session):
        """Test step completion with multiple consumptions"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_cooking_session_repository.save.return_value = mock_session
        
        consumptions = [
            Mock(ingredient_name="Tomate", quantity_used=2.0, unit="piezas"),
            Mock(ingredient_name="Cebolla", quantity_used=1.0, unit="piezas"),
            Mock(ingredient_name="Aceite", quantity_used=50.0, unit="ml")
        ]
        
        # Act
        result = use_case.execute(
            session_id="session_123",
            user_uid="user_123",
            step_number=2,
            consumptions=consumptions
        )
        
        # Assert
        assert result["ok"] is True
        assert result["step_completed"] == 2
        mock_session.complete_step.assert_called_once_with(2, consumptions)

    def test_complete_step_empty_consumptions(self, use_case, mock_cooking_session_repository, 
                                            mock_session):
        """Test step completion with empty consumptions"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_cooking_session_repository.save.return_value = mock_session
        
        # Act
        result = use_case.execute(
            session_id="session_123",
            user_uid="user_123",
            step_number=1,
            consumptions=[]
        )
        
        # Assert
        assert result["ok"] is True
        mock_session.complete_step.assert_called_once_with(1, [])

    def test_complete_step_repository_error_propagation(self, use_case, mock_cooking_session_repository):
        """Test that repository errors are propagated"""
        # Arrange
        mock_cooking_session_repository.find_by_id.side_effect = Exception("Database connection error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                session_id="session_123",
                user_uid="user_123",
                step_number=1,
                consumptions=[]
            )
        
        assert str(exc_info.value) == "Database connection error"

    def test_complete_step_save_error_propagation(self, use_case, mock_cooking_session_repository, mock_session):
        """Test that save errors are propagated"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_cooking_session_repository.save.side_effect = Exception("Save operation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                session_id="session_123",
                user_uid="user_123",
                step_number=1,
                consumptions=[]
            )
        
        assert str(exc_info.value) == "Save operation failed"

    def test_complete_step_with_timestamp_validation(self, use_case, mock_cooking_session_repository, 
                                                   mock_session):
        """Test step completion includes timestamp validation"""
        # Arrange
        mock_cooking_session_repository.find_by_id.return_value = mock_session
        mock_cooking_session_repository.save.return_value = mock_session
        
        # Act
        result = use_case.execute(
            session_id="session_123",
            user_uid="user_123",
            step_number=1,
            consumptions=[]
        )
        
        # Assert
        assert "completed_at" in result
        # Verify the timestamp is recent (within last 10 seconds)
        completed_at = datetime.fromisoformat(result["completed_at"].replace('Z', '+00:00'))
        time_diff = datetime.now(completed_at.tzinfo) - completed_at
        assert time_diff.total_seconds() < 10