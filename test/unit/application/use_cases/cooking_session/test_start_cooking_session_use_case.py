"""
Unit tests for Start Cooking Session Use Case
Tests cooking session initialization and validation
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from src.application.use_cases.cooking_session.start_cooking_session_use_case import StartCookingSessionUseCase
from src.domain.models.cooking_session import CookingSession, CookingLevel
from src.shared.exceptions.custom import RecipeNotFoundException


class TestStartCookingSessionUseCase:
    """Test suite for Start Cooking Session Use Case"""
    
    @pytest.fixture
    def mock_cooking_session_repository(self):
        """Mock cooking session repository"""
        return Mock()
    
    @pytest.fixture
    def mock_recipe_repository(self):
        """Mock recipe repository"""
        return Mock()
    
    @pytest.fixture
    def use_case(self, mock_cooking_session_repository, mock_recipe_repository):
        """Create use case with mocked dependencies"""
        return StartCookingSessionUseCase(
            cooking_session_repository=mock_cooking_session_repository,
            recipe_repository=mock_recipe_repository
        )
    
    @pytest.fixture
    def valid_recipe(self):
        """Mock valid recipe object"""
        recipe = Mock()
        recipe.uid = "recipe_123"
        recipe.title = "Pasta Italiana"
        recipe.steps = [
            {"id": "step_1", "instruction": "Boil water", "duration_ms": 300000},
            {"id": "step_2", "instruction": "Cook pasta", "duration_ms": 600000}
        ]
        return recipe

    def test_start_cooking_session_success(self, use_case, mock_cooking_session_repository, 
                                          mock_recipe_repository, valid_recipe):
        """Test successful cooking session start"""
        # Arrange
        mock_recipe_repository.get_recipe_by_uid.return_value = valid_recipe
        mock_cooking_session_repository.count_active_sessions.return_value = 1
        
        mock_session = Mock()
        mock_session.session_id = "cook_456"
        mock_cooking_session_repository.create_session.return_value = mock_session
        
        started_at = datetime.now(timezone.utc)
        
        # Act
        result = use_case.execute(
            recipe_uid="recipe_123",
            servings=2,
            level="intermediate",
            user_uid="user_123",
            started_at=started_at
        )
        
        # Assert
        assert result.session_id == "cook_456"
        mock_recipe_repository.get_recipe_by_uid.assert_called_once_with("recipe_123")
        mock_cooking_session_repository.count_active_sessions.assert_called_once_with("user_123")
        mock_cooking_session_repository.create_session.assert_called_once()

    def test_start_cooking_session_recipe_not_found(self, use_case, mock_recipe_repository):
        """Test start cooking session with non-existent recipe"""
        # Arrange
        mock_recipe_repository.get_recipe_by_uid.return_value = None
        started_at = datetime.now(timezone.utc)
        
        # Act & Assert
        with pytest.raises(RecipeNotFoundException):
            use_case.execute(
                recipe_uid="nonexistent_recipe",
                servings=2,
                level="intermediate",
                user_uid="user_123",
                started_at=started_at
            )

    def test_start_cooking_session_invalid_servings(self, use_case):
        """Test start cooking session with invalid servings"""
        # Arrange
        started_at = datetime.now(timezone.utc)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                recipe_uid="recipe_123",
                servings=0,  # Invalid: zero servings
                level="intermediate",
                user_uid="user_123",
                started_at=started_at
            )
        
        assert str(exc_info.value) == "Servings must be positive"

    def test_start_cooking_session_negative_servings(self, use_case):
        """Test start cooking session with negative servings"""
        # Arrange
        started_at = datetime.now(timezone.utc)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                recipe_uid="recipe_123",
                servings=-1,  # Invalid: negative servings
                level="intermediate",
                user_uid="user_123",
                started_at=started_at
            )
        
        assert str(exc_info.value) == "Servings must be positive"

    def test_start_cooking_session_invalid_level(self, use_case):
        """Test start cooking session with invalid cooking level"""
        # Arrange
        started_at = datetime.now(timezone.utc)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                recipe_uid="recipe_123",
                servings=2,
                level="invalid_level",  # Invalid level
                user_uid="user_123",
                started_at=started_at
            )
        
        assert "Invalid cooking level: invalid_level" in str(exc_info.value)

    def test_start_cooking_session_too_many_active_sessions(self, use_case, 
                                                           mock_cooking_session_repository,
                                                           mock_recipe_repository, valid_recipe):
        """Test start cooking session when user has too many active sessions"""
        # Arrange
        mock_recipe_repository.get_recipe_by_uid.return_value = valid_recipe
        mock_cooking_session_repository.count_active_sessions.return_value = 3  # Max limit reached
        
        started_at = datetime.now(timezone.utc)
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                recipe_uid="recipe_123",
                servings=2,
                level="intermediate",
                user_uid="user_123",
                started_at=started_at
            )
        
        assert "too many active sessions" in str(exc_info.value).lower()

    def test_start_cooking_session_beginner_level(self, use_case, mock_cooking_session_repository,
                                                  mock_recipe_repository, valid_recipe):
        """Test start cooking session with beginner level"""
        # Arrange
        mock_recipe_repository.get_recipe_by_uid.return_value = valid_recipe
        mock_cooking_session_repository.count_active_sessions.return_value = 0
        
        mock_session = Mock()
        mock_session.level = CookingLevel.BEGINNER
        mock_cooking_session_repository.create_session.return_value = mock_session
        
        started_at = datetime.now(timezone.utc)
        
        # Act
        result = use_case.execute(
            recipe_uid="recipe_123",
            servings=2,
            level="beginner",
            user_uid="user_123",
            started_at=started_at
        )
        
        # Assert
        assert result.level == CookingLevel.BEGINNER

    def test_start_cooking_session_advanced_level(self, use_case, mock_cooking_session_repository,
                                                  mock_recipe_repository, valid_recipe):
        """Test start cooking session with advanced level"""
        # Arrange
        mock_recipe_repository.get_recipe_by_uid.return_value = valid_recipe
        mock_cooking_session_repository.count_active_sessions.return_value = 0
        
        mock_session = Mock()
        mock_session.level = CookingLevel.ADVANCED
        mock_cooking_session_repository.create_session.return_value = mock_session
        
        started_at = datetime.now(timezone.utc)
        
        # Act
        result = use_case.execute(
            recipe_uid="recipe_123",
            servings=2,
            level="advanced",
            user_uid="user_123",
            started_at=started_at
        )
        
        # Assert
        assert result.level == CookingLevel.ADVANCED

    def test_start_cooking_session_large_servings(self, use_case, mock_cooking_session_repository,
                                                  mock_recipe_repository, valid_recipe):
        """Test start cooking session with large number of servings"""
        # Arrange
        mock_recipe_repository.get_recipe_by_uid.return_value = valid_recipe
        mock_cooking_session_repository.count_active_sessions.return_value = 0
        
        mock_session = Mock()
        mock_cooking_session_repository.create_session.return_value = mock_session
        
        started_at = datetime.now(timezone.utc)
        
        # Act
        result = use_case.execute(
            recipe_uid="recipe_123",
            servings=10,  # Large number
            level="intermediate",
            user_uid="user_123",
            started_at=started_at
        )
        
        # Assert
        mock_cooking_session_repository.create_session.assert_called_once()

    def test_start_cooking_session_repository_error_propagates(self, use_case, 
                                                              mock_cooking_session_repository,
                                                              mock_recipe_repository, valid_recipe):
        """Test that repository errors are propagated"""
        # Arrange
        mock_recipe_repository.get_recipe_by_uid.return_value = valid_recipe
        mock_cooking_session_repository.count_active_sessions.return_value = 0
        mock_cooking_session_repository.create_session.side_effect = Exception("Database error")
        
        started_at = datetime.now(timezone.utc)
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            use_case.execute(
                recipe_uid="recipe_123",
                servings=2,
                level="intermediate",
                user_uid="user_123",
                started_at=started_at
            )
        
        assert str(exc_info.value) == "Database error"

    def test_start_cooking_session_with_past_datetime(self, use_case, mock_cooking_session_repository,
                                                     mock_recipe_repository, valid_recipe):
        """Test start cooking session with past datetime"""
        # Arrange
        mock_recipe_repository.get_recipe_by_uid.return_value = valid_recipe
        mock_cooking_session_repository.count_active_sessions.return_value = 0
        
        mock_session = Mock()
        mock_cooking_session_repository.create_session.return_value = mock_session
        
        # Past datetime
        started_at = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = use_case.execute(
            recipe_uid="recipe_123",
            servings=2,
            level="intermediate",
            user_uid="user_123",
            started_at=started_at
        )
        
        # Assert
        mock_cooking_session_repository.create_session.assert_called_once()

    def test_session_creation_parameters(self, use_case, mock_cooking_session_repository,
                                        mock_recipe_repository, valid_recipe):
        """Test that session is created with correct parameters"""
        # Arrange
        mock_recipe_repository.get_recipe_by_uid.return_value = valid_recipe
        mock_cooking_session_repository.count_active_sessions.return_value = 0
        
        started_at = datetime.now(timezone.utc)
        
        # Act
        use_case.execute(
            recipe_uid="recipe_123",
            servings=3,
            level="beginner",
            user_uid="user_456",
            started_at=started_at
        )
        
        # Assert
        # Verify that create_session was called with a properly constructed CookingSession
        call_args = mock_cooking_session_repository.create_session.call_args[0][0]
        assert call_args.recipe_uid == "recipe_123"
        assert call_args.servings == 3
        assert call_args.level == CookingLevel.BEGINNER
        assert call_args.user_uid == "user_456"
        assert call_args.started_at == started_at