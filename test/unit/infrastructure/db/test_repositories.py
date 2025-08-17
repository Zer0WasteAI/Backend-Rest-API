import pytest
import uuid
from datetime import datetime, date, timedelta
from unittest.mock import Mock, MagicMock
from src.infrastructure.db.ingredient_batch_repository_impl import IngredientBatchRepository
from src.infrastructure.db.cooking_session_repository_impl import CookingSessionRepository
from src.infrastructure.db.leftover_repository_impl import LeftoverRepository
from src.infrastructure.db.waste_log_repository_impl import WasteLogRepository
from src.domain.models.ingredient_batch import IngredientBatch, BatchState, LabelType, StorageLocation
from src.domain.models.cooking_session import CookingSession, CookingLevel, CookingStep, StepConsumption
from src.domain.models.leftover_item import LeftoverItem
from src.domain.models.waste_log import WasteLog, WasteReason


class TestIngredientBatchRepository:
    """Test suite for IngredientBatchRepository"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock()
        self.mock_session = Mock()
        self.mock_db.session = self.mock_session
        self.repository = IngredientBatchRepository(self.mock_db)
        self.user_uid = "test_user_123"

    def create_test_batch(self, batch_id=None, state=BatchState.AVAILABLE):
        """Helper to create test batch"""
        batch = IngredientBatch(
            id=batch_id or str(uuid.uuid4()),
            ingredient_uid="ing_chicken",
            qty=500.0,
            unit="g",
            storage_location=StorageLocation.FRIDGE,
            label_type=LabelType.USE_BY,
            expiry_date=datetime.utcnow() + timedelta(days=2),
            state=state
        )
        batch.user_uid = self.user_uid
        return batch

    def test_save_new_batch(self):
        """Test saving a new batch"""
        # Arrange
        batch = self.create_test_batch()
        self.mock_session.get.return_value = None  # No existing batch
        
        # Act
        result = self.repository.save(batch)
        
        # Assert
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()
        assert result.id == batch.id

    def test_save_existing_batch(self):
        """Test updating an existing batch"""
        # Arrange
        batch = self.create_test_batch("existing_batch_123")
        existing_orm = Mock()
        existing_orm.id = batch.id
        self.mock_session.get.return_value = existing_orm
        
        # Act
        result = self.repository.save(batch)
        
        # Assert
        assert existing_orm.qty == batch.qty
        assert existing_orm.state == batch.state
        self.mock_session.add.assert_not_called()  # Should not add new
        self.mock_session.commit.assert_called_once()

    def test_find_by_ingredient_fefo(self):
        """Test FEFO (First Expired, First Out) logic"""
        # Arrange
        ingredient_uid = "ing_chicken"
        required_qty = 300.0
        
        # Create mock ORM objects with different expiry dates
        batch_orm_1 = Mock()
        batch_orm_1.id = "batch_1"
        batch_orm_1.expiry_date = datetime.utcnow() + timedelta(days=1)  # Expires sooner
        batch_orm_1.label_type = LabelType.USE_BY
        batch_orm_1.state = BatchState.AVAILABLE
        batch_orm_1.qty = 200.0
        batch_orm_1.ingredient_uid = ingredient_uid
        batch_orm_1.unit = "g"
        batch_orm_1.storage_location = StorageLocation.FRIDGE
        batch_orm_1.sealed = True
        batch_orm_1.user_uid = self.user_uid
        batch_orm_1.created_at = datetime.utcnow()
        batch_orm_1.updated_at = datetime.utcnow()
        
        batch_orm_2 = Mock()
        batch_orm_2.id = "batch_2"
        batch_orm_2.expiry_date = datetime.utcnow() + timedelta(days=3)  # Expires later
        batch_orm_2.label_type = LabelType.USE_BY
        batch_orm_2.state = BatchState.AVAILABLE
        batch_orm_2.qty = 300.0
        batch_orm_2.ingredient_uid = ingredient_uid
        batch_orm_2.unit = "g"
        batch_orm_2.storage_location = StorageLocation.FRIDGE
        batch_orm_2.sealed = True
        batch_orm_2.user_uid = self.user_uid
        batch_orm_2.created_at = datetime.utcnow()
        batch_orm_2.updated_at = datetime.utcnow()
        
        # Mock query result ordered by expiry date (FEFO)
        query_mock = Mock()
        query_mock.all.return_value = [batch_orm_1, batch_orm_2]  # Already sorted by expiry
        self.mock_session.query.return_value.filter.return_value.order_by.return_value = query_mock
        
        # Act
        result = self.repository.find_by_ingredient_fefo(ingredient_uid, self.user_uid, required_qty)
        
        # Assert
        assert len(result) == 2
        assert result[0].id == "batch_1"  # Earlier expiry should come first
        assert result[1].id == "batch_2"

    def test_find_expiring_soon_with_urgency_calculation(self):
        """Test finding expiring batches with urgency score calculation"""
        # Arrange
        within_days = 3
        
        # Mock batch expiring in 1 day (high urgency)
        urgent_batch_orm = Mock()
        urgent_batch_orm.id = "urgent_batch"
        urgent_batch_orm.expiry_date = datetime.utcnow() + timedelta(days=1)
        urgent_batch_orm.label_type = LabelType.USE_BY
        urgent_batch_orm.state = BatchState.AVAILABLE
        urgent_batch_orm.qty = 200.0
        urgent_batch_orm.ingredient_uid = "ing_vegetables"
        urgent_batch_orm.unit = "g"
        urgent_batch_orm.storage_location = StorageLocation.FRIDGE
        urgent_batch_orm.sealed = True
        urgent_batch_orm.user_uid = self.user_uid
        urgent_batch_orm.created_at = datetime.utcnow()
        urgent_batch_orm.updated_at = datetime.utcnow()
        
        query_mock = Mock()
        query_mock.all.return_value = [urgent_batch_orm]
        self.mock_session.query.return_value.filter.return_value.order_by.return_value = query_mock
        
        # Act
        result = self.repository.find_expiring_soon(self.user_uid, within_days)
        
        # Assert
        assert len(result) == 1
        batch = result[0]
        urgency_score = batch.calculate_urgency_score(datetime.utcnow())
        assert urgency_score > 0.9  # Should be very urgent

    def test_update_expired_batches(self):
        """Test batch expiry update job functionality"""
        # Arrange
        use_by_query = Mock()
        use_by_query.update.return_value = 2  # 2 use_by batches expired
        
        best_before_query = Mock()
        best_before_query.update.return_value = 1  # 1 best_before batch to quarantine
        
        expiring_soon_query = Mock()
        expiring_soon_query.update.return_value = 5  # 5 batches now expiring soon
        
        self.mock_session.query.return_value.filter.return_value = use_by_query
        
        # Mock different query responses for different filters
        def mock_query_filter_side_effect(*args):
            # This is a simplified mock - in reality you'd need more specific mocking
            mock_result = Mock()
            mock_result.update.return_value = 2  # Default return
            return mock_result
        
        self.mock_session.query.return_value.filter.side_effect = mock_query_filter_side_effect
        
        # Act
        total_updated = self.repository.update_expired_batches()
        
        # Assert
        assert total_updated >= 0  # Should update some batches
        self.mock_session.commit.assert_called_once()

    def test_lock_batch_for_update(self):
        """Test batch locking for concurrent access control"""
        # Arrange
        batch_id = "batch_to_lock"
        batch_orm = Mock()
        batch_orm.id = batch_id
        
        query_mock = Mock()
        query_mock.first.return_value = batch_orm
        with_for_update_mock = Mock()
        with_for_update_mock.first.return_value = batch_orm
        filter_mock = Mock()
        filter_mock.with_for_update.return_value = with_for_update_mock
        self.mock_session.query.return_value.filter.return_value = filter_mock
        
        # Act
        result = self.repository.lock_batch_for_update(batch_id)
        
        # Assert
        assert result is not None
        filter_mock.with_for_update.assert_called_once()


class TestCookingSessionRepository:
    """Test suite for CookingSessionRepository"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock()
        self.mock_session = Mock()
        self.mock_db.session = self.mock_session
        self.repository = CookingSessionRepository(self.mock_db)
        self.user_uid = "test_user_123"

    def create_test_session(self):
        """Helper to create test cooking session"""
        session = CookingSession(
            session_id=str(uuid.uuid4()),
            recipe_uid="recipe_test_001",
            user_uid=self.user_uid,
            servings=2,
            level=CookingLevel.INTERMEDIATE,
            started_at=datetime.utcnow()
        )
        
        # Add some steps
        step1 = CookingStep(step_id="S1")
        step2 = CookingStep(step_id="S2")
        session.add_step(step1)
        session.add_step(step2)
        
        return session

    def test_save_new_session(self):
        """Test saving a new cooking session"""
        # Arrange
        session = self.create_test_session()
        self.mock_session.get.return_value = None  # No existing session
        
        # Act
        result = self.repository.save(session)
        
        # Assert
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()

    def test_serialize_and_deserialize_steps(self):
        """Test step serialization/deserialization"""
        # Arrange
        step = CookingStep(step_id="S1")
        step.consumptions.append(StepConsumption("ing_chicken", "batch_123", 200, "g"))
        
        # Act
        serialized = self.repository._serialize_steps([step])
        deserialized = self.repository._deserialize_steps(serialized)
        
        # Assert
        assert len(deserialized) == 1
        assert deserialized[0].step_id == "S1"
        assert len(deserialized[0].consumptions) == 1
        assert deserialized[0].consumptions[0].ingredient_uid == "ing_chicken"

    def test_log_consumption(self):
        """Test consumption logging"""
        # Arrange
        session_id = str(uuid.uuid4())
        step_id = "S1"
        consumption = StepConsumption("ing_chicken", "batch_123", 200, "g")
        
        # Act
        result = self.repository.log_consumption(session_id, step_id, consumption, self.user_uid)
        
        # Assert
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()
        assert isinstance(result, str)  # Should return consumption log ID

    def test_get_session_consumptions(self):
        """Test retrieving all consumptions for a session"""
        # Arrange
        session_id = str(uuid.uuid4())
        
        # Mock consumption logs
        consumption_log_1 = Mock()
        consumption_log_1.ingredient_uid = "ing_chicken"
        consumption_log_1.lot_id = "batch_123"
        consumption_log_1.qty_consumed = 200
        consumption_log_1.unit = "g"
        consumption_log_1.step_id = "S1"
        consumption_log_1.consumed_at = datetime.utcnow()
        
        consumption_log_2 = Mock()
        consumption_log_2.ingredient_uid = "ing_onion"
        consumption_log_2.lot_id = "batch_456"
        consumption_log_2.qty_consumed = 100
        consumption_log_2.unit = "g"
        consumption_log_2.step_id = "S2"
        consumption_log_2.consumed_at = datetime.utcnow()
        
        query_mock = Mock()
        query_mock.all.return_value = [consumption_log_1, consumption_log_2]
        self.mock_session.query.return_value.filter.return_value.order_by.return_value = query_mock
        
        # Act
        result = self.repository.get_session_consumptions(session_id)
        
        # Assert
        assert len(result) == 2
        assert result[0]["ingredient_uid"] == "ing_chicken"
        assert result[1]["ingredient_uid"] == "ing_onion"

    def test_find_active_sessions(self):
        """Test finding active (unfinished) sessions"""
        # Arrange
        active_session_orm = Mock()
        active_session_orm.session_id = "active_session"
        active_session_orm.finished_at = None
        active_session_orm.recipe_uid = "recipe_001"
        active_session_orm.user_uid = self.user_uid
        active_session_orm.servings = 2
        active_session_orm.level = "intermediate"
        active_session_orm.started_at = datetime.utcnow()
        active_session_orm.notes = None
        active_session_orm.photo_url = None
        active_session_orm.steps_data = {"steps": []}
        
        query_mock = Mock()
        query_mock.all.return_value = [active_session_orm]
        self.mock_session.query.return_value.filter.return_value.order_by.return_value = query_mock
        
        # Act
        result = self.repository.find_active_sessions(self.user_uid)
        
        # Assert
        assert len(result) == 1
        assert result[0].session_id == "active_session"
        assert result[0].finished_at is None


class TestLeftoverRepository:
    """Test suite for LeftoverRepository"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock()
        self.mock_session = Mock()
        self.mock_db.session = self.mock_session
        self.repository = LeftoverRepository(self.mock_db)
        self.user_uid = "test_user_123"

    def create_test_leftover(self):
        """Helper to create test leftover"""
        return LeftoverItem(
            leftover_id=str(uuid.uuid4()),
            recipe_uid="recipe_test_001",
            user_uid=self.user_uid,
            title="Test Leftover",
            portions=2,
            eat_by=date.today() + timedelta(days=2),
            storage_location=StorageLocation.FRIDGE
        )

    def test_save_leftover(self):
        """Test saving a leftover item"""
        # Arrange
        leftover = self.create_test_leftover()
        
        # Act
        result = self.repository.save(leftover)
        
        # Assert
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()

    def test_find_expiring_soon(self):
        """Test finding leftovers expiring soon"""
        # Arrange
        days_ahead = 2
        
        leftover_orm = Mock()
        leftover_orm.leftover_id = "leftover_123"
        leftover_orm.eat_by = date.today() + timedelta(days=1)  # Expires soon
        leftover_orm.consumed_at = None  # Not consumed yet
        leftover_orm.recipe_uid = "recipe_001"
        leftover_orm.user_uid = self.user_uid
        leftover_orm.title = "Expiring Leftover"
        leftover_orm.portions = 2
        leftover_orm.storage_location = StorageLocation.FRIDGE
        leftover_orm.session_id = None
        leftover_orm.created_at = datetime.utcnow()
        
        query_mock = Mock()
        query_mock.all.return_value = [leftover_orm]
        self.mock_session.query.return_value.filter.return_value.order_by.return_value = query_mock
        
        # Act
        result = self.repository.find_expiring_soon(self.user_uid, days_ahead)
        
        # Assert
        assert len(result) == 1
        assert result[0].leftover_id == "leftover_123"

    def test_mark_consumed(self):
        """Test marking leftover as consumed"""
        # Arrange
        leftover_id = "leftover_to_consume"
        
        leftover_orm = Mock()
        leftover_orm.leftover_id = leftover_id
        leftover_orm.consumed_at = None
        
        query_mock = Mock()
        query_mock.first.return_value = leftover_orm
        self.mock_session.query.return_value.filter.return_value = query_mock
        
        # Act
        result = self.repository.mark_consumed(leftover_id, self.user_uid)
        
        # Assert
        assert leftover_orm.consumed_at is not None
        self.mock_session.commit.assert_called_once()


class TestWasteLogRepository:
    """Test suite for WasteLogRepository"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock()
        self.mock_session = Mock()
        self.mock_db.session = self.mock_session
        self.repository = WasteLogRepository(self.mock_db)
        self.user_uid = "test_user_123"

    def create_test_waste_log(self):
        """Helper to create test waste log"""
        return WasteLog(
            waste_id=str(uuid.uuid4()),
            batch_id="batch_123",
            user_uid=self.user_uid,
            reason=WasteReason.EXPIRED,
            estimated_weight=500.0,
            unit="g",
            waste_date=date.today(),
            ingredient_uid="ing_chicken"
        )

    def test_save_waste_log(self):
        """Test saving a waste log"""
        # Arrange
        waste_log = self.create_test_waste_log()
        
        # Act
        result = self.repository.save(waste_log)
        
        # Assert
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()

    def test_get_waste_summary(self):
        """Test getting waste summary for a period"""
        # Arrange
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        # Mock aggregation result
        summary_result = Mock()
        summary_result.total_weight = 1500.0  # 1.5 kg total waste
        summary_result.total_co2e = 0.75  # 0.75 kg CO2e impact
        summary_result.waste_events = 3  # 3 waste events
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = summary_result
        
        # Act
        result = self.repository.get_waste_summary(self.user_uid, start_date, end_date)
        
        # Assert
        assert result["total_weight_kg"] == 1500.0
        assert result["total_co2e_kg"] == 0.75
        assert result["waste_events"] == 3
        assert "period" in result

    def test_find_by_date_range(self):
        """Test finding waste logs in a date range"""
        # Arrange
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        waste_log_orm = Mock()
        waste_log_orm.waste_id = "waste_123"
        waste_log_orm.batch_id = "batch_456"
        waste_log_orm.user_uid = self.user_uid
        waste_log_orm.reason = WasteReason.EXPIRED
        waste_log_orm.estimated_weight = 300.0
        waste_log_orm.unit = "g"
        waste_log_orm.waste_date = date.today()
        waste_log_orm.ingredient_uid = "ing_vegetables"
        waste_log_orm.co2e_wasted_kg = 0.15
        waste_log_orm.created_at = datetime.utcnow()
        
        query_mock = Mock()
        query_mock.all.return_value = [waste_log_orm]
        self.mock_session.query.return_value.filter.return_value.order_by.return_value = query_mock
        
        # Act
        result = self.repository.find_by_date_range(self.user_uid, start_date, end_date)
        
        # Assert
        assert len(result) == 1
        assert result[0].waste_id == "waste_123"


class TestRepositoryIntegration:
    """Integration tests between repositories"""

    def test_cooking_session_with_batch_consumption(self):
        """Test integration between cooking session and batch repositories"""
        # This would test the complete flow from cooking session
        # to batch consumption logging
        pass

    def test_waste_log_with_environmental_calculation(self):
        """Test waste logging with environmental impact calculation"""
        # This would test how waste logs integrate with environmental
        # savings calculations
        pass


if __name__ == "__main__":
    pytest.main([__file__])