from datetime import datetime, timezone
from src.infrastructure.db.base import db

class User(db.Model):
    __tablename__ = "users"
    uid = db.Column(db.String(36), primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))


User.auth = db.relationship("AuthUser", backref="user", uselist=False)
User.profile = db.relationship("ProfileUser", backref="user", uselist=False)