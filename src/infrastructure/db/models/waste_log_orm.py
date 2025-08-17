from sqlalchemy import Column, String, Float, Date, DateTime, Enum as SQLEnum, Index
from sqlalchemy.dialects.mysql import CHAR
from src.infrastructure.db.base import db
from src.domain.models.waste_log import WasteReason
from datetime import datetime, timezone

class WasteLogORM(db.Model):
    __tablename__ = "waste_log"

    waste_id = Column(CHAR(36), primary_key=True)
    batch_id = Column(CHAR(36), nullable=False)
    user_uid = Column(String(128), nullable=False)
    ingredient_uid = Column(String(255), nullable=True)  # Denormalized for easier queries
    reason = Column(SQLEnum(WasteReason), nullable=False)
    estimated_weight = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    waste_date = Column(Date, nullable=False)
    co2e_wasted_kg = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Indexes for performance
    __table_args__ = (
        Index('idx_waste_log_user_date', 'user_uid', 'waste_date'),
        Index('idx_waste_log_batch', 'batch_id'),
        Index('idx_waste_log_ingredient', 'ingredient_uid'),
        Index('idx_waste_log_reason', 'reason'),
    )