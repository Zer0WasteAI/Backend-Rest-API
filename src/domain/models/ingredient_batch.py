from datetime import datetime
from typing import Optional
from enum import Enum

class BatchState(Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    IN_COOKING = "in_cooking"
    LEFTOVER = "leftover"
    FROZEN = "frozen"
    EXPIRING_SOON = "expiring_soon"
    QUARANTINE = "quarantine"
    EXPIRED = "expired"

class LabelType(Enum):
    USE_BY = "use_by"
    BEST_BEFORE = "best_before"

class StorageLocation(Enum):
    PANTRY = "pantry"
    FRIDGE = "fridge"
    FREEZER = "freezer"

class IngredientBatch:
    def __init__(
        self,
        id: str,
        ingredient_uid: str,
        qty: float,
        unit: str,
        storage_location: StorageLocation,
        label_type: LabelType,
        expiry_date: datetime,
        state: BatchState = BatchState.AVAILABLE,
        sealed: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.ingredient_uid = ingredient_uid
        self.qty = qty
        self.unit = unit
        self.storage_location = storage_location
        self.label_type = label_type
        self.expiry_date = expiry_date
        self.state = state
        self.sealed = sealed
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self._validate()

    def _validate(self):
        if self.qty < 0:
            raise ValueError("Quantity must be non-negative")
        if not self.ingredient_uid:
            raise ValueError("Ingredient UID is required")
        if not self.unit:
            raise ValueError("Unit is required")

    def can_be_consumed(self, current_time: datetime) -> bool:
        """Check if batch can be consumed based on label type and expiry date"""
        if self.state not in [BatchState.AVAILABLE, BatchState.RESERVED]:
            return False
        
        if self.label_type == LabelType.USE_BY and current_time > self.expiry_date:
            return False
        
        return True

    def consume_quantity(self, amount: float) -> 'IngredientBatch':
        """Consume a quantity from this batch"""
        if amount > self.qty:
            raise ValueError(f"Cannot consume {amount} {self.unit}, only {self.qty} available")
        
        self.qty -= amount
        self.updated_at = datetime.utcnow()
        
        if self.qty == 0:
            self.state = BatchState.LEFTOVER  # Will be handled by cleanup
        
        return self

    def reserve(self) -> 'IngredientBatch':
        """Mark batch as reserved"""
        if self.state != BatchState.AVAILABLE:
            raise ValueError(f"Cannot reserve batch in state {self.state}")
        
        self.state = BatchState.RESERVED
        self.updated_at = datetime.utcnow()
        return self

    def freeze(self, new_expiry_date: datetime) -> 'IngredientBatch':
        """Freeze the batch and extend expiry date"""
        if self.state not in [BatchState.AVAILABLE, BatchState.RESERVED]:
            raise ValueError(f"Cannot freeze batch in state {self.state}")
        
        self.state = BatchState.FROZEN
        self.storage_location = StorageLocation.FREEZER
        self.expiry_date = new_expiry_date
        self.updated_at = datetime.utcnow()
        return self

    def quarantine(self) -> 'IngredientBatch':
        """Move batch to quarantine"""
        self.state = BatchState.QUARANTINE
        self.updated_at = datetime.utcnow()
        return self

    def calculate_urgency_score(self, current_time: datetime) -> float:
        """Calculate urgency score (0.0 to 1.0) based on time to expiry"""
        if self.state in [BatchState.EXPIRED, BatchState.QUARANTINE]:
            return 1.0
        
        time_to_expiry = (self.expiry_date - current_time).total_seconds()
        
        # If already expired, urgency is maximum
        if time_to_expiry <= 0:
            return 1.0
        
        # Calculate urgency based on days remaining
        days_to_expiry = time_to_expiry / (24 * 3600)
        
        # Different urgency thresholds based on label type
        if self.label_type == LabelType.USE_BY:
            # More urgent for use_by dates
            if days_to_expiry <= 1:
                return 0.95
            elif days_to_expiry <= 2:
                return 0.85
            elif days_to_expiry <= 3:
                return 0.70
            else:
                return max(0.0, 1.0 - (days_to_expiry / 7))
        else:  # BEST_BEFORE
            # Less urgent for best_before dates
            if days_to_expiry <= 1:
                return 0.80
            elif days_to_expiry <= 3:
                return 0.60
            elif days_to_expiry <= 7:
                return 0.40
            else:
                return max(0.0, 1.0 - (days_to_expiry / 14))

    def __repr__(self):
        return f"IngredientBatch(id={self.id}, ingredient={self.ingredient_uid}, qty={self.qty}, state={self.state})"