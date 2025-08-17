from sqlalchemy import Column, String, Float, DateTime, Boolean, Enum as SQLEnum, Index
from sqlalchemy.dialects.mysql import CHAR
from src.infrastructure.db.base import db
from src.domain.models.ingredient_batch import BatchState, LabelType, StorageLocation
from datetime import datetime, timezone

class IngredientBatchORM(db.Model):
    __tablename__ = "ingredient_batches"

    id = Column(CHAR(36), primary_key=True)
    ingredient_uid = Column(String(255), nullable=False)
    qty = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    storage_location = Column(SQLEnum(StorageLocation), nullable=False)
    label_type = Column(SQLEnum(LabelType), nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    state = Column(SQLEnum(BatchState), nullable=False, default=BatchState.AVAILABLE)
    sealed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # User relationship for tracking ownership
    user_uid = Column(String(128), nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index('idx_ingredient_batches_ingredient_expiry', 'ingredient_uid', 'expiry_date'),
        Index('idx_ingredient_batches_state_storage', 'state', 'storage_location'),
        Index('idx_ingredient_batches_user_state', 'user_uid', 'state'),
        Index('idx_ingredient_batches_expiry_state', 'expiry_date', 'state'),
    )