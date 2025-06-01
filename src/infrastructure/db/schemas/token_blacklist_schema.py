from datetime import datetime, timezone
from src.infrastructure.db.base import db

class TokenBlacklist(db.Model):
    __tablename__ = "token_blacklist"
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(10), nullable=False)  # 'access' or 'refresh'
    user_uid = db.Column(db.String(128), db.ForeignKey("users.uid"), nullable=False)
    revoked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(100))  # 'logout', 'reuse_detected', 'manual', etc.
    
    def __repr__(self):
        return f"TokenBlacklist(jti={self.jti}, type={self.token_type}, revoked_at={self.revoked_at})"

class RefreshTokenTracking(db.Model):
    __tablename__ = "refresh_token_tracking"
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), unique=True, nullable=False, index=True)
    user_uid = db.Column(db.String(128), db.ForeignKey("users.uid"), nullable=False)
    parent_jti = db.Column(db.String(36), nullable=True)  # JTI del token que generó este
    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # Para detectar actividad sospechosa
    user_agent = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f"RefreshTokenTracking(jti={self.jti}, used={self.used}, created_at={self.created_at})" 