from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass

class CookingLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class StepStatus(Enum):
    PENDING = "pending"
    DONE = "done"
    SKIPPED = "skipped"

@dataclass
class StepConsumption:
    ingredient_uid: str
    lot_id: str
    qty: float
    unit: str

@dataclass
class CookingStep:
    step_id: str
    status: StepStatus = StepStatus.PENDING
    timer_ms: Optional[int] = None
    consumptions: List[StepConsumption] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.consumptions is None:
            self.consumptions = []

class CookingSession:
    def __init__(
        self,
        session_id: str,
        recipe_uid: str,
        user_uid: str,
        servings: int,
        level: CookingLevel,
        started_at: datetime,
        finished_at: Optional[datetime] = None,
        steps: Optional[List[CookingStep]] = None,
        notes: Optional[str] = None,
        photo_url: Optional[str] = None
    ):
        self.session_id = session_id
        self.recipe_uid = recipe_uid
        self.user_uid = user_uid
        self.servings = servings
        self.level = level
        self.started_at = started_at
        self.finished_at = finished_at
        self.steps = steps or []
        self.notes = notes
        self.photo_url = photo_url
        self._validate()

    def _validate(self):
        if self.servings <= 0:
            raise ValueError("Servings must be positive")
        if not self.recipe_uid:
            raise ValueError("Recipe UID is required")
        if not self.user_uid:
            raise ValueError("User UID is required")

    def add_step(self, step: CookingStep):
        """Add a cooking step to the session"""
        self.steps.append(step)

    def complete_step(
        self, 
        step_id: str, 
        timer_ms: Optional[int] = None,
        consumptions: Optional[List[StepConsumption]] = None
    ) -> CookingStep:
        """Mark a step as completed with consumptions"""
        step = self.get_step(step_id)
        if not step:
            raise ValueError(f"Step {step_id} not found in session")
        
        step.status = StepStatus.DONE
        step.timer_ms = timer_ms
        step.completed_at = datetime.utcnow()
        
        if consumptions:
            step.consumptions.extend(consumptions)
        
        return step

    def get_step(self, step_id: str) -> Optional[CookingStep]:
        """Get a step by its ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def finish_session(self, notes: Optional[str] = None, photo_url: Optional[str] = None):
        """Finish the cooking session"""
        self.finished_at = datetime.utcnow()
        if notes:
            self.notes = notes
        if photo_url:
            self.photo_url = photo_url

    def is_running(self) -> bool:
        """Check if session is currently running"""
        return self.finished_at is None

    def get_all_consumptions(self) -> List[StepConsumption]:
        """Get all consumptions from all completed steps"""
        all_consumptions = []
        for step in self.steps:
            if step.status == StepStatus.DONE:
                all_consumptions.extend(step.consumptions)
        return all_consumptions

    def get_total_cooking_time(self) -> Optional[int]:
        """Get total cooking time in milliseconds"""
        if not self.finished_at:
            return None
        return int((self.finished_at - self.started_at).total_seconds() * 1000)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "session_id": self.session_id,
            "recipe_uid": self.recipe_uid,
            "user_uid": self.user_uid,
            "servings": self.servings,
            "level": self.level.value,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "steps": [
                {
                    "step_id": step.step_id,
                    "status": step.status.value,
                    "timer_ms": step.timer_ms,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                    "consumptions": [
                        {
                            "ingredient_uid": c.ingredient_uid,
                            "lot_id": c.lot_id,
                            "qty": c.qty,
                            "unit": c.unit
                        } for c in step.consumptions
                    ]
                } for step in self.steps
            ],
            "notes": self.notes,
            "photo_url": self.photo_url
        }

    def __repr__(self):
        return f"CookingSession(id={self.session_id}, recipe={self.recipe_uid}, servings={self.servings})"