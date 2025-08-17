from typing import Optional, Dict, Any
from datetime import datetime, date, timedelta
from src.domain.models.ingredient_batch import IngredientBatch, BatchState
from src.domain.models.waste_log import WasteLog, WasteReason
from src.infrastructure.db.ingredient_batch_repository_impl import IngredientBatchRepository
from src.infrastructure.db.waste_log_repository_impl import WasteLogRepository
from src.shared.exceptions.custom import InvalidRequestDataException
import uuid

class ReserveBatchUseCase:
    def __init__(self, batch_repository: IngredientBatchRepository):
        self.batch_repository = batch_repository

    def execute(self, batch_id: str, user_uid: str, planner_date: str, meal_type: str) -> dict:
        """Reserve a batch for planned consumption"""
        batch = self.batch_repository.find_by_id(batch_id)
        if not batch or batch.user_uid != user_uid:
            raise InvalidRequestDataException(details={"batch_id": "Batch not found or not owned by user"})
        
        try:
            batch.reserve()
            updated_batch = self.batch_repository.save(batch)
            
            return {
                "batch_id": batch_id,
                "state": updated_batch.state.value,
                "reserved_for": {
                    "date": planner_date,
                    "meal_type": meal_type
                }
            }
        except ValueError as e:
            raise InvalidRequestDataException(details={"state": str(e)})

class FreezeBatchUseCase:
    def __init__(self, batch_repository: IngredientBatchRepository):
        self.batch_repository = batch_repository

    def execute(self, batch_id: str, user_uid: str, new_best_before: str) -> dict:
        """Freeze a batch to extend its life"""
        batch = self.batch_repository.find_by_id(batch_id)
        if not batch or batch.user_uid != user_uid:
            raise InvalidRequestDataException(details={"batch_id": "Batch not found or not owned by user"})
        
        try:
            new_expiry = datetime.fromisoformat(new_best_before)
            batch.freeze(new_expiry)
            updated_batch = self.batch_repository.save(batch)
            
            return {
                "batch_id": batch_id,
                "state": updated_batch.state.value,
                "storage_location": updated_batch.storage_location.value,
                "new_expiry_date": updated_batch.expiry_date.isoformat()
            }
        except ValueError as e:
            raise InvalidRequestDataException(details={"error": str(e)})

class TransformBatchUseCase:
    def __init__(self, batch_repository: IngredientBatchRepository):
        self.batch_repository = batch_repository

    def execute(
        self, 
        batch_id: str, 
        user_uid: str, 
        output_type: str, 
        yield_qty: float, 
        unit: str, 
        eat_by: str
    ) -> dict:
        """Transform a batch into a prepared item (like sofrito)"""
        batch = self.batch_repository.find_by_id(batch_id)
        if not batch or batch.user_uid != user_uid:
            raise InvalidRequestDataException(details={"batch_id": "Batch not found or not owned by user"})
        
        try:
            eat_by_date = datetime.fromisoformat(eat_by)
            
            # Create a new batch for the transformed product
            new_batch = IngredientBatch(
                id=str(uuid.uuid4()),
                ingredient_uid=f"transformed_{output_type}",
                qty=yield_qty,
                unit=unit,
                storage_location=batch.storage_location,
                label_type=batch.label_type,
                expiry_date=eat_by_date,
                state=BatchState.AVAILABLE
            )
            new_batch.user_uid = user_uid
            
            # Mark original batch as consumed/used
            batch.state = BatchState.LEFTOVER
            batch.qty = 0
            
            # Save both batches
            self.batch_repository.save(batch)
            saved_new_batch = self.batch_repository.save(new_batch)
            
            return {
                "original_batch_id": batch_id,
                "new_batch_id": saved_new_batch.id,
                "output_type": output_type,
                "yield_qty": yield_qty,
                "unit": unit,
                "eat_by": eat_by
            }
        except ValueError as e:
            raise InvalidRequestDataException(details={"error": str(e)})

class QuarantineBatchUseCase:
    def __init__(self, batch_repository: IngredientBatchRepository):
        self.batch_repository = batch_repository

    def execute(self, batch_id: str, user_uid: str) -> dict:
        """Move batch to quarantine for quality check"""
        batch = self.batch_repository.find_by_id(batch_id)
        if not batch or batch.user_uid != user_uid:
            raise InvalidRequestDataException(details={"batch_id": "Batch not found or not owned by user"})
        
        batch.quarantine()
        updated_batch = self.batch_repository.save(batch)
        
        return {
            "batch_id": batch_id,
            "state": updated_batch.state.value,
            "quarantined_at": updated_batch.updated_at.isoformat()
        }

class DiscardBatchUseCase:
    def __init__(
        self, 
        batch_repository: IngredientBatchRepository,
        waste_log_repository: WasteLogRepository
    ):
        self.batch_repository = batch_repository
        self.waste_log_repository = waste_log_repository

    def execute(
        self, 
        batch_id: str, 
        user_uid: str, 
        estimated_weight: float, 
        unit: str, 
        reason: str
    ) -> dict:
        """Discard a batch and log the waste"""
        batch = self.batch_repository.find_by_id(batch_id)
        if not batch or batch.user_uid != user_uid:
            raise InvalidRequestDataException(details={"batch_id": "Batch not found or not owned by user"})
        
        try:
            waste_reason = WasteReason(reason)
        except ValueError:
            raise InvalidRequestDataException(details={"reason": "Invalid waste reason"})
        
        # Create waste log
        waste_log = WasteLog(
            waste_id=str(uuid.uuid4()),
            batch_id=batch_id,
            user_uid=user_uid,
            reason=waste_reason,
            estimated_weight=estimated_weight,
            unit=unit,
            waste_date=date.today(),
            ingredient_uid=batch.ingredient_uid
        )
        
        # Calculate environmental impact
        co2e_wasted = waste_log.calculate_environmental_impact()
        
        # Mark batch as removed/expired
        batch.state = BatchState.EXPIRED
        batch.qty = 0
        
        # Save both records
        self.batch_repository.save(batch)
        saved_waste_log = self.waste_log_repository.save(waste_log)
        
        return {
            "waste_id": saved_waste_log.waste_id,
            "batch_id": batch_id,
            "co2e_wasted_kg": round(co2e_wasted, 3),
            "discarded_at": datetime.utcnow().isoformat()
        }