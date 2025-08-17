from datetime import datetime, date
from typing import Optional
from src.domain.models.ingredient_batch import StorageLocation

class LeftoverItem:
    def __init__(
        self,
        leftover_id: str,
        recipe_uid: str,
        user_uid: str,
        title: str,
        portions: int,
        eat_by: date,
        storage_location: StorageLocation,
        created_at: Optional[datetime] = None,
        consumed_at: Optional[datetime] = None,
        session_id: Optional[str] = None
    ):
        self.leftover_id = leftover_id
        self.recipe_uid = recipe_uid
        self.user_uid = user_uid
        self.title = title
        self.portions = portions
        self.eat_by = eat_by
        self.storage_location = storage_location
        self.created_at = created_at or datetime.utcnow()
        self.consumed_at = consumed_at
        self.session_id = session_id
        self._validate()

    def _validate(self):
        if self.portions <= 0:
            raise ValueError("Portions must be positive")
        if not self.title:
            raise ValueError("Title is required")
        if not self.recipe_uid:
            raise ValueError("Recipe UID is required")
        if not self.user_uid:
            raise ValueError("User UID is required")

    def is_consumed(self) -> bool:
        """Check if leftover has been consumed"""
        return self.consumed_at is not None

    def consume(self):
        """Mark leftover as consumed"""
        if self.is_consumed():
            raise ValueError("Leftover already consumed")
        self.consumed_at = datetime.utcnow()

    def is_expired(self, current_date: date) -> bool:
        """Check if leftover is past its eat_by date"""
        return current_date > self.eat_by

    def days_until_expiry(self, current_date: date) -> int:
        """Calculate days until expiry (negative if already expired)"""
        return (self.eat_by - current_date).days

    def generate_planner_suggestion(self) -> dict:
        """Generate a suggestion for meal planning"""
        # Suggest consuming 1 day before expiry, preferably for dinner
        suggested_date = self.eat_by
        if self.days_until_expiry(date.today()) > 1:
            suggested_date = date.today()
        
        return {
            "date": suggested_date.isoformat(),
            "meal_type": "dinner"  # Default to dinner for leftovers
        }

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "leftover_id": self.leftover_id,
            "recipe_uid": self.recipe_uid,
            "user_uid": self.user_uid,
            "title": self.title,
            "portions": self.portions,
            "eat_by": self.eat_by.isoformat(),
            "storage_location": self.storage_location.value,
            "created_at": self.created_at.isoformat(),
            "consumed_at": self.consumed_at.isoformat() if self.consumed_at else None,
            "session_id": self.session_id
        }

    def __repr__(self):
        return f"LeftoverItem(id={self.leftover_id}, title={self.title}, portions={self.portions})"