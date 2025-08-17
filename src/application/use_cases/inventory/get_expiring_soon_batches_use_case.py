from typing import List, Optional
from src.domain.models.ingredient_batch import IngredientBatch
from src.infrastructure.db.ingredient_batch_repository_impl import IngredientBatchRepository

class GetExpiringSoonBatchesUseCase:
    def __init__(self, batch_repository: IngredientBatchRepository):
        self.batch_repository = batch_repository

    def execute(
        self, 
        user_uid: str, 
        within_days: int = 3, 
        storage: Optional[str] = None
    ) -> List[dict]:
        """
        Get batches expiring soon with urgency scores.
        
        Args:
            user_uid: UID of the user
            within_days: Number of days to look ahead
            storage: Optional storage location filter
            
        Returns:
            List of batch dictionaries with urgency scores
        """
        if within_days <= 0:
            raise ValueError("within_days must be positive")
        
        batches = self.batch_repository.find_expiring_soon(
            user_uid=user_uid,
            within_days=within_days,
            storage=storage
        )
        
        # Format response with urgency scores
        result = []
        for batch in batches:
            urgency_score = batch.calculate_urgency_score(batch.expiry_date)
            
            result.append({
                "batch_id": batch.id,
                "ingredient_uid": batch.ingredient_uid,
                "qty": batch.qty,
                "unit": batch.unit,
                "expiry_date": batch.expiry_date.isoformat(),
                "storage_location": batch.storage_location.value,
                "label_type": batch.label_type.value,
                "state": batch.state.value,
                "urgency_score": round(urgency_score, 2),
                "days_to_expiry": (batch.expiry_date - batch.created_at).days
            })
        
        return result