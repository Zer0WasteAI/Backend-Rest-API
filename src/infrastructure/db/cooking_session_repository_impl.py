from typing import List, Optional
from datetime import datetime
from sqlalchemy import and_, desc
from src.domain.models.cooking_session import CookingSession, CookingLevel, CookingStep, StepStatus, StepConsumption
from src.infrastructure.db.models.cooking_session_orm import CookingSessionORM
from src.infrastructure.db.models.consumption_log_orm import ConsumptionLogORM
from src.infrastructure.db.base import db
import uuid
import json

class CookingSessionRepository:
    def __init__(self, database=None):
        self.db = database or db

    def save(self, session: CookingSession) -> CookingSession:
        """Save or update a cooking session"""
        session_orm = self.db.session.get(CookingSessionORM, session.session_id)
        
        if session_orm:
            # Update existing
            session_orm.servings = session.servings
            session_orm.level = session.level.value
            session_orm.finished_at = session.finished_at
            session_orm.notes = session.notes
            session_orm.photo_url = session.photo_url
            session_orm.steps_data = self._serialize_steps(session.steps)
            session_orm.updated_at = datetime.utcnow()
        else:
            # Create new
            if not session.session_id:
                session.session_id = str(uuid.uuid4())
            
            session_orm = CookingSessionORM(
                session_id=session.session_id,
                recipe_uid=session.recipe_uid,
                user_uid=session.user_uid,
                servings=session.servings,
                level=session.level.value,
                started_at=session.started_at,
                finished_at=session.finished_at,
                notes=session.notes,
                photo_url=session.photo_url,
                steps_data=self._serialize_steps(session.steps)
            )
            self.db.session.add(session_orm)
        
        self.db.session.commit()
        return self._map_to_domain(session_orm)

    def find_by_id(self, session_id: str) -> Optional[CookingSession]:
        """Find session by ID"""
        session_orm = self.db.session.get(CookingSessionORM, session_id)
        return self._map_to_domain(session_orm) if session_orm else None

    def find_by_user(self, user_uid: str, limit: Optional[int] = None) -> List[CookingSession]:
        """Find sessions by user"""
        query = (
            self.db.session.query(CookingSessionORM)
            .filter(CookingSessionORM.user_uid == user_uid)
            .order_by(desc(CookingSessionORM.started_at))
        )
        
        if limit:
            query = query.limit(limit)
        
        session_orms = query.all()
        return [self._map_to_domain(session_orm) for session_orm in session_orms]

    def find_active_sessions(self, user_uid: str) -> List[CookingSession]:
        """Find active (unfinished) sessions for user"""
        session_orms = (
            self.db.session.query(CookingSessionORM)
            .filter(
                and_(
                    CookingSessionORM.user_uid == user_uid,
                    CookingSessionORM.finished_at.is_(None)
                )
            )
            .order_by(desc(CookingSessionORM.started_at))
            .all()
        )
        return [self._map_to_domain(session_orm) for session_orm in session_orms]

    def log_consumption(self, session_id: str, step_id: str, consumption: StepConsumption, user_uid: str) -> str:
        """Log a consumption event"""
        consumption_log = ConsumptionLogORM(
            id=str(uuid.uuid4()),
            session_id=session_id,
            step_id=step_id,
            ingredient_uid=consumption.ingredient_uid,
            lot_id=consumption.lot_id,
            qty_consumed=consumption.qty,
            unit=consumption.unit,
            user_uid=user_uid,
            consumed_at=datetime.utcnow()
        )
        
        self.db.session.add(consumption_log)
        self.db.session.commit()
        return consumption_log.id

    def get_session_consumptions(self, session_id: str) -> List[dict]:
        """Get all consumptions for a session"""
        consumption_logs = (
            self.db.session.query(ConsumptionLogORM)
            .filter(ConsumptionLogORM.session_id == session_id)
            .order_by(ConsumptionLogORM.consumed_at)
            .all()
        )
        
        return [
            {
                "ingredient_uid": log.ingredient_uid,
                "lot_id": log.lot_id,
                "qty": log.qty_consumed,
                "unit": log.unit,
                "step_id": log.step_id,
                "consumed_at": log.consumed_at.isoformat()
            }
            for log in consumption_logs
        ]

    def _serialize_steps(self, steps: List[CookingStep]) -> dict:
        """Serialize steps to JSON"""
        return {
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
                } for step in steps
            ]
        }

    def _deserialize_steps(self, steps_data: dict) -> List[CookingStep]:
        """Deserialize steps from JSON"""
        if not steps_data or "steps" not in steps_data:
            return []
        
        steps = []
        for step_data in steps_data["steps"]:
            consumptions = [
                StepConsumption(
                    ingredient_uid=c["ingredient_uid"],
                    lot_id=c["lot_id"],
                    qty=c["qty"],
                    unit=c["unit"]
                ) for c in step_data.get("consumptions", [])
            ]
            
            step = CookingStep(
                step_id=step_data["step_id"],
                status=StepStatus(step_data["status"]),
                timer_ms=step_data.get("timer_ms"),
                consumptions=consumptions
            )
            
            if step_data.get("completed_at"):
                step.completed_at = datetime.fromisoformat(step_data["completed_at"])
            
            steps.append(step)
        
        return steps

    def _map_to_domain(self, session_orm: CookingSessionORM) -> CookingSession:
        """Map ORM to domain model"""
        steps = self._deserialize_steps(session_orm.steps_data or {})
        
        return CookingSession(
            session_id=session_orm.session_id,
            recipe_uid=session_orm.recipe_uid,
            user_uid=session_orm.user_uid,
            servings=session_orm.servings,
            level=CookingLevel(session_orm.level),
            started_at=session_orm.started_at,
            finished_at=session_orm.finished_at,
            steps=steps,
            notes=session_orm.notes,
            photo_url=session_orm.photo_url
        )