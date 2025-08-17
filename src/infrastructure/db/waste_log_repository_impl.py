from typing import List, Optional
from datetime import date, datetime
from sqlalchemy import and_, desc
from src.domain.models.waste_log import WasteLog, WasteReason
from src.infrastructure.db.models.waste_log_orm import WasteLogORM
from src.infrastructure.db.base import db

class WasteLogRepository:
    def __init__(self, database=None):
        self.db = database or db

    def save(self, waste_log: WasteLog) -> WasteLog:
        """Save a waste log entry"""
        waste_log_orm = WasteLogORM(
            waste_id=waste_log.waste_id,
            batch_id=waste_log.batch_id,
            user_uid=waste_log.user_uid,
            ingredient_uid=waste_log.ingredient_uid,
            reason=waste_log.reason,
            estimated_weight=waste_log.estimated_weight,
            unit=waste_log.unit,
            waste_date=waste_log.waste_date,
            co2e_wasted_kg=waste_log.co2e_wasted_kg
        )
        
        self.db.session.add(waste_log_orm)
        self.db.session.commit()
        
        return self._map_to_domain(waste_log_orm)

    def find_by_user(self, user_uid: str, limit: Optional[int] = None) -> List[WasteLog]:
        """Find waste logs by user"""
        query = (
            self.db.session.query(WasteLogORM)
            .filter(WasteLogORM.user_uid == user_uid)
            .order_by(desc(WasteLogORM.waste_date))
        )
        
        if limit:
            query = query.limit(limit)
        
        waste_logs = query.all()
        return [self._map_to_domain(log) for log in waste_logs]

    def find_by_date_range(
        self, 
        user_uid: str, 
        start_date: date, 
        end_date: date
    ) -> List[WasteLog]:
        """Find waste logs in date range"""
        waste_logs = (
            self.db.session.query(WasteLogORM)
            .filter(
                and_(
                    WasteLogORM.user_uid == user_uid,
                    WasteLogORM.waste_date >= start_date,
                    WasteLogORM.waste_date <= end_date
                )
            )
            .order_by(desc(WasteLogORM.waste_date))
            .all()
        )
        
        return [self._map_to_domain(log) for log in waste_logs]

    def get_waste_summary(self, user_uid: str, start_date: date, end_date: date) -> dict:
        """Get waste summary for a period"""
        from sqlalchemy import func
        
        result = (
            self.db.session.query(
                func.sum(WasteLogORM.estimated_weight).label('total_weight'),
                func.sum(WasteLogORM.co2e_wasted_kg).label('total_co2e'),
                func.count(WasteLogORM.waste_id).label('waste_events')
            )
            .filter(
                and_(
                    WasteLogORM.user_uid == user_uid,
                    WasteLogORM.waste_date >= start_date,
                    WasteLogORM.waste_date <= end_date
                )
            )
            .first()
        )
        
        return {
            "total_weight_kg": result.total_weight or 0,
            "total_co2e_kg": result.total_co2e or 0,
            "waste_events": result.waste_events or 0,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }

    def _map_to_domain(self, waste_log_orm: WasteLogORM) -> WasteLog:
        """Map ORM to domain model"""
        return WasteLog(
            waste_id=waste_log_orm.waste_id,
            batch_id=waste_log_orm.batch_id,
            user_uid=waste_log_orm.user_uid,
            reason=waste_log_orm.reason,
            estimated_weight=waste_log_orm.estimated_weight,
            unit=waste_log_orm.unit,
            waste_date=waste_log_orm.waste_date,
            ingredient_uid=waste_log_orm.ingredient_uid,
            co2e_wasted_kg=waste_log_orm.co2e_wasted_kg,
            created_at=waste_log_orm.created_at
        )