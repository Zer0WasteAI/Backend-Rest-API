import pytest
import uuid
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch
from src.domain.models.cooking_session import CookingSession, CookingLevel, CookingStep, StepConsumption
from src.domain.models.ingredient_batch import IngredientBatch, BatchState, LabelType, StorageLocation
from src.application.use_cases.cooking_session.start_cooking_session_use_case import StartCookingSessionUseCase
from src.application.use_cases.cooking_session.complete_step_use_case import CompleteStepUseCase
from src.application.use_cases.cooking_session.finish_cooking_session_use_case import FinishCookingSessionUseCase
from src.application.use_cases.recipes.get_mise_en_place_use_case import GetMiseEnPlaceUseCase
from src.shared.exceptions.custom import RecipeNotFoundException


class TestCookingSession:
    """Test suite for cooking session functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_session_repo = Mock()
        self.mock_recipe_repo = Mock()
        self.mock_batch_repo = Mock()
        self.mock_env_use_case = Mock()
        self.mock_mise_service = Mock()
        
        self.user_uid = "test_user_123"
        self.recipe_uid = "recipe_test_001"
        self.session_id = str(uuid.uuid4())

    def test_start_cooking_session_success(self):
        """Test successful cooking session start"""
        # Arrange
        recipe_mock = Mock()
        recipe_mock.uid = self.recipe_uid
        recipe_mock.steps = [Mock(), Mock()]  # 2 steps
        
        self.mock_recipe_repo.find_by_uid.return_value = recipe_mock
        self.mock_session_repo.find_active_sessions.return_value = []
        self.mock_session_repo.save.return_value = Mock(session_id=self.session_id)
        
        use_case = StartCookingSessionUseCase(
            self.mock_session_repo,
            self.mock_recipe_repo
        )
        
        # Act
        result = use_case.execute(
            recipe_uid=self.recipe_uid,
            servings=3,
            level="intermediate",
            user_uid=self.user_uid,
            started_at=datetime.utcnow()
        )
        
        # Assert
        assert result.session_id == self.session_id
        self.mock_recipe_repo.find_by_uid.assert_called_once_with(self.recipe_uid)
        self.mock_session_repo.save.assert_called_once()

    def test_start_cooking_session_recipe_not_found(self):
        """Test cooking session start with non-existent recipe"""
        # Arrange
        self.mock_recipe_repo.find_by_uid.return_value = None
        
        use_case = StartCookingSessionUseCase(
            self.mock_session_repo,
            self.mock_recipe_repo
        )
        
        # Act & Assert
        with pytest.raises(RecipeNotFoundException):
            use_case.execute(
                recipe_uid="non_existent",
                servings=2,
                level="beginner",
                user_uid=self.user_uid,
                started_at=datetime.utcnow()
            )

    def test_start_cooking_session_too_many_active(self):
        """Test cooking session start with too many active sessions"""
        # Arrange
        recipe_mock = Mock()
        self.mock_recipe_repo.find_by_uid.return_value = recipe_mock
        self.mock_session_repo.find_active_sessions.return_value = [Mock(), Mock(), Mock()]  # 3 active
        
        use_case = StartCookingSessionUseCase(
            self.mock_session_repo,
            self.mock_recipe_repo
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Too many active cooking sessions"):
            use_case.execute(
                recipe_uid=self.recipe_uid,
                servings=2,
                level="beginner",
                user_uid=self.user_uid,
                started_at=datetime.utcnow()
            )

    def test_complete_step_success(self):
        """Test successful step completion with ingredient consumption"""
        # Arrange
        session = CookingSession(
            session_id=self.session_id,
            recipe_uid=self.recipe_uid,
            user_uid=self.user_uid,
            servings=2,
            level=CookingLevel.INTERMEDIATE,
            started_at=datetime.utcnow()
        )
        session.add_step(CookingStep(step_id="S1"))
        
        batch = IngredientBatch(
            id="batch_123",
            ingredient_uid="ing_chicken",
            qty=500.0,
            unit="g",
            storage_location=StorageLocation.FRIDGE,
            label_type=LabelType.USE_BY,
            expiry_date=datetime.utcnow() + timedelta(days=2),
            state=BatchState.AVAILABLE
        )
        batch.user_uid = self.user_uid
        
        self.mock_session_repo.find_by_id.return_value = session
        self.mock_batch_repo.lock_batch_for_update.return_value = batch
        self.mock_batch_repo.save.return_value = batch
        self.mock_session_repo.save.return_value = session
        
        use_case = CompleteStepUseCase(
            self.mock_session_repo,
            self.mock_batch_repo
        )
        
        consumptions = [
            {
                "ingredient_uid": "ing_chicken",
                "lot_id": "batch_123",
                "qty": 300,
                "unit": "g"
            }
        ]
        
        # Act
        with patch('src.infrastructure.db.base.db.session'):
            result = use_case.execute(
                session_id=self.session_id,
                step_id="S1",
                user_uid=self.user_uid,
                timer_ms=120000,
                consumptions=consumptions
            )
        
        # Assert
        assert result["ok"] is True
        assert len(result["inventory_updates"]) == 1
        assert result["inventory_updates"][0]["lot_id"] == "batch_123"
        assert result["inventory_updates"][0]["new_qty"] == 200.0  # 500 - 300

    def test_complete_step_insufficient_quantity(self):
        """Test step completion with insufficient ingredient quantity"""
        # Arrange
        session = CookingSession(
            session_id=self.session_id,
            recipe_uid=self.recipe_uid,
            user_uid=self.user_uid,
            servings=2,
            level=CookingLevel.INTERMEDIATE,
            started_at=datetime.utcnow()
        )
        
        batch = IngredientBatch(
            id="batch_123",
            ingredient_uid="ing_chicken",
            qty=100.0,  # Only 100g available
            unit="g",
            storage_location=StorageLocation.FRIDGE,
            label_type=LabelType.USE_BY,
            expiry_date=datetime.utcnow() + timedelta(days=2),
            state=BatchState.AVAILABLE
        )
        batch.user_uid = self.user_uid
        
        self.mock_session_repo.find_by_id.return_value = session
        self.mock_batch_repo.lock_batch_for_update.return_value = batch
        
        use_case = CompleteStepUseCase(
            self.mock_session_repo,
            self.mock_batch_repo
        )
        
        consumptions = [
            {
                "ingredient_uid": "ing_chicken",
                "lot_id": "batch_123",
                "qty": 300,  # Trying to consume 300g
                "unit": "g"
            }
        ]
        
        # Act & Assert
        with patch('src.infrastructure.db.base.db.session'):
            with pytest.raises(ValueError, match="Insufficient quantity"):
                use_case.execute(
                    session_id=self.session_id,
                    step_id="S1",
                    user_uid=self.user_uid,
                    consumptions=consumptions
                )

    def test_finish_cooking_session_success(self):
        """Test successful cooking session finish"""
        # Arrange
        session = CookingSession(
            session_id=self.session_id,
            recipe_uid=self.recipe_uid,
            user_uid=self.user_uid,
            servings=4,  # More than 2, should suggest leftovers
            level=CookingLevel.INTERMEDIATE,
            started_at=datetime.utcnow()
        )
        
        self.mock_session_repo.find_by_id.return_value = session
        self.mock_session_repo.save.return_value = session
        self.mock_env_use_case.execute.return_value = {
            "co2_reduction_kg": 0.5,
            "water_saved_liters": 120,
            "food_waste_reduced_kg": 0.2
        }
        
        use_case = FinishCookingSessionUseCase(
            self.mock_session_repo,
            self.mock_env_use_case
        )
        
        # Act
        result = use_case.execute(
            session_id=self.session_id,
            user_uid=self.user_uid,
            notes="Great recipe!",
            photo_url="https://example.com/photo.jpg"
        )
        
        # Assert
        assert result["ok"] is True
        assert result["session_id"] == self.session_id
        assert "environmental_saving" in result
        assert result["environmental_saving"]["co2e_kg"] == 0.5
        assert "leftover_suggestion" in result
        assert result["leftover_suggestion"]["portions"] == 2  # 4 - 2

    def test_get_mise_en_place_success(self):
        """Test successful mise en place generation"""
        # Arrange
        recipe_mock = Mock()
        recipe_mock.uid = self.recipe_uid
        recipe_mock.ingredients = [
            Mock(name="chicken", quantity=200, type_unit="g"),
            Mock(name="onion", quantity=100, type_unit="g")
        ]
        
        mise_en_place_mock = Mock()
        mise_en_place_mock.to_dict.return_value = {
            "recipe_uid": self.recipe_uid,
            "servings": 3,
            "tools": ["knife", "pan"],
            "prep_tasks": [],
            "measured_ingredients": []
        }
        
        self.mock_recipe_repo.find_by_uid.return_value = recipe_mock
        self.mock_mise_service.generate_mise_en_place.return_value = mise_en_place_mock
        
        use_case = GetMiseEnPlaceUseCase(
            self.mock_recipe_repo,
            self.mock_batch_repo,
            self.mock_mise_service
        )
        
        # Act
        result = use_case.execute(
            recipe_uid=self.recipe_uid,
            servings=3,
            user_uid=self.user_uid
        )
        
        # Assert
        assert result.recipe_uid == self.recipe_uid
        self.mock_recipe_repo.find_by_uid.assert_called_once_with(self.recipe_uid)
        self.mock_mise_service.generate_mise_en_place.assert_called_once()

    def test_get_mise_en_place_invalid_servings(self):
        """Test mise en place with invalid servings"""
        # Arrange
        use_case = GetMiseEnPlaceUseCase(
            self.mock_recipe_repo,
            self.mock_batch_repo,
            self.mock_mise_service
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Servings must be positive"):
            use_case.execute(
                recipe_uid=self.recipe_uid,
                servings=0,
                user_uid=self.user_uid
            )


class TestCookingSessionIntegration:
    """Integration tests for cooking session workflow"""

    def test_complete_cooking_workflow(self):
        """Test complete cooking workflow from start to finish"""
        # This would be a full integration test with real database
        # For now, we'll test the flow with mocked dependencies
        pass


if __name__ == "__main__":
    pytest.main([__file__])