from src.infrastructure.db.base import db

class AuthUser(db.Model):
    __tablename__ = "auth_users"
    uid = db.Column(db.String(36), db.ForeignKey("users.uid"), primary_key=True)
    password_hash = db.Column(db.String(255), nullable=False)
    auth_provider = db.Column(db.String(50), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    jwt_token = db.Column(db.Text, nullable=True)

