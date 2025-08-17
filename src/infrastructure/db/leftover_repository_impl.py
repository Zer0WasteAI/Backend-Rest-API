from typing import List, Optional
from datetime import date, datetime
from sqlalchemy import and_, desc, asc
from src.domain.models.leftover_item import LeftoverItem
from src.domain.models.ingredient_batch import StorageLocation
from src.infrastructure.db.models.leftover_orm import LeftoverORM
from src.infrastructure.db.base import db

class LeftoverRepository:
    def __init__(self, database=None):
        self.db = database or db

    def save(self, leftover: LeftoverItem) -> LeftoverItem:
        """Save a leftover item"""
        leftover_orm = LeftoverORM(
            leftover_id=leftover.leftover_id,
            recipe_uid=leftover.recipe_uid,
            user_uid=leftover.user_uid,
            title=leftover.title,
            portions=leftover.portions,
            eat_by=leftover.eat_by,
            storage_location=leftover.storage_location,
            session_id=leftover.session_id,
            created_at=leftover.created_at,
            consumed_at=leftover.consumed_at
        )
        
        self.db.session.add(leftover_orm)
        self.db.session.commit()
        
        return self._map_to_domain(leftover_orm)

    def find_by_id(self, leftover_id: str) -> Optional[LeftoverItem]:
        """Find leftover by ID"""
        leftover_orm = self.db.session.get(LeftoverORM, leftover_id)
        return self._map_to_domain(leftover_orm) if leftover_orm else None

    def find_by_user(self, user_uid: str, include_consumed: bool = False) -> List[LeftoverItem]:
        """Find leftovers by user"""
        query = self.db.session.query(LeftoverORM).filter(
            LeftoverORM.user_uid == user_uid
        )
        
        if not include_consumed:
            query = query.filter(LeftoverORM.consumed_at.is_(None))
        
        leftover_orms = query.order_by(asc(LeftoverORM.eat_by)).all()
        return [self._map_to_domain(leftover) for leftover in leftover_orms]

    def find_expiring_soon(self, user_uid: str, days_ahead: int = 2) -> List[LeftoverItem]:
        """Find leftovers expiring soon"""
        cutoff_date = date.today().replace(day=date.today().day + days_ahead)
        
        leftover_orms = (
            self.db.session.query(LeftoverORM)
            .filter(
                and_(
                    LeftoverORM.user_uid == user_uid,
                    LeftoverORM.eat_by <= cutoff_date,
                    LeftoverORM.consumed_at.is_(None)
                )
            )
            .order_by(asc(LeftoverORM.eat_by))
            .all()
        )
        
        return [self._map_to_domain(leftover) for leftover in leftover_orms]

    def mark_consumed(self, leftover_id: str, user_uid: str) -> Optional[LeftoverItem]:
        """Mark leftover as consumed"""
        leftover_orm = (
            self.db.session.query(LeftoverORM)
            .filter(
                and_(
                    LeftoverORM.leftover_id == leftover_id,
                    LeftoverORM.user_uid == user_uid,
                    LeftoverORM.consumed_at.is_(None)
                )
            )
            .first()
        )
        
        if leftover_orm:
            leftover_orm.consumed_at = datetime.utcnow()
            self.db.session.commit()
            return self._map_to_domain(leftover_orm)
        
        return None

    def _map_to_domain(self, leftover_orm: LeftoverORM) -> LeftoverItem:
        """Map ORM to domain model"""
        return LeftoverItem(
            leftover_id=leftover_orm.leftover_id,
            recipe_uid=leftover_orm.recipe_uid,
            user_uid=leftover_orm.user_uid,
            title=leftover_orm.title,
            portions=leftover_orm.portions,
            eat_by=leftover_orm.eat_by,
            storage_location=leftover_orm.storage_location,
            created_at=leftover_orm.created_at,
            consumed_at=leftover_orm.consumed_at,
            session_id=leftover_orm.session_id
        )