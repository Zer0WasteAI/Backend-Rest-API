from sqlalchemy import Column, String, Integer, Date, DateTime, Enum as SQLEnum, Index
from sqlalchemy.dialects.mysql import CHAR
from src.infrastructure.db.base import db
from src.domain.models.ingredient_batch import StorageLocation
from datetime import datetime, timezone

class LeftoverORM(db.Model):
    __tablename__ = "leftovers"

    leftover_id = Column(CHAR(36), primary_key=True)
    recipe_uid = Column(String(255), nullable=False)
    user_uid = Column(String(128), nullable=False)
    title = Column(String(255), nullable=False)
    portions = Column(Integer, nullable=False)
    eat_by = Column(Date, nullable=False)
    storage_location = Column(SQLEnum(StorageLocation), nullable=False)
    
    # Optional reference to cooking session that created this leftover
    session_id = Column(CHAR(36), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    consumed_at = Column(DateTime, nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index('idx_leftovers_user_eat_by', 'user_uid', 'eat_by'),
        Index('idx_leftovers_recipe', 'recipe_uid'),
        Index('idx_leftovers_session', 'session_id'),
        Index('idx_leftovers_storage', 'storage_location'),
    )