from sqlalchemy import Column, String, Float, DateTime, Index
from sqlalchemy.dialects.mysql import CHAR
from src.infrastructure.db.base import db
from datetime import datetime, timezone

class ConsumptionLogORM(db.Model):
    __tablename__ = "consumption_log"

    id = Column(CHAR(36), primary_key=True)
    session_id = Column(CHAR(36), nullable=False)
    step_id = Column(String(50), nullable=False)
    ingredient_uid = Column(String(255), nullable=False)
    lot_id = Column(CHAR(36), nullable=False)
    qty_consumed = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    consumed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # User for tracking
    user_uid = Column(String(128), nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index('idx_consumption_log_session_step', 'session_id', 'step_id'),
        Index('idx_consumption_log_lot', 'lot_id'),
        Index('idx_consumption_log_user_date', 'user_uid', 'consumed_at'),
        Index('idx_consumption_log_ingredient', 'ingredient_uid'),
    )