import pytest
import uuid
from datetime import datetime, date, timedelta
from unittest.mock import Mock
from src.domain.models.ingredient_batch import IngredientBatch, BatchState, LabelType, StorageLocation
from src.domain.models.waste_log import WasteLog, WasteReason
from src.application.use_cases.inventory.get_expiring_soon_batches_use_case import GetExpiringSoonBatchesUseCase
from src.application.use_cases.inventory.batch_management_use_cases import (
    ReserveBatchUseCase, FreezeBatchUseCase, TransformBatchUseCase,
    QuarantineBatchUseCase, DiscardBatchUseCase
)
from src.shared.exceptions.custom import InvalidRequestDataException


class TestBatchManagement:
    """Test suite for batch management functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_batch_repo = Mock()
        self.mock_waste_repo = Mock()
        self.user_uid = "test_user_123"
        self.batch_id = str(uuid.uuid4())

    def create_test_batch(self, state=BatchState.AVAILABLE, qty=500.0, days_to_expiry=3):
        """Helper to create test batch"""
        batch = IngredientBatch(
            id=self.batch_id,
            ingredient_uid="ing_chicken",
            qty=qty,
            unit="g",
            storage_location=StorageLocation.FRIDGE,
            label_type=LabelType.USE_BY,
            expiry_date=datetime.utcnow() + timedelta(days=days_to_expiry),
            state=state
        )
        batch.user_uid = self.user_uid
        return batch

    def test_get_expiring_soon_batches_success(self):
        """Test getting batches expiring soon"""
        # Arrange
        batch1 = self.create_test_batch(days_to_expiry=1)  # Very urgent
        batch2 = self.create_test_batch(days_to_expiry=2)  # Moderately urgent
        
        self.mock_batch_repo.find_expiring_soon.return_value = [batch1, batch2]
        
        use_case = GetExpiringSoonBatchesUseCase(self.mock_batch_repo)
        
        # Act
        result = use_case.execute(
            user_uid=self.user_uid,
            within_days=3,
            storage="fridge"
        )
        
        # Assert
        assert len(result) == 2
        assert result[0]["batch_id"] == batch1.id
        assert result[0]["urgency_score"] > result[1]["urgency_score"]  # batch1 more urgent
        self.mock_batch_repo.find_expiring_soon.assert_called_once()

    def test_get_expiring_soon_invalid_days(self):
        """Test expiring soon with invalid days parameter"""
        # Arrange
        use_case = GetExpiringSoonBatchesUseCase(self.mock_batch_repo)
        
        # Act & Assert
        with pytest.raises(ValueError, match="within_days must be positive"):
            use_case.execute(
                user_uid=self.user_uid,
                within_days=0
            )

    def test_reserve_batch_success(self):
        """Test successful batch reservation"""
        # Arrange
        batch = self.create_test_batch()
        reserved_batch = self.create_test_batch(state=BatchState.RESERVED)
        
        self.mock_batch_repo.find_by_id.return_value = batch
        self.mock_batch_repo.save.return_value = reserved_batch
        
        use_case = ReserveBatchUseCase(self.mock_batch_repo)
        
        # Act
        result = use_case.execute(
            batch_id=self.batch_id,
            user_uid=self.user_uid,
            planner_date="2025-08-17",
            meal_type="dinner"
        )
        
        # Assert
        assert result["batch_id"] == self.batch_id
        assert result["state"] == "reserved"
        assert result["reserved_for"]["date"] == "2025-08-17"
        assert result["reserved_for"]["meal_type"] == "dinner"

    def test_reserve_batch_not_found(self):
        """Test reserving non-existent batch"""
        # Arrange
        self.mock_batch_repo.find_by_id.return_value = None
        
        use_case = ReserveBatchUseCase(self.mock_batch_repo)
        
        # Act & Assert
        with pytest.raises(InvalidRequestDataException):
            use_case.execute(
                batch_id="non_existent",
                user_uid=self.user_uid,
                planner_date="2025-08-17",
                meal_type="dinner"
            )

    def test_freeze_batch_success(self):
        """Test successful batch freezing"""
        # Arrange
        batch = self.create_test_batch()
        new_expiry = datetime.utcnow() + timedelta(days=30)
        frozen_batch = self.create_test_batch(state=BatchState.FROZEN)
        frozen_batch.storage_location = StorageLocation.FREEZER
        frozen_batch.expiry_date = new_expiry
        
        self.mock_batch_repo.find_by_id.return_value = batch
        self.mock_batch_repo.save.return_value = frozen_batch
        
        use_case = FreezeBatchUseCase(self.mock_batch_repo)
        
        # Act
        result = use_case.execute(
            batch_id=self.batch_id,
            user_uid=self.user_uid,
            new_best_before=new_expiry.isoformat()
        )
        
        # Assert
        assert result["batch_id"] == self.batch_id
        assert result["state"] == "frozen"
        assert result["storage_location"] == "freezer"

    def test_transform_batch_success(self):
        """Test successful batch transformation"""
        # Arrange
        original_batch = self.create_test_batch()
        transformed_batch = self.create_test_batch()
        transformed_batch.id = "new_batch_456"
        transformed_batch.ingredient_uid = "transformed_sofrito"
        transformed_batch.qty = 250.0
        
        self.mock_batch_repo.find_by_id.return_value = original_batch
        self.mock_batch_repo.save.side_effect = [original_batch, transformed_batch]
        
        use_case = TransformBatchUseCase(self.mock_batch_repo)
        
        # Act
        result = use_case.execute(
            batch_id=self.batch_id,
            user_uid=self.user_uid,
            output_type="sofrito",
            yield_qty=250.0,
            unit="g",
            eat_by="2025-08-20T00:00:00"
        )
        
        # Assert
        assert result["original_batch_id"] == self.batch_id
        assert result["new_batch_id"] == "new_batch_456"
        assert result["output_type"] == "sofrito"
        assert result["yield_qty"] == 250.0

    def test_quarantine_batch_success(self):
        """Test successful batch quarantine"""
        # Arrange
        batch = self.create_test_batch()
        quarantined_batch = self.create_test_batch(state=BatchState.QUARANTINE)
        
        self.mock_batch_repo.find_by_id.return_value = batch
        self.mock_batch_repo.save.return_value = quarantined_batch
        
        use_case = QuarantineBatchUseCase(self.mock_batch_repo)
        
        # Act
        result = use_case.execute(
            batch_id=self.batch_id,
            user_uid=self.user_uid
        )
        
        # Assert
        assert result["batch_id"] == self.batch_id
        assert result["state"] == "quarantine"

    def test_discard_batch_success(self):
        """Test successful batch discard with waste logging"""
        # Arrange
        batch = self.create_test_batch()
        waste_log = WasteLog(
            waste_id="waste_123",
            batch_id=self.batch_id,
            user_uid=self.user_uid,
            reason=WasteReason.EXPIRED,
            estimated_weight=500.0,
            unit="g",
            waste_date=date.today()
        )
        waste_log.co2e_wasted_kg = 0.25
        
        self.mock_batch_repo.find_by_id.return_value = batch
        self.mock_batch_repo.save.return_value = batch
        self.mock_waste_repo.save.return_value = waste_log
        
        use_case = DiscardBatchUseCase(self.mock_batch_repo, self.mock_waste_repo)
        
        # Act
        result = use_case.execute(
            batch_id=self.batch_id,
            user_uid=self.user_uid,
            estimated_weight=500.0,
            unit="g",
            reason="expired"
        )
        
        # Assert
        assert result["waste_id"] == "waste_123"
        assert result["batch_id"] == self.batch_id
        assert result["co2e_wasted_kg"] == 0.25

    def test_discard_batch_invalid_reason(self):
        """Test discarding batch with invalid reason"""
        # Arrange
        batch = self.create_test_batch()
        self.mock_batch_repo.find_by_id.return_value = batch
        
        use_case = DiscardBatchUseCase(self.mock_batch_repo, self.mock_waste_repo)
        
        # Act & Assert
        with pytest.raises(InvalidRequestDataException, match="Invalid waste reason"):
            use_case.execute(
                batch_id=self.batch_id,
                user_uid=self.user_uid,
                estimated_weight=500.0,
                unit="g",
                reason="invalid_reason"
            )


class TestIngredientBatch:
    """Test suite for IngredientBatch domain model"""

    def test_batch_can_be_consumed_available(self):
        """Test batch can be consumed when available"""
        # Arrange
        batch = IngredientBatch(
            id="test_batch",
            ingredient_uid="ing_chicken",
            qty=500.0,
            unit="g",
            storage_location=StorageLocation.FRIDGE,
            label_type=LabelType.USE_BY,
            expiry_date=datetime.utcnow() + timedelta(days=2),
            state=BatchState.AVAILABLE
        )
        
        # Act
        can_consume = batch.can_be_consumed(datetime.utcnow())
        
        # Assert
        assert can_consume is True

    def test_batch_cannot_be_consumed_expired_use_by(self):
        """Test batch cannot be consumed when use_by date has passed"""
        # Arrange
        batch = IngredientBatch(
            id="test_batch",
            ingredient_uid="ing_chicken",
            qty=500.0,
            unit="g",
            storage_location=StorageLocation.FRIDGE,
            label_type=LabelType.USE_BY,
            expiry_date=datetime.utcnow() - timedelta(days=1),  # Expired
            state=BatchState.AVAILABLE
        )
        
        # Act
        can_consume = batch.can_be_consumed(datetime.utcnow())
        
        # Assert
        assert can_consume is False

    def test_batch_can_be_consumed_expired_best_before(self):
        """Test batch can still be consumed when best_before date has passed"""
        # Arrange
        batch = IngredientBatch(
            id="test_batch",
            ingredient_uid="ing_chicken",
            qty=500.0,
            unit="g",
            storage_location=StorageLocation.FRIDGE,
            label_type=LabelType.BEST_BEFORE,
            expiry_date=datetime.utcnow() - timedelta(days=1),  # Past best before
            state=BatchState.AVAILABLE
        )
        
        # Act
        can_consume = batch.can_be_consumed(datetime.utcnow())
        
        # Assert
        assert can_consume is True

    def test_consume_quantity_success(self):
        """Test successful quantity consumption"""
        # Arrange
        batch = IngredientBatch(
            id="test_batch",
            ingredient_uid="ing_chicken",
            qty=500.0,
            unit="g",
            storage_location=StorageLocation.FRIDGE,
            label_type=LabelType.USE_BY,
            expiry_date=datetime.utcnow() + timedelta(days=2),
            state=BatchState.AVAILABLE
        )
        
        # Act
        batch.consume_quantity(200.0)
        
        # Assert
        assert batch.qty == 300.0

    def test_consume_quantity_insufficient(self):
        """Test consuming more quantity than available"""
        # Arrange
        batch = IngredientBatch(
            id="test_batch",
            ingredient_uid="ing_chicken",
            qty=100.0,
            unit="g",
            storage_location=StorageLocation.FRIDGE,
            label_type=LabelType.USE_BY,
            expiry_date=datetime.utcnow() + timedelta(days=2),
            state=BatchState.AVAILABLE
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot consume 200.0"):
            batch.consume_quantity(200.0)

    def test_calculate_urgency_score_use_by(self):
        """Test urgency score calculation for use_by labels"""
        # Arrange
        current_time = datetime.utcnow()
        
        # Batch expiring in 1 day
        batch = IngredientBatch(
            id="test_batch",
            ingredient_uid="ing_chicken",
            qty=500.0,
            unit="g",
            storage_location=StorageLocation.FRIDGE,
            label_type=LabelType.USE_BY,
            expiry_date=current_time + timedelta(days=1),
            state=BatchState.AVAILABLE
        )
        
        # Act
        urgency_score = batch.calculate_urgency_score(current_time)
        
        # Assert
        assert urgency_score == 0.95  # Very urgent for use_by

    def test_calculate_urgency_score_best_before(self):
        """Test urgency score calculation for best_before labels"""
        # Arrange
        current_time = datetime.utcnow()
        
        # Batch expiring in 1 day
        batch = IngredientBatch(
            id="test_batch",
            ingredient_uid="ing_chicken",
            qty=500.0,
            unit="g",
            storage_location=StorageLocation.FRIDGE,
            label_type=LabelType.BEST_BEFORE,
            expiry_date=current_time + timedelta(days=1),
            state=BatchState.AVAILABLE
        )
        
        # Act
        urgency_score = batch.calculate_urgency_score(current_time)
        
        # Assert
        assert urgency_score == 0.80  # Less urgent for best_before


if __name__ == "__main__":
    pytest.main([__file__])