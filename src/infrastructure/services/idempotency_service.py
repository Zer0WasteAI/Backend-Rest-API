from typing import Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import and_
from src.infrastructure.db.models.idempotency_key_orm import IdempotencyKeyORM
from src.infrastructure.db.base import db
import hashlib
import json

class IdempotencyService:
    def __init__(self, database=None):
        self.db = database or db
        self.default_ttl_hours = 24  # Keys expire after 24 hours

    def check_idempotency(
        self, 
        idempotency_key: str, 
        user_uid: str, 
        endpoint: str, 
        request_body: dict
    ) -> Optional[Tuple[str, str]]:
        """
        Check if request is idempotent and return cached response if exists.
        Returns (status_code, response_body) if found, None if new request.
        """
        request_hash = self._hash_request(request_body)
        
        existing = (
            self.db.session.query(IdempotencyKeyORM)
            .filter(
                and_(
                    IdempotencyKeyORM.idempotency_key == idempotency_key,
                    IdempotencyKeyORM.user_uid == user_uid,
                    IdempotencyKeyORM.endpoint == endpoint,
                    IdempotencyKeyORM.request_hash == request_hash,
                    IdempotencyKeyORM.expires_at > datetime.utcnow()
                )
            )
            .first()
        )
        
        if existing:
            return (existing.response_status, existing.response_body)
        
        return None

    def store_response(
        self,
        idempotency_key: str,
        user_uid: str,
        endpoint: str,
        request_body: dict,
        status_code: str,
        response_body: str,
        ttl_hours: Optional[int] = None
    ):
        """Store response for idempotency checking"""
        request_hash = self._hash_request(request_body)
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours or self.default_ttl_hours)
        
        # Delete any existing key first (in case of retry)
        self.db.session.query(IdempotencyKeyORM).filter(
            and_(
                IdempotencyKeyORM.idempotency_key == idempotency_key,
                IdempotencyKeyORM.user_uid == user_uid,
                IdempotencyKeyORM.endpoint == endpoint
            )
        ).delete()
        
        # Store new response
        idempotency_record = IdempotencyKeyORM(
            idempotency_key=idempotency_key,
            user_uid=user_uid,
            endpoint=endpoint,
            request_hash=request_hash,
            response_status=status_code,
            response_body=response_body,
            expires_at=expires_at
        )
        
        self.db.session.add(idempotency_record)
        self.db.session.commit()

    def cleanup_expired_keys(self) -> int:
        """Clean up expired idempotency keys (job function)"""
        deleted = (
            self.db.session.query(IdempotencyKeyORM)
            .filter(IdempotencyKeyORM.expires_at <= datetime.utcnow())
            .delete()
        )
        self.db.session.commit()
        return deleted

    def _hash_request(self, request_body: dict) -> str:
        """Create SHA256 hash of request body for comparison"""
        # Sort keys for consistent hashing
        normalized = json.dumps(request_body, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(normalized.encode()).hexdigest()