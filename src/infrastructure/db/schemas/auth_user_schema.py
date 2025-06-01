from src.infrastructure.db.base import db

class AuthUser(db.Model):
    __tablename__ = "auth_users"
    uid = db.Column(db.String(128), db.ForeignKey("users.uid"), primary_key=True)
    auth_provider = db.Column(db.String(50), nullable=False, index=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

