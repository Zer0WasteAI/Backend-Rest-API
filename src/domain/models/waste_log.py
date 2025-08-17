from datetime import date, datetime
from typing import Optional
from enum import Enum

class WasteReason(Enum):
    EXPIRED = "expired"
    BAD_CONDITION = "bad_condition"
    OTHER = "other"

class WasteLog:
    def __init__(
        self,
        waste_id: str,
        batch_id: str,
        user_uid: str,
        reason: WasteReason,
        estimated_weight: float,
        unit: str,
        waste_date: date,
        ingredient_uid: Optional[str] = None,
        co2e_wasted_kg: Optional[float] = None,
        created_at: Optional[datetime] = None
    ):
        self.waste_id = waste_id
        self.batch_id = batch_id
        self.user_uid = user_uid
        self.reason = reason
        self.estimated_weight = estimated_weight
        self.unit = unit
        self.waste_date = waste_date
        self.ingredient_uid = ingredient_uid
        self.co2e_wasted_kg = co2e_wasted_kg
        self.created_at = created_at or datetime.utcnow()
        self._validate()

    def _validate(self):
        if self.estimated_weight <= 0:
            raise ValueError("Estimated weight must be positive")
        if not self.unit:
            raise ValueError("Unit is required")
        if not self.batch_id:
            raise ValueError("Batch ID is required")

    def calculate_environmental_impact(self, ingredient_co2_factor: float = 0.5) -> float:
        """Calculate CO2 impact of wasted food"""
        # Default factor: 0.5 kg CO2e per kg of food waste
        if self.unit == "g":
            weight_kg = self.estimated_weight / 1000
        elif self.unit == "kg":
            weight_kg = self.estimated_weight
        else:
            # Assume grams for other units
            weight_kg = self.estimated_weight / 1000
        
        co2e_impact = weight_kg * ingredient_co2_factor
        self.co2e_wasted_kg = co2e_impact
        return co2e_impact

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "waste_id": self.waste_id,
            "batch_id": self.batch_id,
            "user_uid": self.user_uid,
            "reason": self.reason.value,
            "estimated_weight": self.estimated_weight,
            "unit": self.unit,
            "waste_date": self.waste_date.isoformat(),
            "ingredient_uid": self.ingredient_uid,
            "co2e_wasted_kg": self.co2e_wasted_kg,
            "created_at": self.created_at.isoformat()
        }

    def __repr__(self):
        return f"WasteLog(id={self.waste_id}, batch={self.batch_id}, weight={self.estimated_weight}{self.unit})"