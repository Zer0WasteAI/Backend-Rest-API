from sqlalchemy import Column, String, DateTime, Text, Index
from sqlalchemy.dialects.mysql import CHAR
from src.infrastructure.db.base import db
from datetime import datetime, timezone

class IdempotencyKeyORM(db.Model):
    __tablename__ = "idempotency_keys"

    idempotency_key = Column(String(255), primary_key=True)
    user_uid = Column(String(128), nullable=False)
    endpoint = Column(String(255), nullable=False)
    request_hash = Column(String(64), nullable=False)  # SHA256 hash of request body
    response_status = Column(String(10), nullable=False)
    response_body = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)  # TTL for cleanup

    # Indexes for performance
    __table_args__ = (
        Index('idx_idempotency_user_endpoint', 'user_uid', 'endpoint'),
        Index('idx_idempotency_expires', 'expires_at'),
    )