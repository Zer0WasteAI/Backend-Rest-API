from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Index
from sqlalchemy.dialects.mysql import CHAR
from src.infrastructure.db.base import db
from datetime import datetime, timezone

class CookingSessionORM(db.Model):
    __tablename__ = "cooking_sessions"

    session_id = Column(CHAR(36), primary_key=True)
    recipe_uid = Column(String(255), nullable=False)
    user_uid = Column(String(128), nullable=False)
    servings = Column(Integer, nullable=False)
    level = Column(String(20), nullable=False)  # beginner|intermediate|advanced
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True)
    
    # Store steps as JSON for flexibility
    steps_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Indexes for performance
    __table_args__ = (
        Index('idx_cooking_sessions_user_recipe', 'user_uid', 'recipe_uid'),
        Index('idx_cooking_sessions_started_at', 'started_at'),
        Index('idx_cooking_sessions_user_finished', 'user_uid', 'finished_at'),
    )